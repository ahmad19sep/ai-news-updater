"""Loads the plain-text files in content/ that shape every draft:
voice.md (who you are, audience, priorities), hooks.json, examples.md,
linkedin_rules.md. Edit those files; never this one."""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "content")


def _read(name, default=""):
    try:
        with open(os.path.join(DIR, name), encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return default


def _sections(md):
    """'## Heading' -> body, lower-cased keys."""
    out, key, buf = {}, "intro", []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            out[key] = "\n".join(buf).strip()
            key, buf = m.group(1).strip().lower(), []
        else:
            buf.append(line)
    out[key] = "\n".join(buf).strip()
    return out


def voice():
    s = _sections(_read("voice.md"))
    return {
        "who": s.get("who i am", ""),
        "audience": s.get("audience", "Working professionals who want to use AI well."),
        "tone": s.get("tone", ""),
        "priorities": s.get("topic priorities", ""),
        "never": s.get("never", ""),
        "raw": _read("voice.md"),
    }


def rules():
    return _read("linkedin_rules.md")


def examples():
    return _read("examples.md")


def hooks():
    try:
        data = json.loads(_read("hooks.json", "[]"))
    except ValueError:
        data = []
    return data if isinstance(data, list) else []


def hooks_text(limit=30):
    lines = []
    for h in hooks()[:limit]:
        if isinstance(h, dict):
            lines.append(f"- ({h.get('type', 'hook')}) {h.get('text', '')}")
        else:
            lines.append(f"- {h}")
    return "\n".join(lines)
