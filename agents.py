from pathlib import Path
import json
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CATEGORY_SOURCE_REQUIREMENTS = {
    "Cleanser": {"KB-01", "KB-02", "KB-03", "KB-04", "KB-12", "KB-14"},
    "Serum": {"KB-05", "KB-06", "KB-07", "KB-08", "KB-09", "KB-10", "KB-11", "KB-15", "KB-17", "KB-18"},
    "Moisturizer": {"KB-01", "KB-03", "KB-04", "KB-12", "KB-14"},
    "Sunscreen": {"KB-01", "KB-13", "KB-17"}
}

def split_semicolon(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [part.strip().lower() for part in str(value).split(";") if part.strip()]

def normalize_ingredient(value):
    value = re.sub(r"\s+", " ", str(value).strip().lower())
    aliases = {
        "aha": "glycolic acid",
        "alpha hydroxy acid": "glycolic acid",
        "bha": "salicylic acid",
        "l-ascorbic acid": "vitamin c",
        "ascorbic acid": "vitamin c",
        "vit c": "vitamin c",
        "retinoid": "retinol",
        "benzoyl-peroxide": "benzoyl peroxide",
    }
    return aliases.get(value, value)

def parse_ingredients(value):
    return [normalize_ingredient(x) for x in split_semicolon(value)]

def parse_sources(value):
    return [x.upper() for x in split_semicolon(value)]

def agent_result(agent, status, data=None, reasons=None, metadata=None):
    """Standard output envelope shared by all agents."""
    return {
        "agent": agent,
        "status": status,
        "data": data if data is not None else {},
        "reasons": reasons or [],
        "metadata": metadata or {}
    }

class ResearchAgent:
    """Input contract: query:str or user_input:dict. Output: snippets with IDs, scores, and source metadata."""
    name = "Research Agent"

    def __init__(self):
        self.knowledge = json.loads((DATA_DIR / "knowledge_base.json").read_text(encoding="utf-8"))
        self.documents = [
            " ".join([item["topic"], item["text"], " ".join(item.get("tags", []))])
            for item in self.knowledge
        ]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(self.documents)
        self.by_id = {item["id"]: item for item in self.knowledge}

    def retrieve(self, query, top_k=5):
        scores = cosine_similarity(self.vectorizer.transform([str(query)]), self.matrix)[0]
        ranked = scores.argsort()[::-1][:top_k]
        snippets = [
            {"id": self.knowledge[i]["id"], "topic": self.knowledge[i]["topic"],
             "text": self.knowledge[i]["text"], "score": float(scores[i]),
             "source_name": self.knowledge[i].get("source_name", "Local project knowledge base"),
             "source_url": self.knowledge[i].get("source_url", "")}
            for i in ranked
        ]
        return agent_result(self.name, "completed", data={"snippets": snippets},
                            metadata={"query": str(query), "top_k": top_k})

    def search_for_user(self, user_input, top_k=5):
        query = " ".join([
            str(user_input.get("skin_type", "")),
            str(user_input.get("concern", "")),
            " ".join(user_input.get("current_ingredient_names", [])),
            "skincare routine safety ingredient advice"
        ])
        return self.retrieve(query, top_k=top_k)["data"]["snippets"]

class ProductAgent:
    """Input contract: state with user_input and rejection feedback. Output: candidate products and selection summary."""
    name = "Product Agent"
    REQUIRED_CATEGORIES = ["Cleanser", "Serum", "Moisturizer", "Sunscreen"]

    def __init__(self):
        self.products = pd.read_csv(DATA_DIR / "products.csv").fillna("")

    def get_product(self, product_id):
        row = self.products[self.products["product_id"] == product_id]
        if row.empty:
            return None
        return self._row_to_product(row.iloc[0])

    def _row_to_product(self, row):
        return {
            "product_id": str(row["product_id"]),
            "name": str(row["name"]),
            "category": str(row["category"]),
            "price_inr": int(float(row["price_inr"])),
            "ingredients": parse_ingredients(row["key_ingredients"]),
            "suitable_skin_types": split_semicolon(row["suitable_skin_types"]),
            "targets_concern": split_semicolon(row["targets_concern"]),
            "source_ids": parse_sources(row["source_ids"]),
            "synthetic": True
        }

    def select_products(self, state):
        user = state["user_input"]
        skin = user.get("skin_type", "normal").lower()
        concern = user.get("concern", "general").lower()
        budget = int(user.get("budget_inr", 1500))
        allergies = {normalize_ingredient(x) for x in user.get("allergies", [])}
        rejected = set(state.get("rejected_product_ids", []))
        selected, spent, decisions = [], 0, []

        for category in self.REQUIRED_CATEGORIES:
            candidates = []
            for _, row in self.products[self.products["category"] == category].iterrows():
                p = self._row_to_product(row)
                if p["product_id"] in rejected:
                    decisions.append({"product_id": p["product_id"], "decision": "excluded", "reason": "Previously rejected by Safety Agent"})
                    continue
                if skin not in p["suitable_skin_types"]:
                    continue
                if category == "Serum" and concern not in p["targets_concern"] and "all" not in p["targets_concern"]:
                    continue
                if any(a and any(a in ing or ing in a for ing in p["ingredients"]) for a in allergies):
                    decisions.append({"product_id": p["product_id"], "decision": "excluded", "reason": "Matches an ingredient to avoid"})
                    continue
                if spent + p["price_inr"] > budget:
                    continue
                candidates.append(p)
            def candidate_score(product):
                score = 0.0
                if concern in product["targets_concern"] or "all" in product["targets_concern"]:
                    score += 3.0
                if skin in product["suitable_skin_types"]:
                    score += 2.0
                preference = user.get("routine_preference", "balanced fit")
                if skin == "sensitive" or preference == "fewer active ingredients":
                    # Conservative preference for simpler formulas; this is a demo heuristic, not clinical evidence.
                    score -= 0.25 * len(product["ingredients"])
                if preference == "lowest price":
                    score -= product["price_inr"] / max(1, budget) * 3.0
                else:
                    score -= product["price_inr"] / max(1, budget)  # budget efficiency tie-breaker
                return score
            candidates.sort(key=lambda p: (-candidate_score(p), p["price_inr"], p["product_id"]))
            if candidates:
                chosen = candidates[0]
                selected.append(chosen)
                spent += chosen["price_inr"]
                decisions.append({"product_id": chosen["product_id"], "decision": "selected", "reason": f"Highest heuristic fit score among eligible {category} candidates; price and formula simplicity are tie-breakers", "score": round(candidate_score(chosen), 3), "alternatives_considered": len(candidates), "preference": user.get("routine_preference", "balanced fit"), "top_candidates": [{"product_id": c["product_id"], "name": c["name"], "price_inr": c["price_inr"], "score": round(candidate_score(c), 3)} for c in candidates[:3]]})
            else:
                decisions.append({"category": category, "decision": "missing", "reason": "No eligible candidate found within filters and remaining budget"})

        state["candidate_products"] = selected
        state["product_selection_summary"] = {
            "selected_count": len(selected), "total_cost_inr": spent,
            "remaining_budget_inr": budget - spent, "decisions": decisions
        }
        return selected

class SafetyAgent:
    """Input contract: plan:list[product], state:user profile. Output: approval, reasons, implicated IDs and checks."""
    name = "Safety Agent"
    ACTIVE_INGREDIENTS = {"retinol", "glycolic acid", "salicylic acid", "benzoyl peroxide", "vitamin c"}

    def __init__(self):
        self.rules = json.loads((DATA_DIR / "conflict_rules.json").read_text(encoding="utf-8"))
        self.knowledge = json.loads((DATA_DIR / "knowledge_base.json").read_text(encoding="utf-8"))
        self.knowledge_by_id = {x["id"]: x for x in self.knowledge}
        self.valid_source_ids = set(self.knowledge_by_id)
        self.products = pd.read_csv(DATA_DIR / "products.csv").fillna("")
        self.valid_product_ids = set(self.products["product_id"].astype(str))

    def _conflict_rule(self, a, b):
        pair = {normalize_ingredient(a), normalize_ingredient(b)}
        for rule in self.rules:
            if pair == {normalize_ingredient(rule["ingredient_a"]), normalize_ingredient(rule["ingredient_b"])}:
                return rule
        return None

    def _source_relevance(self, product):
        allowed = CATEGORY_SOURCE_REQUIREMENTS.get(product.get("category"), set())
        source_ids = set(product.get("source_ids", []))
        valid = source_ids & self.valid_source_ids
        relevant = valid & allowed
        return {
            "valid_source_ids": sorted(valid),
            "relevant_source_ids": sorted(relevant),
            "passed": bool(valid) and bool(relevant),
            "message": "" if valid and relevant else (
                "No valid source ID." if not valid else
                f"No source ID is mapped as relevant to category {product.get('category')}."
            )
        }

    def validate(self, plan, state):
        user = state["user_input"]
        reasons, rejected_ids, checks = [], set(), []
        budget = int(user.get("budget_inr", 1500))
        total = sum(int(p.get("price_inr", 0)) for p in plan)
        if total > budget:
            reasons.append(f"Budget exceeded: ₹{total} > ₹{budget}.")
            checks.append({"check": "budget", "passed": False})
        else:
            checks.append({"check": "budget", "passed": True})

        categories = {p.get("category") for p in plan}
        for required in ProductAgent.REQUIRED_CATEGORIES:
            if required not in categories:
                reasons.append(f"Required category missing: {required}.")
        checks.append({"check": "required_categories", "passed": all(c in categories for c in ProductAgent.REQUIRED_CATEGORIES)})

        for p in plan:
            pid = p.get("product_id")
            if pid not in self.valid_product_ids:
                reasons.append(f"Unknown product ID: {pid}.")
                if pid:
                    rejected_ids.add(pid)
            source_check = self._source_relevance(p)
            if not source_check["passed"]:
                reasons.append(f"{p.get('name', pid)} failed source relevance validation: {source_check['message']}")
                if pid:
                    rejected_ids.add(pid)
            checks.append({"check": "source_relevance", "product_id": pid, **source_check})

            ingredients = {normalize_ingredient(x) for x in p.get("ingredients", [])}
            allergies = {normalize_ingredient(x) for x in user.get("allergies", [])}
            matches = {i for i in ingredients for a in allergies if a and (a in i or i in a)}
            if matches:
                reasons.append(f"{p.get('name', pid)} contains ingredient(s) matching an avoid/allergy entry: {', '.join(sorted(matches))}.")
                if pid:
                    rejected_ids.add(pid)
            checks.append({"check": "avoid_list", "product_id": pid, "passed": not bool(matches), "matches": sorted(matches)})

        # Pair selected products against each other and against existing products.
        entries = []
        for p in plan:
            entries.append((p.get("product_id"), p.get("name", "selected product"),
                            {normalize_ingredient(x) for x in p.get("ingredients", [])}))
        for current in user.get("current_products", []):
            entries.append((None, current.get("name", "current product"),
                            {normalize_ingredient(x) for x in current.get("ingredients", [])}))

        for i in range(len(entries)):
            id_a, name_a, ing_a = entries[i]
            for j in range(i + 1, len(entries)):
                id_b, name_b, ing_b = entries[j]
                shared = (ing_a & ing_b) & self.ACTIVE_INGREDIENTS
                if shared:
                    for active in sorted(shared):
                        reasons.append(f"Repeated active '{active}' in {name_a} and {name_b}; conservative demo policy flags duplicates.")
                    if id_a:
                        rejected_ids.add(id_a)
                    if id_b:
                        rejected_ids.add(id_b)
                for a in ing_a:
                    for b in ing_b:
                        rule = self._conflict_rule(a, b)
                        if rule:
                            reasons.append(
                                f"{rule['rule_id']} warning: {a} + {b} across {name_a} and {name_b}. "
                                f"{rule['description']}"
                            )
                            if id_a:
                                rejected_ids.add(id_a)
                            if id_b:
                                rejected_ids.add(id_b)
        checks.append({"check": "ingredient_rules", "passed": not any("warning:" in r or "Repeated active" in r for r in reasons)})

        # Explainable, product-level audit rows for the UI and evaluation report.
        audit = []
        checks_by_product = {}
        for check in checks:
            pid = check.get("product_id")
            if pid:
                checks_by_product.setdefault(pid, []).append(check)
        for product in plan:
            pid = product.get("product_id")
            rows = checks_by_product.get(pid, [])
            audit.append({"product_id": pid, "name": product.get("name"), "category": product.get("category"),
                          "price_inr": product.get("price_inr"), "source_ids": product.get("source_ids", []),
                          "passed": all(row.get("passed", True) for row in rows),
                          "checks": rows,
                          "decision": "PASS" if all(row.get("passed", True) for row in rows) else "REVIEW / REPLACE"})

        result = {
            "approved": not reasons,
            "reasons": list(dict.fromkeys(reasons)),
            "rejected_product_ids": sorted(rejected_ids),
            "total_cost_inr": total,
            "budget_inr": budget,
            "checks": checks,
            "product_audit": audit,
            "check_summary": {"total": len(checks), "passed": sum(bool(c.get("passed")) for c in checks),
                              "failed": sum(not bool(c.get("passed")) for c in checks)}
        }
        state["safety_result"] = result
        return result

class RoutineAgent:
    """Input contract: approved plan + validation + retrieved snippets. Output: AM/PM steps with explanations and citations."""
    name = "Routine Agent"

    def __init__(self):
        self.knowledge = json.loads((DATA_DIR / "knowledge_base.json").read_text(encoding="utf-8"))
        self.knowledge_by_id = {item["id"]: item for item in self.knowledge}

    def _best_source(self, product):
        candidates = [sid for sid in product.get("source_ids", []) if sid in self.knowledge_by_id]
        category = product.get("category")
        preferred = {
            "Cleanser": ["KB-01", "KB-02", "KB-03", "KB-04", "KB-14"],
            "Serum": ["KB-05", "KB-06", "KB-07", "KB-08", "KB-09", "KB-10", "KB-11", "KB-15", "KB-17", "KB-18"],
            "Moisturizer": ["KB-03", "KB-04", "KB-12", "KB-14"],
            "Sunscreen": ["KB-13", "KB-17", "KB-01"]
        }.get(category, [])
        return next((sid for sid in preferred if sid in candidates), candidates[0] if candidates else None)

    def _explanation(self, product, source_id):
        category = product.get("category")
        source = self.knowledge_by_id.get(source_id, {})
        templates = {
            "Cleanser": "Use a gentle cleanser to clean the skin without harsh scrubbing.",
            "Serum": f"Consider this treatment step gradually; {source.get('text', 'individual tolerance varies')}",
            "Moisturizer": "Apply moisturizer to help maintain skin comfort and reduce dryness.",
            "Sunscreen": "Use broad-spectrum SPF 30 or higher during the day and follow the label for reapplication."
        }
        return templates.get(category, "Follow the product label and stop if irritation develops.")

    def generate(self, plan, safety_result, research_results):
        if not safety_result.get("approved"):
            return None
        by_category = {p["category"]: p for p in plan}
        def step(category, time_of_day, order):
            p = by_category.get(category)
            if not p:
                return None
            source_id = self._best_source(p)
            explanation = self._explanation(p, source_id)
            return {
                "step": order,
                "time_of_day": time_of_day,
                "category": category,
                "product_id": p["product_id"],
                "name": p["name"],
                "price_inr": p["price_inr"],
                "ingredients": p["ingredients"],
                "source_ids": [source_id] if source_id else [],
                "explanation": explanation + (f" [{source_id}]" if source_id else ""),
                "source_name": self.knowledge_by_id.get(source_id, {}).get("source_name", "") if source_id else "",
                "source_url": self.knowledge_by_id.get(source_id, {}).get("source_url", "") if source_id else ""
            }
        am = [step("Cleanser", "AM", 1), step("Moisturizer", "AM", 2), step("Sunscreen", "AM", 3)]
        pm = [step("Cleanser", "PM", 1), step("Serum", "PM", 2), step("Moisturizer", "PM", 3)]
        return {
            "AM": [x for x in am if x],
            "PM": [x for x in pm if x],
            "research_sources": research_results,
            "disclaimer": "Educational demo only, not medical advice. Products are synthetic examples. Check real product labels and consult a qualified dermatologist for persistent, severe, painful, scarring, or rapidly worsening concerns."
        }
