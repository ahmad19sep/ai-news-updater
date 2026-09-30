"""Claude access for every agent: one call shape (JSON in, JSON out), one
cost ledger, one budget.

Models come from config.PIPELINE_MODELS per role so the cheap roles stay
cheap. Every call records tokens and dollars; the orchestrator prints the
total and stops the run if the budget is exceeded.
"""

import json
import os
import time

import config

# USD per million tokens (input, output). Update when Anthropic changes prices.
PRICES = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
    "claude-fable-5-1": (10.0, 50.0),
}
# Models that take no `effort` / adaptive-thinking parameters.
NO_EFFORT_MODELS = {"claude-haiku-4-5"}


def _local_key():
    """ANTHROPIC_API_KEY wins; otherwise anthropic_key.txt next to config.py
    (git-ignored) so a local run needs no shell setup."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "anthropic_key.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


class BudgetExceeded(RuntimeError):
    pass


class LLMError(RuntimeError):
    pass


class LLM:
    """`LLM().json(role, system, user, schema)` -> dict.

    Pass `client=` to inject a fake in tests; otherwise the Anthropic SDK is
    imported lazily so the deterministic agents (enrich, verify checks) run
    without it installed.
    """

    def __init__(self, budget_usd=None, client=None):
        self.budget = (config.PIPELINE_DAILY_BUDGET_USD
                       if budget_usd is None else budget_usd)
        self.spent = 0.0
        self.calls = []          # one entry per call: role, model, tokens, usd, seconds
        self._client = client

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=_local_key() or None)
        return self._client

    def json(self, role, system, user, schema, max_tokens=8000, cache_system=False):
        if self.spent >= self.budget:
            raise BudgetExceeded(f"pipeline budget ${self.budget:.2f} reached")
        model = config.PIPELINE_MODELS[role]
        system_block = [{"type": "text", "text": system}]
        if cache_system:
            # A stable system prompt shared by several calls in one run (voice +
            # rules + examples) is cached; only the per-story user turn varies.
            system_block[0]["cache_control"] = {"type": "ephemeral"}
        kwargs = dict(
            model=model, max_tokens=max_tokens, system=system_block,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        t0 = time.time()
        if model in NO_EFFORT_MODELS:
            resp = self.client.messages.create(**kwargs)
        else:
            kwargs["output_config"]["effort"] = config.PIPELINE_EFFORT.get(role, "medium")
            # Server-side fallback: if a safety classifier declines a benign
            # request, Anthropic re-runs it on a recommended model instead of
            # failing the draft.
            resp = self.client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
        seconds = time.time() - t0

        usage = getattr(resp, "usage", None)
        tokens_in = int(getattr(usage, "input_tokens", 0) or 0)
        tokens_in += int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        tokens_in += int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
        tokens_out = int(getattr(usage, "output_tokens", 0) or 0)
        price_in, price_out = PRICES.get(getattr(resp, "model", model) or model, PRICES[model])
        usd = tokens_in * price_in / 1e6 + tokens_out * price_out / 1e6
        self.spent += usd
        self.calls.append({"role": role, "model": model, "tokens_in": tokens_in,
                           "tokens_out": tokens_out, "usd": round(usd, 5),
                           "seconds": round(seconds, 1)})

        if resp.stop_reason == "refusal":
            raise LLMError(f"{role}: request declined by safety classifier")
        if resp.stop_reason == "max_tokens":
            raise LLMError(f"{role}: output truncated at {max_tokens} tokens")
        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            return json.loads(text)
        except ValueError as e:
            raise LLMError(f"{role}: model returned invalid JSON ({e})")

    def summary(self):
        by_role = {}
        for c in self.calls:
            r = by_role.setdefault(c["role"], {"calls": 0, "tokens_in": 0, "tokens_out": 0, "usd": 0.0})
            r["calls"] += 1
            r["tokens_in"] += c["tokens_in"]
            r["tokens_out"] += c["tokens_out"]
            r["usd"] += c["usd"]
        for r in by_role.values():
            r["usd"] = round(r["usd"], 4)
        return {"usd": round(self.spent, 4), "calls": len(self.calls), "by_role": by_role}
