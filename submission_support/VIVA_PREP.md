# SkinSage — Viva preparation (not the PPT/report)

## 1. What problem does SkinSage solve?
It helps structure an educational skincare product-planning workflow around user-entered skin type, concern, budget, existing ingredients, and avoid-list preferences. It retrieves relevant snippets, selects synthetic product candidates, validates the plan, and creates an AM/PM routine only if approved.

## 2. Why did you choose this domain?
Personal-care product choices can be confusing because users compare concerns, ingredients, existing products, and prices. The PoC demonstrates how a multi-step workflow can make that selection process more structured. It does not diagnose or treat skin conditions.

## 3. Why is this agentic and not just a chatbot?
It has multiple specialised components coordinated by an orchestrator. The system retrieves information, executes candidate selection, validates outputs, can reject candidates and retry with feedback, and gates routine generation on validation. It does not simply return a single text response.

## 4. What does the Orchestrator do?
It defines the task sequence, stores shared state, calls agents in order, collects safety feedback, tracks rejected product IDs, and enforces a maximum of two retries.

## 5. What does the Research Agent use?
TF-IDF vectorisation and cosine similarity over a local knowledge base. It returns snippets with local KB IDs, retrieval scores, and reference metadata. TF-IDF is a lightweight lexical retrieval baseline, not a large language model.

## 6. What does the Product Agent do?
It filters a synthetic CSV catalogue by category, skin type, concern, budget, and ingredients the user wants to avoid. It excludes previously rejected product IDs during retry attempts.

## 7. What does the Safety Agent validate?
Budget, required product categories, known product IDs, knowledge-source IDs, allergy/avoid-list matches, repeated active ingredients, and configured ingredient-pair warnings.

## 8. What happens when validation fails?
The Safety Agent returns reasons and implicated product IDs. The Orchestrator adds those IDs to a rejected set and asks the Product Agent to try again, up to the retry limit. If no safe complete plan is approved, the Routine Agent does not generate a routine.

## 9. How does the referral gate work?
For configured high-risk concerns such as painful or scarring acne, persistent rash, or severe irritation, the application returns a referral message and blocks routine generation before product selection.

## 10. What data is used?
A local JSON knowledge base, a synthetic product CSV, JSON safety rules, ten predefined retrieval queries, and three planted conflict profiles. Product names and prices are fictional.

## 11. What is the evaluation result?
The current local run reports 10/10 retrieval queries with at least one expected ID in the top three (100% hit rate), and four automated unit tests pass. This is a small hand-authored benchmark; it does not establish clinical accuracy or generalisation.

## 12. What are the main limitations?
Synthetic products, small knowledge base, basic comma-separated current-ingredient input, limited ingredient synonyms, simplified rules, and no diagnosis. The source IDs provide traceability to snippets but do not independently establish clinical validity.

## 13. Why not use a paid LLM API?
The assignment permits local/free implementations and does not require paid APIs. The PoC focuses on visible orchestration and validation using Python, Streamlit, TF-IDF, and explicit rules, which makes the workflow deterministic and easier to explain.

## 14. What is novel about the project?
The contribution is the integrated workflow: retrieval, profile-aware candidate selection, explicit safety validation, bounded feedback/replacement, a referral gate, and traceable outputs in one small domain-specific PoC. Avoid claiming the underlying techniques are novel research.

## 15. What could be improved in future?
Clinician-reviewed knowledge, verified source mapping for each recommendation, richer ingredient-label parsing and synonyms, larger evaluation datasets, a human review path, privacy review, and usability testing.

## 16. Is the system medically safe?
It is not a medical device and should not be described as clinically safe. It demonstrates conservative educational checks and referral gating. Real-world use would require expert review, validated content, robust ingredient interpretation, and formal testing.

## Commands to know
Run tests:
`python -m unittest discover -s tests -v`

Run retrieval evaluation:
`python evaluation.py`

Launch UI:
`streamlit run app.py`
