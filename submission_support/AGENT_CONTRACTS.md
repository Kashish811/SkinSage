# SkinSage Agent Contracts

All agents exchange Python dictionaries. The Orchestrator maintains the shared state and an audit log.

## Research Agent
**Input:** query string or user profile dictionary.  
**Output:** `{"agent": "Research Agent", "status": "completed", "data": {"snippets": [...]}, "reasons": [], "metadata": {...}}`  
Each snippet includes a KB ID, topic, text, TF-IDF score, source label, and URL.

## Product Agent
**Input:** shared workflow state containing `user_input` and `rejected_product_ids`.  
**Output:** list of candidate product dictionaries; the selection summary records selected/excluded/missing decisions and reasons. Products contain ID, category, price, normalized ingredients, suitability metadata, and source IDs.

## Safety Agent
**Input:** candidate plan and state containing the user profile/current products.  
**Output:** approval Boolean, validation reasons, implicated `rejected_product_ids`, total cost, budget, and per-check results. The source check verifies that at least one valid source ID is category-relevant under `CATEGORY_SOURCE_REQUIREMENTS`; this is a deterministic relevance heuristic, not semantic proof that a citation supports a claim.

## Routine Agent
**Input:** a plan, an approved Safety Agent result, and retrieved snippets.  
**Output:** AM/PM steps with product details, a short explanation, a relevant local KB citation ID, and source metadata. It is template-based and does not call Ollama.

## Orchestrator
**Input:** user profile.  
**Output:** shared state including task plan, candidate products, agent statuses, structured agent outputs, logs, retry count, safety result, referral status, and final routine. It allows at most two retry attempts after the initial attempt.
