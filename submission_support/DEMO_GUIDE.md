# SkinSage — Five-minute live demo guide (not the PPT)

## Before presenting
- Open the SkinSage project in VS Code.
- Start the app with `streamlit run app.py`.
- Confirm the browser is open and the sidebar is visible.
- Avoid showing the terminal unless asked; keep the app ready at the profile form.
- Do not claim a test passed unless the test command was run.

## Suggested 5-minute sequence

### 0:00–0:35 — Problem and purpose
“SkinSage is a domain-specific multi-agent AI proof of concept for personal-care product planning. People can find it difficult to compare ingredients, consider their current products, and stay within budget. SkinSage coordinates research, product selection, and validation. It is educational and does not diagnose or replace a dermatologist.”

### 0:35–1:25 — Normal plan
- Select skin type: Oily.
- Concern: Acne.
- Budget: ₹1500.
- Leave allergies and current ingredients empty.
- Click “Create my skincare plan”.
- Point out the AM/PM routine, prices, remaining budget, and knowledge IDs.
- Explain that the catalogue is synthetic.

### 1:25–2:30 — Show agent collaboration
- Open “Agent control room”.
- Point to Research Agent retrieval, Product Agent selection, Safety Agent decision, and Routine Agent status.
- Explain the orchestrator’s bounded feedback loop: rejected product IDs are fed back to the Product Agent for a replacement attempt.
- If the normal plan does not trigger a retry, use the next scenario to show safety feedback.

### 2:30–3:35 — Ingredient safety scenario
- Enter `salicylic acid` in the current-product ingredients field and generate a plan.
- Open Agent control room and point out the safety decision and orchestration logs.
- Explain that configured ingredient rules are conservative demo policies; they are not universal medical contraindications.
- If the planner avoids the conflict without a retry, say that it filtered the candidate during selection; use the planted-conflict tests to demonstrate explicit rejection/replacement behaviour.

### 3:35–4:10 — Referral gate
- Choose “painful acne” and generate.
- Show that the system blocks routine generation and recommends professional assessment.
- Explain that this is a safety boundary, not diagnosis.

### 4:10–4:40 — Evaluation
- Open Evaluation and run the retrieval benchmark.
- Explain that a hit means at least one expected knowledge-base ID appears in the top three results.
- Current local run: 10/10 queries hit (100%) on the small hand-authored set.
- Current automated test run: 4 tests passed. This is a small PoC test suite, not proof of clinical accuracy.

### 4:40–5:00 — Limitations and close
“Limitations include synthetic products, a small local knowledge base, simple ingredient parsing, and conservative rules. Future work could include a clinician-reviewed knowledge base, richer label parsing, broader test sets, and user studies. SkinSage demonstrates an orchestrated workflow with retrieval, execution, validation, and feedback rather than a standalone chatbot.”

## Important presentation honesty
- Do not call the product catalogue real or recommend purchasing these fictional products.
- Do not claim an LLM, LangChain, LangGraph, MCP, or autonomous model planner is used; this implementation uses Python classes, TF-IDF, rules, and Streamlit.
- Retrieval scores are relevance signals, not medical confidence scores.
- Avoid claiming every selected product is clinically suitable; the checks are simplified.
