import json
from pathlib import Path
import pandas as pd
from agents import ResearchAgent, SafetyAgent, ProductAgent

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def evaluate_retrieval(top_k=3):
    queries = json.loads((DATA_DIR / "evaluation_queries.json").read_text(encoding="utf-8"))
    agent = ResearchAgent()
    rows = []
    for item in queries:
        response = agent.retrieve(item["query"], top_k=top_k)
        results = response["data"]["snippets"]
        returned = [x["id"] for x in results]
        expected = set(item["expected_ids"])
        hit = bool(expected.intersection(returned))
        rows.append({"query": item["query"], "expected_ids": ", ".join(item["expected_ids"]),
                     "top_k_ids": ", ".join(returned), "hit": hit})
    hits = sum(r["hit"] for r in rows)
    return {"passed": hits, "total": len(rows), "accuracy": hits / len(rows) if rows else 0,
            "details": pd.DataFrame(rows)}

def evaluate_plan(plan, user_input):
    safety = SafetyAgent()
    state = {"user_input": user_input}
    result = safety.validate(plan, state)
    source_ok = all(p.get("source_ids") and all(s in safety.valid_source_ids for s in p["source_ids"]) for p in plan)
    allergy_ok = not any(pid in result.get("rejected_product_ids", []) for pid in [p.get("product_id") for p in plan])
    return {"budget_ok": result["total_cost_inr"] <= int(user_input.get("budget_inr", 1500)),
            "source_ids_ok": source_ok, "safety_approved": result["approved"],
            "allergy_and_conflict_checks_passed": allergy_ok, "safety_result": result}

def run_evaluation():
    result = evaluate_retrieval()
    print(f"Retrieval hit rate: {result['passed']}/{result['total']} ({result['accuracy']:.0%})")
    print(result["details"].to_string(index=False))

if __name__ == "__main__":
    run_evaluation()


def evaluate_system():
    """Run deterministic, local end-to-end scenarios; metrics are prototype checks, not clinical validation."""
    from orchestrator import OrchestratorAgent
    scenarios = [
        {"name":"Standard profile", "profile":{"skin_type":"oily","concern":"acne","budget_inr":1500,"allergies":[],"current_products":[]}, "expect_routine":True},
        {"name":"Sensitive skin", "profile":{"skin_type":"sensitive","concern":"dryness","budget_inr":1800,"allergies":[],"current_products":[]}, "expect_routine":True},
        {"name":"Tight budget", "profile":{"skin_type":"normal","concern":"dullness","budget_inr":500,"allergies":[],"current_products":[]}, "expect_routine":False},
        {"name":"Known ingredient avoid", "profile":{"skin_type":"oily","concern":"acne","budget_inr":1800,"allergies":["salicylic acid"],"current_products":[]}, "expect_routine":True},
        {"name":"Existing active overlap", "profile":{"skin_type":"oily","concern":"acne","budget_inr":2000,"allergies":[],"current_products":[{"name":"Current serum","ingredients":["salicylic acid"]}],"current_ingredient_names":["salicylic acid"]}, "expect_routine":True},
        {"name":"Referral gate", "profile":{"skin_type":"oily","concern":"painful acne","budget_inr":1500,"allergies":[],"current_products":[]}, "expect_referral":True},
    ]
    rows=[]
    for item in scenarios:
        result=OrchestratorAgent().run(item["profile"])
        routine=bool(result.get("final_routine"))
        referral=bool(result.get("referral_required"))
        safety_ok=bool(result.get("safety_result",{}).get("approved")) if routine else False
        budget_ok=(result.get("safety_result",{}).get("total_cost_inr",0) <= item["profile"].get("budget_inr",0)) if routine else not item.get("expect_routine",False)
        passed=(referral == item.get("expect_referral",False)) and (routine == item.get("expect_routine",False)) and (not routine or safety_ok) and (budget_ok if routine else True)
        rows.append({"scenario":item["name"],"expected_routine":item.get("expect_routine",False),"routine_generated":routine,
                     "referral_triggered":referral,"safety_approved":safety_ok,"budget_compliant":budget_ok,
                     "attempts":len(result.get("attempt_history",[])),"passed":passed,
                     "notes":"; ".join(result.get("rejection_reasons",[])) or ("Referral gate engaged" if referral else "")})
    frame=pd.DataFrame(rows)
    return {"passed":int(frame["passed"].sum()),"total":len(frame),"accuracy":float(frame["passed"].mean()) if len(frame) else 0.0,
            "safety_approval_rate":float(frame.loc[frame["routine_generated"],"safety_approved"].mean()) if frame["routine_generated"].any() else 0.0,
            "budget_compliance_rate":float(frame.loc[frame["routine_generated"],"budget_compliant"].mean()) if frame["routine_generated"].any() else 0.0,
            "details":frame}
