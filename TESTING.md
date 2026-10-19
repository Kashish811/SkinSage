# Testing and evaluation

## Automated tests
Run:
```bash
python -m unittest discover -s tests -v
```

The tests exercise:
- Three planted conflict cases (retinol + salicylic acid, duplicate glycolic acid, duplicate benzoyl peroxide).
- Whether the safety agent identifies the candidate product that should be rejected.
- Whether the corresponding replacement candidate passes the demo safety checks.
- The dermatologist referral gate for a high-risk concern.
- Whether the retrieval evaluation loads and runs over ten queries.
- Whether the orchestrator emits real workflow events through its callback and persists the same events in the final state.
- Product-level audit outputs, planner decisions, and the six-scenario end-to-end suite.

## Retrieval metric
`evaluation.py` measures top-k hit rate: a query counts as a hit when at least one expected knowledge-base ID appears in the retrieved top-k results. This is a small hand-authored test set, not a statistically representative benchmark.

## Manual checks
1. Start the app and submit a normal profile; watch the callback-driven live agent execution timeline.
2. Enter `salicylic acid` in current product ingredients and observe the safety/retry log.
3. Select `painful acne` and confirm that the app shows a referral message and does not generate a routine.
4. Enter a known avoid-list ingredient and verify the app avoids matching synthetic products where possible.
5. Use a low budget and confirm that the safety gate does not approve a plan that exceeds it.

Record actual outputs from your run before presenting evaluation results.
