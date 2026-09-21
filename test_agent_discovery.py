import unittest
import os
import tempfile

import config
import database
import fetcher


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


if __name__ == "__main__":
    unittest.main()
