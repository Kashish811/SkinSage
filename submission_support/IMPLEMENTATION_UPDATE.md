# SkinSage — Enhanced Implementation Notes

## New capabilities
1. Explicit orchestrator action log and bounded feedback/replanning loop.
2. Attempt history showing selected IDs, costs, approval and rejection reasons.
3. Per-product Safety Agent audit table and check pass/fail summary.
4. Candidate ranking and alternatives table with visible heuristic scores.
5. What-if simulator for profile, budget, avoid-list, current ingredients and planning preference.
6. End-to-end evaluation suite for six deterministic scenarios, in addition to ten-query retrieval evaluation.
7. Planning preference choices: balanced fit, lowest price, fewer active ingredients.
8. Source names/URLs remain visible alongside local KB identifiers; source validation is explicitly described as heuristic rather than scientific proof.

## Architecture
Streamlit UI → Orchestrator / Planner → Research Agent (TF-IDF over local KB) → Product Agent (synthetic CSV, profile filters and ranked candidates) → Safety Agent (budget, category, source-ID, avoid-list, duplicate-active and conservative pair-rule checks) → Routine Agent (only after safety approval) → UI audit/evaluation. Safety feedback loops to candidate selection up to the retry limit. High-risk concerns are routed before product selection.

## Important limitations
- No paid API or external LLM is used; planning is a deterministic rule-based agentic workflow.
- Source ID validation checks known IDs and category mappings, not whether a source fully supports each sentence.
- Product catalogue is synthetic; no real product should be purchased based on this demo.
- Ingredient pair rules are conservative demo warnings, not universal contraindications.
- Candidate ranking is a transparent heuristic, not a clinical efficacy model.
- Evaluation scenarios are hand-authored software checks, not clinical trials or evidence of medical safety.
