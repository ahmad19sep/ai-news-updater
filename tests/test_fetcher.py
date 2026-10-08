"""Date parsing regressions; no network or database access."""

import calendar
import unittest
from datetime import datetime, timezone
from unittest import mock

import feedparser

import fetcher


class FeedPublishedTests(unittest.TestCase):
    def test_published_is_utc_on_a_karachi_host(self):
        parsed = feedparser.parse("""<?xml version="1.0"?>
            <rss version="2.0"><channel><title>News</title>
            <item><title>Release</title>
            <pubDate>Thu, 08 Oct 2026 13:30:00 +0500</pubDate>
            </item></channel></rss>""")
        # Simulate the erroneous local-time conversion on any platform,
        # including Windows where time.tzset is unavailable.
        karachi_mktime = lambda value: calendar.timegm(value) - 5 * 3600
        with mock.patch("fetcher.time.mktime", side_effect=karachi_mktime):
            published = fetcher._entry_published(parsed.entries[0])
        self.assertEqual(published, datetime(2026, 10, 8, 8, 30, tzinfo=timezone.utc))

    def test_updated_timestamp_is_used_when_published_is_missing(self):
        parsed = feedparser.parse("""<feed xmlns="http://www.w3.org/2005/Atom">
            <title>News</title><entry><title>Update</title>
            <updated>2026-10-08T06:45:00-04:00</updated>
            </entry></feed>""")
        self.assertEqual(fetcher._entry_published(parsed.entries[0]),
                         datetime(2026, 10, 8, 10, 45, tzinfo=timezone.utc))

    def test_published_takes_precedence_over_updated(self):
        self.assertEqual(fetcher._entry_published({
            "published_parsed": (2026, 10, 8, 8, 30, 0, 3, 281, 0),
            "updated_parsed": (2026, 10, 8, 10, 45, 0, 3, 281, 0),
        }), datetime(2026, 10, 8, 8, 30, tzinfo=timezone.utc))

    def test_undated_entries_remain_undated(self):
        self.assertIsNone(fetcher._entry_published({}))


if __name__ == "__main__":
    unittest.main()
