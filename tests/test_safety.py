import json
import unittest
from pathlib import Path
from agents import ProductAgent, SafetyAgent, RoutineAgent, ResearchAgent
from orchestrator import OrchestratorAgent, REFERRAL_CONCERNS
from evaluation import evaluate_retrieval, evaluate_system

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

class SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = ProductAgent()
        cls.safety = SafetyAgent()
        cls.profiles = json.loads((DATA_DIR / "planted_conflicts.json").read_text(encoding="utf-8"))

    def test_planted_conflicts_are_rejected_and_targeted_product_identified(self):
        for profile in self.profiles:
            with self.subTest(profile=profile["profile_id"]):
                plan = [self.products.get_product(pid) for pid in profile["initial_candidate_ids"]]
                result = self.safety.validate(plan, {"user_input": profile})
                self.assertFalse(result["approved"])
                self.assertIn(profile["expected_rejected_product"], result["rejected_product_ids"])
                self.assertTrue(result["reasons"])

    def test_replacement_plan_can_pass_safety(self):
        for profile in self.profiles:
            with self.subTest(profile=profile["profile_id"]):
                ids = [x for x in profile["initial_candidate_ids"] if x != profile["expected_rejected_product"]]
                ids.append(profile["replacement_product"])
                plan = [self.products.get_product(pid) for pid in ids]
                result = self.safety.validate(plan, {"user_input": profile})
                self.assertTrue(result["approved"], msg="; ".join(result["reasons"]))

    def test_referral_gate_blocks_routine_for_severe_concerns(self):
        result = OrchestratorAgent().run({"skin_type":"oily","concern":"painful acne","budget_inr":1500,
                                          "allergies":[],"current_products":[]})
        self.assertTrue(result["referral_required"])
        self.assertIsNone(result["final_routine"])
        self.assertEqual(result["agent_status"]["Routine Agent"], "blocked by referral gate")

    def test_retrieval_evaluation_runs(self):
        result = evaluate_retrieval(top_k=3)
        self.assertEqual(result["total"], 10)
        self.assertGreaterEqual(result["accuracy"], 0.0)
        self.assertLessEqual(result["accuracy"], 1.0)

    def test_vitamin_c_with_strong_acid_rule_exists(self):
        for acid in ("glycolic acid", "salicylic acid"):
            self.assertIsNotNone(self.safety._conflict_rule("vitamin c", acid))

    def test_routine_has_explanation_and_valid_citation_per_step(self):
        profile = {"skin_type":"oily","concern":"acne","budget_inr":1500,"allergies":[],"current_products":[]}
        state = OrchestratorAgent().run(profile)
        self.assertIsNotNone(state["final_routine"], msg="; ".join(state.get("rejection_reasons", [])))
        for period in ("AM", "PM"):
            for step in state["final_routine"][period]:
                self.assertTrue(step["explanation"])
                self.assertTrue(step["source_ids"])
                self.assertIn(step["source_ids"][0], self.safety.valid_source_ids)


    def test_product_level_audit_and_planner_decisions_exist(self):
        result = OrchestratorAgent().run({"skin_type":"oily","concern":"acne","budget_inr":1800,
                                          "allergies":[],"current_products":[],"current_ingredient_names":[]})
        self.assertIsNotNone(result["final_routine"])
        self.assertTrue(result["safety_result"]["product_audit"])
        self.assertTrue(result["planner_decisions"])
        self.assertTrue(result["routine_comparison"])

    def test_end_to_end_scenario_suite(self):
        result = evaluate_system()
        self.assertEqual(result["total"], 6)
        self.assertEqual(result["passed"], 6)

    def test_orchestrator_emits_real_workflow_events(self):
        events = []
        profile = {"skin_type":"oily", "concern":"acne", "budget_inr":1800,
                   "allergies":[], "current_products":[], "current_ingredient_names":[]}
        result = OrchestratorAgent().run(profile, event_callback=lambda event, state: events.append(event))
        self.assertTrue(events)
        self.assertEqual(events, result["workflow_events"])
        self.assertIn("Research Agent", {event["agent"] for event in events})
        self.assertIn("Safety Agent", {event["agent"] for event in events})
        self.assertEqual(events[-1]["status"], "completed")

    def test_agent_contract_outputs_present(self):
        research = ResearchAgent().retrieve("oily skin acne", top_k=2)
        self.assertEqual(research["agent"], "Research Agent")
        self.assertIn("snippets", research["data"])
        result = OrchestratorAgent().run({"skin_type":"oily","concern":"acne","budget_inr":1500,
                                          "allergies":[],"current_products":[]})
        self.assertIn("agent_outputs", result)
        for name in ("Research Agent", "Product Agent", "Safety Agent", "Routine Agent"):
            self.assertIn(name, result["agent_outputs"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
