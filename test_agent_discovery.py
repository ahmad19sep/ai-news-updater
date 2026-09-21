import unittest
import os
import tempfile
from datetime import datetime, timezone
from unittest import mock

import config
import database
import fetcher
from generate_site import _agent_date_label


class AgentDiscoveryNormalizerTest(unittest.TestCase):
    def test_hf_space_keeps_runnable_project_facts(self):
        story = fetcher._hf_space_story({
            "id": "builder/invoice-agent",
            "author": "builder",
            "private": False,
            "sdk": "gradio",
            "likes": 42,
            "createdAt": "2026-09-10T12:00:00.000Z",
            "tags": ["gradio", "agents", "rag"],
            "cardData": {
                "title": "Invoice Agent",
                "short_description": "Reviews invoices with human approval",
            },
        })
        self.assertEqual(story["url"], "https://huggingface.co/spaces/builder/invoice-agent")
        self.assertIn("human approval", story["summary"])
        self.assertEqual(story["upvotes"], 42)
        self.assertIsNotNone(story["published"])

    def test_hf_space_rejects_unrelated_or_private_projects(self):
        self.assertIsNone(fetcher._hf_space_story({
            "id": "builder/weather-map", "private": False, "tags": ["gradio"],
        }))
        self.assertIsNone(fetcher._hf_space_story({
            "id": "builder/private-agent", "private": True,
        }))

    def test_github_repo_keeps_build_evidence(self):
        story = fetcher._github_repo_story({
            "full_name": "builder/support-agent",
            "html_url": "https://github.com/builder/support-agent",
            "description": "Customer support agent with approval gates",
            "created_at": "2026-09-11T10:00:00Z",
            "stargazers_count": 18,
            "language": "Python",
            "topics": ["ai-agents", "customer-support"],
            "private": False,
            "fork": False,
            "archived": False,
        })
        self.assertIn("support-agent", story["title"])
        self.assertIn("Language: Python", story["summary"])
        self.assertEqual(story["upvotes"], 18)

    def test_github_repo_rejects_forks(self):
        self.assertIsNone(fetcher._github_repo_story({
            "full_name": "builder/forked-agent",
            "html_url": "https://github.com/builder/forked-agent",
            "fork": True,
        }))

    def test_repository_creation_is_not_labeled_as_a_release(self):
        self.assertEqual(_agent_date_label("GitHub Agent Builds"), "Repository created")
        self.assertEqual(_agent_date_label("Hugging Face Agent Spaces"), "Space created")
        self.assertEqual(_agent_date_label("DEV Agent Builders"), "Published")

    def test_agent_discoveries_are_isolated_from_news(self):
        old_db = config.DB_FILE
        try:
            with tempfile.TemporaryDirectory() as tmp:
                config.DB_FILE = os.path.join(tmp, "test.db")
                conn = database.connect()
                database.add_agent_discovery(
                    conn, "Invoice agent", "https://example.com/agent",
                    "GitHub Agent Builds", "2026-09-01T00:00:00+00:00",
                    "A public agent repository.", 12,
                )
                conn.commit()
                self.assertTrue(database.agent_discovery_exists(
                    conn, "https://example.com/agent"
                ))
                self.assertFalse(database.url_exists(
                    conn, "https://example.com/agent"
                ))
                self.assertEqual(
                    conn.execute("SELECT COUNT(*) n FROM items").fetchone()["n"], 0
                )
                conn.close()
        finally:
            config.DB_FILE = old_db

    def test_source_health_keeps_last_success_when_a_later_attempt_fails(self):
        health = {}
        fetcher._health_update(health, "Example", True)
        first_success = health["Example"]["last_success"]
        fetcher._health_update(health, "Example", False, "rate limited")
        self.assertEqual(health["Example"]["state"], "failed")
        self.assertEqual(health["Example"]["last_success"], first_success)
        self.assertEqual(health["Example"]["detail"], "rate limited")

    def test_github_query_failure_does_not_block_other_discovery_family(self):
        class GoodResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "incomplete_results": False,
                    "items": [{
                        "full_name": "builder/invoice-agent",
                        "html_url": "https://github.com/builder/invoice-agent",
                        "description": "AI agent for invoice review",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "stargazers_count": 9,
                        "language": "Python",
                        "topics": ["ai-agents"],
                        "private": False,
                        "fork": False,
                        "archived": False,
                    }],
                }

        old_db = config.DB_FILE
        old_queries = config.AGENT_GITHUB_QUERIES
        try:
            with tempfile.TemporaryDirectory() as tmp:
                config.DB_FILE = os.path.join(tmp, "test.db")
                config.AGENT_GITHUB_QUERIES = [
                    {"name": "Broken family", "query": "broken created:>={since}", "limit": 1},
                    {"name": "Working family", "query": "agent created:>={since}", "limit": 1},
                ]
                conn = database.connect()
                stats = {"new": 0, "grouped": 0, "failed_feeds": []}
                with mock.patch.object(fetcher.requests, "get", side_effect=[RuntimeError("rate limit"), GoodResponse()]):
                    results = fetcher.fetch_github_agent_repos(conn, [], stats)
                self.assertFalse(results["Broken family"][0])
                self.assertTrue(results["Working family"][0])
                self.assertIn("Broken family", stats["failed_feeds"])
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM agent_discoveries").fetchone()[0], 1)
                conn.close()
        finally:
            config.DB_FILE = old_db
            config.AGENT_GITHUB_QUERIES = old_queries


if __name__ == "__main__":
    unittest.main()
