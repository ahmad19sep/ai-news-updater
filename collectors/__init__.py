"""AI Pulse collectors — free signal sources, server-side only.

Each collector exposes a `collect()` that returns a list of normalized
RawSignal dicts and MUST fail gracefully (return [] on any error) so one bad
source never takes down the pipeline.

RawSignal shape:
    {platform, type, text, url, metric, captured_at, ...extras}
"""
