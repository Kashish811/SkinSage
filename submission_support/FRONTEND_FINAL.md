# SkinSage Frontend — Final Implementation Notes

## Views
- **Home:** profile summary, workflow overview, latest plan state and planner decisions.
- **My Skin Profile:** summary of the profile used for the latest workflow run.
- **Routine Planner:** AM/PM routine cards, cost, budget remaining, source IDs and structured product output.
- **Inline Technical Insights toggle:** an opt-in sidebar toggle reveals agent status cards, event timeline, planner actions, attempt history and agent output contracts within the current page. There is no separate developer-mode page; ordinary users see friendly progress by default.
- **Safety & Comparison:** actual safety checks, product-level audit, validation attempts and candidate ranking.
- **Research Explorer:** searchable local knowledge library, source labels/URLs, retrieved-ID highlighting and relevance scores.
- **What-if Simulator:** reruns the same orchestrator with changed constraints and compares product IDs and costs against the baseline.
- **Evaluation Centre:** retrieval benchmark, end-to-end scenarios, detailed tables and rate chart.

## Actual workflow integration
`OrchestratorAgent.run(profile, event_callback=...)` now emits workflow events when the orchestrator starts, retrieves research, selects candidates, validates a plan, decides to replan, blocks routine generation or finalises a plan. The Streamlit frontend consumes these callbacks and updates user-friendly progress during execution. If Technical Insights is enabled, the same in-place progress area also shows the actual agent event timeline. The completed event list is persisted in the returned workflow state and exposed through an inline technical expander on the current result page.

The UI is driven by the returned `agent_status`, `workflow_events`, `planner_decisions`, `attempt_history`, `safety_result`, `routine_comparison`, `retrieved_sources` and `final_routine`. The live timeline is not a decorative animation or hardcoded success sequence.

## Run and verify
```bash
python -m pip install -r requirements.txt
streamlit run app.py
python -m unittest discover -s tests -v
python evaluation.py
```

## Honest limitations
- Product catalogue and prices are synthetic.
- Ranking scores are deterministic heuristics, not clinical efficacy scores.
- Ingredient-pair rules are conservative demonstration warnings, not universal contraindications.
- Source-ID/category checks are traceability heuristics; they do not prove that every recommendation is scientifically established.
- The application is an educational prototype, not medical advice or a diagnostic tool.
