"""AI Pulse analyzers: turn raw signals into trends + pain points.

  - momentum.py          : rising/hot/cooling from real history (both modes)
  - raw_synthesizer.py   : deterministic, no-LLM path (PULSE_USE_LLM = False)
  - trend_synthesizer.py : LLM-enriched path     (PULSE_USE_LLM = True)

Both synthesizers return the SAME schema; LLM-only fields are empty in raw mode.
"""
