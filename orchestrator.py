from agents import ResearchAgent, ProductAgent, SafetyAgent, RoutineAgent, agent_result

REFERRAL_CONCERNS = {
    "severe acne", "painful acne", "scarring acne", "persistent rash",
    "severe irritation", "rapidly worsening skin condition"
}

class OrchestratorAgent:
    """Coordinates agent contracts. Shared state is the workflow context and audit trail."""
    def __init__(self, max_retries=2):
        self.research_agent = ResearchAgent()
        self.product_agent = ProductAgent()
        self.safety_agent = SafetyAgent()
        self.routine_agent = RoutineAgent()
        self.max_retries = min(2, max(0, int(max_retries)))

    def run(self, user_input, event_callback=None):
        """Execute the workflow. Optional callback receives real workflow events for live UI rendering."""
        def emit(agent, status, message, details=None):
            event = {"agent": agent, "status": status, "message": message, "details": details or {}}
            state.setdefault("workflow_events", []).append(event)
            if event_callback:
                event_callback(event, state)

        state = {
            "user_input": dict(user_input),
            "task_plan": [
                {"step": 1, "agent": "Research Agent", "purpose": "retrieve relevant knowledge"},
                {"step": 2, "agent": "Product Agent", "purpose": "select profile-aware candidates"},
                {"step": 3, "agent": "Safety Agent", "purpose": "validate plan and return actionable feedback"},
                {"step": 4, "agent": "Routine Agent", "purpose": "generate cited routine only after approval"}
            ],
            "retrieved_sources": [], "candidate_products": [], "safety_result": None,
            "retry_count": 0, "rejection_reasons": [], "rejected_product_ids": [],
            "agent_status": {}, "agent_logs": [], "agent_outputs": {}, "final_routine": None,
            "planner_decisions": [], "attempt_history": [], "routine_comparison": [], "session_preferences": {}, "workflow_events": []
        }
        emit("Orchestrator", "running", "Created a task plan and shared workflow state.", {"task_plan": state["task_plan"]})

        concern = str(user_input.get("concern", "")).strip().lower()
        emit("Research Agent", "running", "Retrieving profile-relevant knowledge from the local research library.")
        state["retrieved_sources"] = self.research_agent.search_for_user(user_input)
        state["agent_status"]["Research Agent"] = "completed"
        state["agent_outputs"]["Research Agent"] = agent_result(
            "Research Agent", "completed", {"snippets": state["retrieved_sources"]},
            metadata={"count": len(state["retrieved_sources"])}
        )
        state["agent_logs"].append(
            f"Research Agent: retrieved {len(state['retrieved_sources'])} snippets with IDs and TF-IDF relevance scores."
        )
        emit("Research Agent", "completed", f"Retrieved {len(state['retrieved_sources'])} knowledge snippets with IDs and relevance scores.", {"count": len(state["retrieved_sources"])})

        if concern in REFERRAL_CONCERNS:
            state["planner_decisions"].append({"action": "REFER_TO_DERMATOLOGIST", "reason": f"Concern '{concern}' is outside the prototype's safe scope."})
            state["referral_required"] = True
            state["referral_message"] = (
                "This concern is outside the safe scope of an automated cosmetic routine. "
                "Please consult a qualified dermatologist; seek urgent care for breathing difficulty "
                "or swelling of the lips/tongue."
            )
            state["agent_status"].update({
                "Product Agent": "skipped by referral gate",
                "Safety Agent": "skipped by referral gate",
                "Routine Agent": "blocked by referral gate"
            })
            state["agent_logs"].append("Orchestrator: high-risk concern detected; blocked product selection and routine generation.")
            emit("Orchestrator", "blocked", "Referral gate activated; product selection and routine generation are blocked.", {"concern": concern})
            return state

        state["referral_required"] = False
        state["planner_decisions"].append({"action": "RESEARCH_AND_DRAFT", "reason": "Profile is within the prototype's cosmetic-guidance scope; retrieve evidence and draft candidates."})
        for attempt in range(self.max_retries + 1):
            state["retry_count"] = attempt
            emit("Product Agent", "running", f"Selecting candidates (attempt {attempt + 1}).", {"excluded_ids": list(state["rejected_product_ids"])})
            plan = self.product_agent.select_products(state)
            state["candidate_products"] = plan
            state["agent_status"]["Product Agent"] = f"completed (attempt {attempt + 1})"
            state["agent_outputs"]["Product Agent"] = agent_result(
                "Product Agent", "completed", {"products": plan},
                metadata={"attempt": attempt + 1, "rejected_ids_received": list(state["rejected_product_ids"]),
                          "selection_summary": state.get("product_selection_summary", {})}
            )
            state["agent_logs"].append(
                f"Product Agent: selected {len(plan)} products on attempt {attempt + 1}; "
                f"received rejected IDs {state['rejected_product_ids'] or 'none'}."
            )
            emit("Product Agent", "completed", f"Selected {len(plan)} candidates on attempt {attempt + 1}.", {"product_ids": [p.get("product_id") for p in plan]})
            emit("Safety Agent", "running", "Validating budget, categories, source mapping, avoid-list entries and ingredient rules.", {"attempt": attempt + 1})

            safety = self.safety_agent.validate(plan, state)
            state["safety_result"] = safety
            state["attempt_history"].append({"attempt": attempt + 1,
                "product_ids": [p.get("product_id") for p in plan],
                "total_cost_inr": sum(int(p.get("price_inr", 0)) for p in plan),
                "approved": bool(safety["approved"]), "reasons": list(safety.get("reasons", [])),
                "rejected_product_ids": list(safety.get("rejected_product_ids", []))})
            state["agent_status"]["Safety Agent"] = "approved" if safety["approved"] else "rejected"
            state["agent_outputs"]["Safety Agent"] = agent_result(
                "Safety Agent", "approved" if safety["approved"] else "rejected",
                {"rejected_product_ids": safety["rejected_product_ids"], "checks": safety["checks"],
                 "total_cost_inr": safety["total_cost_inr"]},
                reasons=safety["reasons"], metadata={"attempt": attempt + 1}
            )
            emit("Safety Agent", "approved" if safety["approved"] else "rejected", "All configured checks passed." if safety["approved"] else f"Rejected candidate plan: {'; '.join(safety['reasons'][:3])}", {"approved": safety["approved"], "reasons": safety["reasons"], "rejected_product_ids": safety["rejected_product_ids"], "check_summary": safety.get("check_summary", {})})
            if safety["approved"]:
                state["planner_decisions"].append({"action": "FINALISE_PLAN", "reason": f"Safety checks passed on attempt {attempt + 1}; routine generation is now permitted."})
                state["agent_logs"].append(
                    f"Safety Agent: approved on attempt {attempt + 1}; all configured checks passed."
                )
                state["final_routine"] = self.routine_agent.generate(plan, safety, state["retrieved_sources"])
                state["agent_status"]["Routine Agent"] = "completed"
                state["agent_outputs"]["Routine Agent"] = agent_result(
                    "Routine Agent", "completed", {"routine": state["final_routine"]}
                )
                state["agent_logs"].append("Routine Agent: generated AM/PM steps with per-step explanations and source IDs.")
                emit("Routine Agent", "completed", "Generated the routine after Safety Agent approval.", {"AM_steps": len(state["final_routine"].get("AM", [])), "PM_steps": len(state["final_routine"].get("PM", []))})
                break

            state["rejection_reasons"] = safety["reasons"]
            if any("Budget exceeded" in r for r in safety["reasons"]):
                action = "REVISE_BUDGET_OR_SELECTION"
            elif safety.get("rejected_product_ids"):
                action = "REPLACE_PRODUCT"
            else:
                action = "REQUEST_CLARIFICATION_OR_STOP"
            state["planner_decisions"].append({"action": action, "reason": "Safety Agent returned actionable feedback: " + " | ".join(safety["reasons"])})
            emit("Orchestrator", "replanning", f"Planner action: {action}", {"reasons": safety["reasons"], "rejected_product_ids": safety.get("rejected_product_ids", [])})
            state["agent_logs"].append(
                "Safety Agent: rejected candidate plan. Reasons: " + " | ".join(safety["reasons"])
            )
            new_ids = set(safety.get("rejected_product_ids", []))
            state["rejected_product_ids"] = sorted(set(state["rejected_product_ids"]) | new_ids)
            if attempt < self.max_retries and new_ids:
                state["planner_decisions"].append({"action": "REPLAN_WITH_EXCLUSIONS", "reason": f"Excluded rejected IDs {sorted(new_ids)} and rerun candidate selection."})
                state["agent_logs"].append(
                    f"Orchestrator: explicit feedback sent to Product Agent; excluding {sorted(new_ids)} on next attempt."
                )
                emit("Orchestrator", "replanning", f"Feedback loop: exclude {sorted(new_ids)} and select again.", {"excluded_ids": sorted(new_ids)})
            else:
                state["agent_logs"].append("Orchestrator: retry limit reached or no actionable product IDs; final routine withheld.")
                state["final_routine"] = None
                state["agent_status"]["Routine Agent"] = "blocked: safety validation failed"
                state["agent_outputs"]["Routine Agent"] = agent_result(
                    "Routine Agent", "blocked", {},
                    reasons=["Routine generation requires Safety Agent approval."]
                )
                emit("Routine Agent", "blocked", "Routine withheld because safety approval was not obtained.")
                break
        if state.get("final_routine"):
            chosen_ids = {p["product_id"] for p in state.get("candidate_products", [])}
            comparison = []
            for decision in state.get("product_selection_summary", {}).get("decisions", []):
                if decision.get("decision") == "selected":
                    for candidate in decision.get("top_candidates", []):
                        comparison.append({**candidate, "selected": candidate["product_id"] in chosen_ids,
                                           "score_basis": "profile/concern fit + formula simplicity heuristic + budget efficiency; safety is a hard gate"})
            state["routine_comparison"] = sorted(comparison, key=lambda x: (not x["selected"], -x["score"], x["price_inr"]))
        emit("Orchestrator", "completed", "Workflow finished; final state and audit trail are ready.", {"routine_approved": bool(state.get("final_routine")), "attempts": len(state.get("attempt_history", []))})
        return state
