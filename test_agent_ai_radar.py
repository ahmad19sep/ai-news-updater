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

    def test_named_model_update_survives_the_ai_context_gate(self):
        meta = self.topic("GPT-5 system card adds new benchmark results")
        self.assertEqual(meta["primary"], "models")
        self.assertIn("models_frameworks", meta["discovery_tabs"])

    def test_agent_runtime_tool_calling(self):
        meta = self.topic("New agent runtime adds tool calling, checkpoints, and human approval")
        self.assertEqual(meta["primary"], "agent_loops")
        self.assertIn("tool calling", meta["secondary"])
        self.assertIn("durable execution", meta["secondary"])

    def test_plural_agents_pass_the_context_gate(self):
        meta = self.topic("Open-source agents coordinate customer-support tasks")
        self.assertEqual(meta["primary"], "agent_loops")

    def test_rag_context(self):
        meta = self.topic("A RAG system improves citations with retrieval, reranking, and grounding")
        self.assertEqual(meta["primary"], "rag_context")

    def test_real_world_agent(self):
        meta = self.topic("Customer support agent case study reaches production deployment")
        self.assertEqual(meta["primary"], "real_world_agents")
        self.assertIn("operations", meta["practical"])

    def test_builder_source_gets_practical_track(self):
        meta = self.topic(
            "Invoice review assistant",
            source="GitHub Agent Builds",
            summary="Open-source repository for a bounded AI agent.",
        )
        self.assertIn("built", meta["practical"])
        self.assertEqual(meta["source_type"], "community")
        self.assertIn("agent_builds", meta["discovery_tabs"])
        self.assertTrue(meta["match_reasons"])

    def test_explicit_ai_mvp_does_not_need_agent_word(self):
        meta = self.topic(
            "I launched an AI MVP that turns support calls into reviewed tickets"
        )
        self.assertIn("mvps", meta["discovery_tabs"])
        self.assertIn("workflows", meta["discovery_tabs"])

    def test_agent_skill_is_not_generic_career_skills(self):
        skill = self.topic(
            "Open-source Agent Skill packages a SKILL.md for invoice review"
        )
        self.assertIn("skills", skill["discovery_tabs"])
        self.assertFalse(
            agent_ai_radar.classify(
                "Five communication skills every product manager should learn"
            ).get("relevant")
        )

    def test_mcp_is_an_integration_not_automatically_multi_agent(self):
        meta = self.topic(
            "New MCP server connects an AI assistant to a customer database"
        )
        self.assertIn("mcp", meta["discovery_tabs"])
        self.assertIn("MCP", meta["secondary"])
        self.assertNotIn("multi-agent", meta["secondary"])

    def test_content_creation_agent_qualifies_as_build(self):
        meta = self.topic(
            "How I built a content creation agent with human review before publishing"
        )
        self.assertIn("agent_builds", meta["discovery_tabs"])
        self.assertIn("built", meta["practical"])

    def test_broad_mvp_and_workflow_terms_do_not_qualify_without_ai(self):
        for title in (
            "The league announces this season's MVP",
            "A simple workflow for planning a family holiday",
            "Startup founders debate their minimum viable product",
        ):
            with self.subTest(title=title):
                self.assertFalse(agent_ai_radar.classify(title).get("relevant"))

    def test_multimodal_and_multi_model_stay_distinct(self):
        multimodal = self.topic("A multimodal AI model handles text and images")
        multi_model = self.topic("An AI router uses multi-model routing for cost control")
        self.assertIn("multimodal", multimodal["secondary"])
        self.assertNotIn("multi-model", multimodal["secondary"])
        self.assertIn("multi-model", multi_model["secondary"])

    def test_agent_business_signal(self):
        meta = self.topic(
            "Consultancy explains pricing an AI agent for client support workflows"
        )
        self.assertIn("selling", meta["practical"])
        self.assertIn("operations", meta["practical"])

    def test_caused_by_does_not_match_used_by(self):
        meta = self.topic("An AI agent breach was caused by one configuration issue")
        self.assertNotIn("operations", meta["practical"])

    def test_business_and_operations_sources_stay_separate(self):
        selling = self.topic(
            "How an AI automation agency prices client work",
            source="AI Automation Agencies",
        )
        operating = self.topic(
            "A support AI agent runs a claims workflow",
            source="Agent Customer Workflows",
        )
        self.assertIn("selling", selling["practical"])
        self.assertIn("operations", operating["practical"])

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
