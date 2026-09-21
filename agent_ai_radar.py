"""
Deterministic discovery metadata for the Agent & AI Radar Studio tab.

This module deliberately works from collected metadata only. It does not fetch
source pages, infer release dates, or change the story's existing category.
"""

import hashlib
import re


PRIMARY_TOPICS = [
    ("models", "Models"),
    ("agent_loops", "Agent Loops"),
    ("rag_context", "RAG & Context"),
    ("real_world_agents", "Real-world Agents"),
    ("eval_safety", "Eval & Safety"),
    ("agi_watch", "AGI Watch"),
]


PRACTICAL_TRACKS = [
    ("built", "Built & shipped"),
    ("operations", "Running in business"),
    ("selling", "Selling agents"),
]


TOPIC_RULES = {
    "models": [
        "model release", "released model", "new model", "reasoning model",
        "frontier model", "foundation model", "model card", "system card",
        "multimodal", "context window", "coding model", "language model",
        "embedding model", "reranker", "open weights", "open-weight",
        "llama", "claude", "gpt", "gemini", "mistral", "deepseek", "grok",
        "sora", "veo", "imagen", "qwen",
    ],
    "agent_loops": [
        "agent", "agents", "agentic", "agent sdk", "agent framework",
        "tool calling", "function calling", "tools", "orchestration",
        "computer use", "browser use", "runtime", "workflow", "mcp",
        "model context protocol", "a2a", "durable execution", "checkpoint",
        "task state", "autonomous", "approval", "human in the loop",
        "multi-agent", "multi agent",
    ],
    "rag_context": [
        "rag", "retrieval", "retrieve", "vector", "embedding",
        "reranking", "reranker", "knowledge base", "grounding",
        "citation", "citations", "context engineering", "long context",
        "external knowledge", "search grounding",
    ],
    "real_world_agents": [
        "case study", "customer", "deployed", "production", "rolls out",
        "used by", "customer support", "support agent", "research agent",
        "coding agent", "software engineering agent", "operations",
        "workflow automation", "enterprise agent", "sales agent",
        "audit agent", "science agent", "robotics", "robot", "embodied",
        "ai automation agency", "automation agency",
    ],
    "eval_safety": [
        "benchmark", "benchmarks", "eval", "evaluation", "reliability",
        "guardrail", "guardrails", "authorization", "permission",
        "permissions", "prompt injection", "jailbreak", "security",
        "policy", "sandbox", "red team", "alignment", "safety",
        "verification", "observability", "cost budget", "timeout",
    ],
    "agi_watch": [
        "agi", "general intelligence", "task horizon", "long-horizon",
        "long horizon", "generalization", "continual learning",
        "self-improvement", "self improvement", "autonomous research",
        "embodied agent", "embodied ai", "robotics", "world model",
    ],
}


SECONDARY_RULES = {
    "MCP": ["mcp", "model context protocol"],
    "A2A": ["a2a", "agent-to-agent", "agent to agent"],
    "computer use": ["computer use", "browser use", "operate a computer"],
    "coding agents": ["coding agent", "software engineering agent", "code agent", "developer agent"],
    "multi-agent": ["multi-agent", "multi agent", "swarm"],
    "agent frameworks": ["agent framework", "agents sdk", "langchain", "llamaindex", "crewai", "autogen"],
    "durable execution": ["durable execution", "checkpoint", "checkpoints", "resume", "stateful workflow"],
    "memory": ["memory", "long-term memory", "state memory"],
    "tool calling": ["tool calling", "function calling", "tools"],
    "robotics / embodied AI": ["robot", "robotics", "embodied"],
    "enterprise agents": ["enterprise agent", "customer support", "operations", "workflow automation"],
    "science agents": ["science agent", "research agent", "lab automation"],
}


PRACTICAL_RULES = {
    "built": [
        "i built", "we built", "i made", "we made", "built an agent",
        "building an agent", "building ai agents", "show hn", "open source", "open-source",
        "github", "repository", "repo", "demo", "prototype", "tutorial",
        "how i built", "how we built", "launch", "launched", "shipped",
        "workflow", "automation", "agent framework", "mcp server",
        "hugging face space", "gradio", "docker",
    ],
    "operations": [
        "in production", "production deployment", "deployed", "case study",
        "customer story", "used by teams", "used by companies", "used by employees",
        "used by customers", "customer support", "sales agent",
        "support agent", "support workflow", "support workflows",
        "client workflow", "client workflows", "business workflow", "business workflows",
        "operations", "back office", "workflow automation",
        "enterprise agent", "employees", "hours saved", "cost savings",
        "human in the loop", "human approval", "approval workflow",
    ],
    "selling": [
        "selling", "sell agents", "agent business", "automation agency",
        "ai agency", "consulting", "client", "clients", "customer",
        "revenue", "pricing", "subscription", "marketplace", "paid plan",
        "business model", "go to market", "go-to-market", "startup",
        "roi", "contract", "freelance", "service business",
    ],
}

STRONG_BUILD_PHRASES = {
    "i built", "we built", "i made", "we made", "built an agent",
    "building an agent", "building ai agents", "show hn", "how i built",
    "how we built", "hugging face space",
}


OFFICIAL_SOURCES = {
    "OpenAI Blog",
    "Google DeepMind",
    "Hugging Face Blog",
    "Google AI Blog",
    "NVIDIA AI Blog",
    "Google Research",
    "AWS ML Blog",
    "Apple ML Research",
    "Together AI",
}

PAPER_SOURCES = {"arXiv AI", "arXiv NLP (cs.CL)", "arXiv ML (cs.LG)", "HF Trending Papers"}
COMMUNITY_SOURCES = {"Hacker News AI", "Hacker News new"}
BUILDER_SOURCES = {
    "Show HN Agent Builds",
    "DEV Agent Builders",
    "GitHub Agent Builds",
    "Hugging Face Agent Spaces",
}
DIRECT_BUILD_SOURCES = {
    "Show HN Agent Builds",
    "GitHub Agent Builds",
    "Hugging Face Agent Spaces",
}
BUSINESS_SOURCES = {
    "Agent Business & Sales",
    "AI Automation Agencies",
}
OPERATIONS_SOURCES = {"Agent Customer Workflows"}


def story_key(url, title=""):
    raw = (url or title or "").strip().lower().encode("utf-8", "ignore")
    return hashlib.sha1(raw).hexdigest()[:16]


def _words(text):
    return re.sub(r"\s+", " ", (text or "").lower())


def _has(text, phrase):
    phrase = phrase.lower()
    if re.search(r"^[a-z0-9_+-]+$", phrase):
        return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None
    return re.search(
        r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])",
        text,
    ) is not None


def _score_topic(text, phrases):
    score = 0
    for phrase in phrases:
        if _has(text, phrase):
            score += 2 if " " in phrase else 1
    return score


def _source_type(source, text):
    if source in OFFICIAL_SOURCES:
        return "official"
    if source in PAPER_SOURCES or " arxiv " in (" " + text + " "):
        return "paper"
    if "case study" in text or "customer story" in text:
        return "case_study"
    if source in COMMUNITY_SOURCES or source in BUILDER_SOURCES or "hacker news" in source.lower():
        return "community"
    if source:
        return "news"
    return "unknown"


def classify(title, source="", url="", summary="", pillar=None):
    text = _words(" ".join([title or "", url or "", summary or ""]))
    scores = {topic: _score_topic(text, phrases) for topic, phrases in TOPIC_RULES.items()}

    # Coding-agent and research-paper stories often use domain words without
    # saying "agent" in the headline; the source category can provide a gentle
    # supporting signal without making the classifier brand-specific.
    if pillar == 2 and any(_has(text, p) for p in ["agent", "coding", "developer", "tool calling"]):
        scores["agent_loops"] += 1
    if pillar == 9 and any(scores.values()):
        scores["eval_safety"] += 1

    ordered = [topic for topic, _label in PRIMARY_TOPICS if scores.get(topic, 0) > 0]
    if not ordered:
        return {"relevant": False}

    ordered.sort(key=lambda t: (-scores[t], [x[0] for x in PRIMARY_TOPICS].index(t)))
    secondary = []
    for label, phrases in SECONDARY_RULES.items():
        if any(_has(text, phrase) for phrase in phrases):
            secondary.append(label)

    source_type = _source_type(source or "", text)
    practical_scores = {
        track: _score_topic(text, phrases)
        for track, phrases in PRACTICAL_RULES.items()
    }
    if source in DIRECT_BUILD_SOURCES:
        practical_scores["built"] += 5
    if source in BUSINESS_SOURCES:
        practical_scores["selling"] += 5
    if source in OPERATIONS_SOURCES:
        practical_scores["operations"] += 5
    if source_type == "case_study":
        practical_scores["operations"] += 2

    practical = []
    for track, _label in PRACTICAL_TRACKS:
        score = practical_scores.get(track, 0)
        if source_type == "paper":
            qualifies = score >= 4
        elif track == "built":
            qualifies = score >= 3 or any(_has(text, p) for p in STRONG_BUILD_PHRASES)
        else:
            qualifies = score >= 2
        if qualifies:
            practical.append(track)
    practical.sort(key=lambda t: (
        -practical_scores[t],
        [x[0] for x in PRACTICAL_TRACKS].index(t),
    ))

    return {
        "relevant": True,
        "primary": ordered[0],
        "topics": ordered,
        "secondary": secondary[:5],
        "source_type": source_type,
        "practical": practical,
    }
