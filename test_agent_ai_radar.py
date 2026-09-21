import unittest

import agent_ai_radar


class AgentAIRadarClassifierTest(unittest.TestCase):
    def topic(self, title, **kw):
        meta = agent_ai_radar.classify(title, **kw)
        self.assertTrue(meta.get("relevant"), title)
        return meta

    def test_model_release(self):
        meta = self.topic("OpenAI releases a new reasoning model with a larger context window")
        self.assertEqual(meta["primary"], "models")
        self.assertIn("models", meta["topics"])

    def test_agent_runtime_tool_calling(self):
        meta = self.topic("New agent runtime adds tool calling, checkpoints, and human approval")
        self.assertEqual(meta["primary"], "agent_loops")
        self.assertIn("tool calling", meta["secondary"])
        self.assertIn("durable execution", meta["secondary"])

    def test_rag_context(self):
        meta = self.topic("A RAG system improves citations with retrieval, reranking, and grounding")
        self.assertEqual(meta["primary"], "rag_context")

    def test_real_world_agent(self):
        meta = self.topic("Customer support agent case study reaches production deployment")
        self.assertEqual(meta["primary"], "real_world_agents")

    def test_eval_safety(self):
        meta = self.topic("Benchmark tests agent reliability against prompt injection and sandbox escapes")
        self.assertEqual(meta["primary"], "eval_safety")

    def test_agi_watch(self):
        meta = self.topic("Researchers measure long-horizon task performance and generalization")
        self.assertEqual(meta["primary"], "agi_watch")

    def test_unrelated_ai_adjacent_item_is_not_included(self):
        meta = agent_ai_radar.classify("A celebrity discusses AI in a short interview")
        self.assertFalse(meta.get("relevant"))

    def test_source_type_hints_are_conservative(self):
        self.assertEqual(
            self.topic("Agents SDK release", source="OpenAI Blog")["source_type"],
            "official",
        )
        self.assertEqual(
            self.topic("Anthropic announces a new model release", source="Anthropic News")["source_type"],
            "news",
        )


if __name__ == "__main__":
    unittest.main()
