# SkinSage — Multi-Agent Skincare Planner

SkinSage is a local, educational proof of concept for a domain-specific agentic AI workflow. It demonstrates retrieval, product candidate selection, safety validation, a bounded rejection/replacement loop, and final routine generation.

> **Important:** This is not medical advice. All product names and prices in `data/products.csv` are synthetic. Ingredient combination rules are conservative demo policies, not universal medical contraindications. High-risk concerns block routine generation and trigger a referral message.

## Requirements
- Python 3.10 or newer
- Internet access only for initial package installation (the app itself uses local files; it does not call paid APIs)

## Run on Windows
Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser. Choose a skin type, concern, budget, any known allergies/ingredients to avoid, and optionally type current product ingredients separated by commas. Click **Generate / Replan**. Use the navigation bar to explore the Routine Planner, Safety & Comparison, Research Explorer, What-if Simulator and Evaluation Centre. The sidebar toggle **View technical insights** reveals the real workflow timeline and agent-level diagnostics inline on the current result page; it is off by default and does not switch to a separate developer page.

## Run tests
With the virtual environment activated:

```bash
python -m unittest discover -s tests -v
python evaluation.py
```

Tests cover planted safety conflicts, replacement plans, the high-risk referral gate, retrieval evaluation, product-level audit/planner outputs, the end-to-end scenario suite and real orchestrator event callbacks. Do not claim a test passed unless you have run it in your environment.

## Project structure
```text
SkinSage/
├── app.py
├── agents.py
├── orchestrator.py
├── evaluation.py
├── requirements.txt
├── README.md
├── data/
│   ├── knowledge_base.json
│   ├── products.csv
│   ├── conflict_rules.json
│   ├── demo_profiles.json
│   ├── planted_conflicts.json
│   └── evaluation_queries.json
└── tests/
    └── test_safety.py
```

## Agent workflow
1. **Research Agent:** TF-IDF retrieval over local educational snippets.
2. **Product Agent:** selects one candidate per category within the budget and excludes rejected candidates.
3. **Safety Agent:** validates required categories, budget, product/source IDs, avoid-list matches, repeated actives, and configured ingredient-pair rules.
4. **Orchestrator:** feeds rejected product IDs back to the Product Agent, with a maximum of two retries.
5. **Routine Agent:** creates AM/PM output only after safety approval.

## Data and traceability
Every product has local knowledge-base source IDs. The knowledge snippets include reference labels and links for further reading; these links are not a substitute for a clinical review. TF-IDF retrieval is a lightweight baseline, not a medical-grade retrieval system.

## Limitations
- Product catalogue, names, and prices are fictional.
- Current-product input is a basic comma-separated ingredient field, not a full ingredient-label parser.
- Ingredient rules are deliberately conservative and simplified.
- No diagnosis, prescription, or treatment guarantee is provided.

## Enhanced agentic workflow (October 2026)

This version adds the following demonstrable capabilities:

- **Explicit planning and replanning:** the orchestrator emits actions such as `RESEARCH_AND_DRAFT`, `REPLACE_PRODUCT`, `REPLAN_WITH_EXCLUSIONS`, `FINALISE_PLAN`, and `REFER_TO_DERMATOLOGIST`. It feeds rejected product IDs back to the Product Agent and caps retries.
- **Evidence traceability:** knowledge snippets carry a KB ID, source name, URL and retrieval score. Routine steps link back to mapped KB IDs. Source-ID/category checks are heuristic traceability checks, not semantic fact verification.
- **Explainable safety audit:** the Safety Agent returns per-product audit rows, named checks, pass/fail counts, rejected IDs, reasons and total cost.
- **Candidate comparison:** the Product Agent ranks eligible synthetic products with a transparent heuristic based on profile/concern fit, user planning preference, formula simplicity and price. The Safety Agent is always a hard gate; heuristic scores are not clinical efficacy scores.
- **What-if simulator:** vary skin type, concern, budget, ingredients to avoid, existing ingredients and planning preference to compare a second workflow run.
- **Evaluation suite:** retrieval benchmark plus deterministic end-to-end scenarios for standard and sensitive profiles, tight budgets, ingredient avoidance, existing active overlap and referral gating.
- **Session-only preference:** the selected planning preference is held in Streamlit session state/profile for the current session; it is not a persistent user profile or a learned medical model.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Run verification:

```bash
python -m py_compile app.py agents.py orchestrator.py evaluation.py
python -m unittest discover -s tests -v
python evaluation.py
```

All product names and prices are synthetic. The source links are further-reading references for the associated local knowledge snippets; this prototype does not automatically verify every claim against the live page. The ingredient interaction policy is deliberately conservative and must not be presented as universal medical advice. SkinSage is an educational prototype, not a diagnostic tool.


## Frontend experience

The Streamlit interface keeps a user-facing experience with Home, My Skin Profile, Routine Planner, Safety & Comparison, Research Explorer, What-if Simulator, and Evaluation Centre. Technical details are revealed with the sidebar toggle **View technical insights**, inline on the current result page rather than on a separate developer page. During execution, callback-driven progress reflects actual orchestrator events; when the toggle is enabled, the same callback also exposes agent names and event details. The completed inline technical panel includes agent statuses, execution timeline, planner decisions, attempt history, and agent input/output contracts. The audit and comparison views use the returned safety checks, attempt history, candidate ranking and planner decisions.

The frontend uses a warm ivory/sage visual system, responsive layout, profile wizard, AM/PM product cards, source explorer, safety audit and original-versus-what-if comparison. It uses local data and deterministic agents; Google Fonts may load from the network for typography, but no paid AI API is used.
