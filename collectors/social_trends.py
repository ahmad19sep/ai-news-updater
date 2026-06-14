"""Instagram / Facebook / LinkedIn — honest stub (intentionally returns []).

There is NO reliable free, ToS-compliant API for platform-wide trends on any
of these three:
  - Meta Graph API only exposes YOUR OWN assets and needs a business account +
    app review; it has no public trend feed.
  - LinkedIn's API is partner-gated and exposes no public trend feed.
  - Scraping any of them violates their Terms of Service.

So we DO NOT fake measured data here. Instead, the synthesizer INFERS likely
trends on these platforms from cross-platform signals (visual / short-form ->
Reels on IG/FB; work / career / productivity -> LinkedIn) and the UI labels
those items 'inferred', never 'measured'.

OPTIONAL future path (enable ONLY if it is ToS-compliant): a paid
social-listening API or an Apify-type actor. Implement it below and return real
RawSignal dicts; everything downstream already handles extra platforms.
"""


def collect():
    return []  # see module docstring — inferred downstream, never faked here
