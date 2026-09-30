"""Content pipeline agents.

Each module is one small agent with one job. They share two things only:
`llm.LLM` (Claude calls + cost ledger) and `store.Store` (shared state the
Studio reads). `run_pipeline.py` runs them in order.
"""
