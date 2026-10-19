"""SkinSage Streamlit frontend: real agent workflow, explainable safety and interactive planning."""
import html
import streamlit as st
import pandas as pd
from agents import ProductAgent, ResearchAgent
from orchestrator import OrchestratorAgent
from evaluation import evaluate_retrieval, evaluate_system

st.set_page_config(page_title="SkinSage | Skincare Intelligence Studio", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

# ---------------- Design system ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--ink:#23372f;--muted:#718078;--green:#244f43;--green2:#477966;--mint:#e8f2e9;--cream:#fbf9f3;--line:#e2e9e1;--peach:#f6e8df;}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:#f7f8f4}.block-container{max-width:1440px;padding-top:1.2rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#f0f4ed;border-right:1px solid var(--line)}
h1,h2,h3{font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;color:var(--ink)}
h1{font-weight:800!important}.stCaption,small{color:var(--muted)}
.stButton>button,.stFormSubmitButton>button{border-radius:12px;border:1px solid var(--green);background:var(--green);color:white;font-weight:700;padding:.65rem 1rem;min-height:2.65rem;transition:all .15s}
.stButton>button:hover,.stFormSubmitButton>button:hover{background:var(--green2);border-color:var(--green2);color:white;transform:translateY(-1px)}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);padding:15px 17px;border-radius:17px;box-shadow:0 3px 14px #1e3c2d08}
[data-testid="stMetricLabel"]{color:var(--muted);font-weight:600}[data-testid="stMetricValue"]{color:var(--green);font-family:'Manrope',sans-serif}
div[data-testid="stExpander"]{background:white;border:1px solid var(--line);border-radius:14px}
div[data-testid="stAlert"]{border-radius:13px}.stTabs [data-baseweb="tab-list"]{gap:8px}
.stTabs [data-baseweb="tab"]{padding:10px 14px;font-weight:700}
.hero{background:linear-gradient(115deg,#e4f0e6 0%,#f8f5e9 60%,#f7e9e1 100%);border:1px solid #e0e8dc;border-radius:25px;padding:30px 32px;margin-bottom:18px;position:relative;overflow:hidden}
.eyebrow,.kicker{color:#5e806c;text-transform:uppercase;letter-spacing:.15em;font-size:.72rem;font-weight:800}
.hero-title{font-family:'Manrope',sans-serif;font-size:clamp(2.1rem,4vw,3.35rem);line-height:1.04;letter-spacing:-.055em;font-weight:800;color:#244f43;margin:9px 0 12px}
.hero-copy{max-width:760px;color:#52645a;line-height:1.65;font-size:1rem}.pill{display:inline-block;background:#ffffffb8;border:1px solid #244f431b;border-radius:999px;padding:7px 11px;margin:8px 6px 0 0;font-size:.76rem;font-weight:700;color:#355d4c}
.panel{background:white;border:1px solid var(--line);border-radius:17px;padding:17px 19px;margin-bottom:12px;box-shadow:0 3px 15px #25453305}
.panel-title{font-family:'Manrope',sans-serif;color:var(--green);font-weight:800;font-size:1rem;margin-bottom:5px}.panel-copy{color:#68796f;font-size:.88rem;line-height:1.55}
.product-card{background:white;border:1px solid var(--line);border-radius:17px;padding:16px;margin:8px 0 12px;box-shadow:0 4px 15px #25453306}
.product-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.product-category{color:#638171;text-transform:uppercase;font-size:.67rem;letter-spacing:.12em;font-weight:800}
.product-name{color:var(--green);font-family:'Manrope',sans-serif;font-size:1rem;font-weight:800;margin:5px 0}.price-tag{white-space:nowrap;color:var(--green);background:var(--mint);border-radius:10px;padding:7px 9px;font-weight:800}
.chip{display:inline-block;background:#f1f5ef;color:#526a5d;padding:5px 8px;border-radius:8px;margin:3px 4px 0 0;font-size:.73rem}
.step-card{border-left:3px solid #b5d3bf;padding:4px 0 4px 13px;margin:12px 0}.step-label{color:#789083;text-transform:uppercase;letter-spacing:.1em;font-size:.67rem;font-weight:800}.step-text{color:#344d40;font-weight:700;margin-top:2px}
.agent-card{background:#fff;border:1px solid var(--line);border-radius:15px;padding:14px 15px;margin:8px 0}.agent-row{display:flex;justify-content:space-between;gap:12px;align-items:center}.badge{display:inline-block;border-radius:999px;padding:4px 8px;font-size:.7rem;font-weight:800;background:#edf1ed;color:#5d6e63}.badge.done{background:#e4f3e7;color:#286342}.badge.warn{background:#fff0d9;color:#885c13}.badge.block{background:#fbe8e6;color:#9c3730}.footer{text-align:center;color:#829087;font-size:.76rem;padding-top:25px}
[data-testid="stRadio"] label{font-weight:600}
@media(max-width:800px){.hero{padding:23px}.hero-title{font-size:2.2rem}.block-container{padding-left:1rem;padding-right:1rem}}
/* Keep the page content clear of the Streamlit Cloud toolbar */
[data-testid="stAppViewContainer"] .main {
    padding-top: 0 !important;
    overflow: visible !important;
}

/* Add space before the first content block */
[data-testid="stAppViewBlockContainer"] {
    padding-top: 6rem !important;
    overflow: visible !important;
}

/* Prevent headings from being clipped by their own containers */
[data-testid="stAppViewBlockContainer"] h1,
[data-testid="stAppViewBlockContainer"] h2,
[data-testid="stAppViewBlockContainer"] h3 {
    overflow: visible !important;
    scroll-margin-top: 6rem;
}
</style>
""", unsafe_allow_html=True)

SKIN_TYPES = ["oily", "dry", "combination", "normal", "sensitive"]
CONCERNS = ["acne", "dryness", "pigmentation", "dullness", "sensitivity", "severe acne", "painful acne", "scarring acne", "persistent rash", "severe irritation", "rapidly worsening skin condition"]
PREFERENCES = ["balanced fit", "lowest price", "fewer active ingredients"]
AVOID_OPTIONS = ["fragrance", "niacinamide", "salicylic acid", "retinol", "glycolic acid", "benzoyl peroxide", "vitamin c", "hyaluronic acid", "glycerin", "ceramides"]

# ---------------- Helpers ----------------
def esc(value):
    return html.escape(str(value if value is not None else ""))

def parse_current_products(raw):
    terms = [x.strip().lower() for x in raw.split(",") if x.strip()]
    return ([{"name": "User-entered current product", "ingredients": terms}] if terms else [])

def profile_from_form(skin, concern, budget, preference, allergies, current):
    terms = [x.strip().lower() for x in current.split(",") if x.strip()]
    return {"skin_type": skin, "concern": concern, "budget_inr": int(budget), "routine_preference": preference,
            "allergies": allergies, "current_products": parse_current_products(current), "current_ingredient_names": terms}

def badge(status):
    text = str(status).lower()
    cls = "done" if any(x in text for x in ["completed", "approved", "passed"]) else "warn" if any(x in text for x in ["running", "replanning", "revision", "rejected"]) else "block" if any(x in text for x in ["blocked", "skipped", "failed"]) else ""
    return f'<span class="badge {cls}">{esc(status).upper()}</span>'

def render_product_card(p, idx=None, explanation=None):
    ingredients = p.get("ingredients", [])
    chips = "".join(f'<span class="chip">{esc(i)}</span>' for i in ingredients)
    source_ids = p.get("source_ids", [])
    step_num = f"STEP {idx:02d} · " if idx is not None else ""
    reason = explanation if explanation is not None else p.get("explanation", "Selected from the synthetic catalogue using profile fit, budget and planning preference.")
    st.markdown(f'''<div class="product-card"><div class="product-top"><div><div class="product-category">{esc(step_num + p.get("category", "Product"))} · {esc(p.get("product_id", ""))}</div><div class="product-name">{esc(p.get("name", "Unnamed product"))}</div></div><div class="price-tag">₹{int(p.get("price_inr",0))}</div></div><div style="margin-top:8px">{chips}</div><div class="panel-copy" style="margin-top:10px">{esc(reason)}</div><div class="small-muted" style="font-size:.76rem;margin-top:8px">Knowledge IDs: {esc(', '.join(source_ids) if source_ids else 'Not mapped')}</div></div>''', unsafe_allow_html=True)

def render_workflow(result, event_mode=False):
    events = result.get("workflow_events", []) if result else []
    statuses = result.get("agent_status", {}) if result else {}
    descriptions = {
        "Orchestrator": "Plans tasks, manages shared state and decides whether to replan or stop.",
        "Research Agent": "Retrieves local knowledge snippets with IDs and TF-IDF relevance scores.",
        "Product Agent": "Ranks eligible synthetic products against profile, preference and budget constraints.",
        "Safety Agent": "Checks budget, required categories, source mapping, avoid-list entries and configured ingredient rules.",
        "Routine Agent": "Generates AM/PM steps only after safety approval."
    }
    order = ["Orchestrator", "Research Agent", "Product Agent", "Safety Agent", "Routine Agent"]
    latest = {}
    for ev in events:
        latest[ev.get("agent")] = ev
    for agent in order:
        event = latest.get(agent, {})
        status = statuses.get(agent, event.get("status", "waiting"))
        message = event.get("message", descriptions[agent])
        st.markdown(f'<div class="agent-card"><div class="agent-row"><strong>{esc(agent)}</strong>{badge(status)}</div><div class="panel-copy" style="margin-top:7px">{esc(message or descriptions[agent])}</div><div class="small-muted" style="font-size:.76rem;margin-top:5px">{esc(descriptions[agent])}</div></div>', unsafe_allow_html=True)

def friendly_stage(agent, status, message):
    """Translate internal agent events into user-facing progress language."""
    agent = str(agent or "").lower()
    status = str(status or "").lower()
    if "research" in agent:
        return ("Finding relevant skincare information", "Looking up guidance relevant to your profile.")
    if "product" in agent:
        if "running" in status:
            return ("Finding suitable products", "Comparing available options against your preferences and budget.")
        return ("Product options reviewed", "Eligible options have been evaluated.")
    if "safety" in agent:
        if any(x in status for x in ["rejected", "failed", "blocked"]):
            return ("Reviewing your routine", "A configured check needs attention; the plan may be adjusted.")
        return ("Checking your routine", "Checking budget, preferences, ingredients, and available knowledge references.")
    if "orchestrator" in agent:
        if "replan" in status:
            return ("Adjusting your plan", "The system is using validation feedback to look for a better-fitting selection.")
        if "blocked" in status:
            return ("Additional care may be needed", "This concern is outside the prototype's routine-planning scope.")
        return ("Coordinating your plan", "Keeping the planning steps in the right order.")
    if "routine" in agent:
        if "blocked" in status:
            return ("Routine not generated", "A routine is only provided when the configured validation gate approves it.")
        return ("Preparing your routine", "Organising the approved selection into morning and evening steps.")
    return ("Working on your plan", "Processing your preferences.")

def render_user_progress(events, completed=False):
    """Compact progress tracker that avoids internal agent names by default."""
    stages = ["Finding relevant information", "Selecting suitable products", "Checking safety", "Preparing your routine"]
    latest = {}
    for ev in events or []:
        title, _ = friendly_stage(ev.get("agent"), ev.get("status"), ev.get("message"))
        latest[title] = ev
    cols = st.columns(4)
    stage_map = [
        ("Finding relevant information", ["Research Agent"]),
        ("Selecting suitable products", ["Product Agent"]),
        ("Checking safety", ["Safety Agent"]),
        ("Preparing your routine", ["Routine Agent"]),
    ]
    events_by_agent = {}
    for ev in events or []:
        events_by_agent[ev.get("agent", "")] = ev
    for col, (label, agents) in zip(cols, stage_map):
        ev = next((events_by_agent.get(a) for a in agents if events_by_agent.get(a)), None)
        status = str((ev or {}).get("status", "waiting")).lower()
        if any(x in status for x in ["completed", "approved"]): icon, state = "✓", "Complete"
        elif any(x in status for x in ["running", "replanning"]): icon, state = "↻", "In progress"
        elif any(x in status for x in ["blocked", "rejected", "failed"]): icon, state = "!", "Needs review"
        elif completed: icon, state = "–", "Not required"
        else: icon, state = "○", "Upcoming"
        with col:
            st.markdown(f'<div class="panel"><div class="kicker">{icon} {esc(state)}</div><div class="panel-title" style="font-size:.9rem">{esc(label)}</div></div>', unsafe_allow_html=True)

def render_technical_insights(result, key="technical_insights"):
    """Inline, opt-in technical observability for the current run (not a separate mode/page)."""
    if not result:
        return
    with st.expander("⚙ Technical insights · agent workflow, decisions and validation", expanded=True):
        st.caption("These details come from the same execution that produced the visible result. They are not a separate or simulated workflow.")
        render_workflow(result)
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("### Execution timeline")
            events = result.get("workflow_events", [])
            if events:
                for i, ev in enumerate(events, 1):
                    st.markdown(f'<div class="step-card"><div class="step-label">EVENT {i:02d} · {esc(ev.get("agent"))} {badge(ev.get("status"))}</div><div class="step-text">{esc(ev.get("message"))}</div></div>', unsafe_allow_html=True)
            else:
                st.info("No detailed event callbacks were recorded for this run.")
        with right:
            st.markdown("### Planner decisions")
            for dec in result.get("planner_decisions", []):
                st.markdown(f'<div class="panel"><div class="kicker">{esc(dec.get("action"))}</div><div class="panel-copy">{esc(dec.get("reason"))}</div></div>', unsafe_allow_html=True)
            st.markdown("### Validation attempts")
            render_attempt_comparison(result)
        with st.expander("Inspect agent input/output contracts"):
            st.json(result.get("agent_outputs", {}))
        with st.expander("Inspect workflow state summary"):
            st.json({"agent_status": result.get("agent_status", {}), "rejected_product_ids": result.get("rejected_product_ids", []), "retry_count": result.get("retry_count", 0), "safety_approved": bool((result.get("safety_result") or {}).get("approved")), "routine_generated": bool(result.get("final_routine"))})

def run_with_live_ui(profile, slot, show_technical=False):
    """Render real orchestrator callbacks as friendly progress, with opt-in technical detail inline."""
    live_events = []
    def on_event(event, state):
        live_events.append(event)
        with slot.container():
            st.markdown("#### Your routine is taking shape")
            st.caption("Progress updates are connected to the planning workflow.")
            render_user_progress(live_events)
            latest_title, latest_copy = friendly_stage(event.get("agent"), event.get("status"), event.get("message"))
            st.info(f"**{latest_title}.** {latest_copy}")
            if show_technical:
                with st.expander("Technical execution details", expanded=True):
                    for i, ev in enumerate(live_events, 1):
                        st.markdown(f'<div class="step-card"><div class="step-label">EVENT {i:02d} · {esc(ev.get("agent"))} {badge(ev.get("status"))}</div><div class="step-text">{esc(ev.get("message"))}</div></div>', unsafe_allow_html=True)
    return OrchestratorAgent().run(profile, event_callback=on_event)

def render_routine(result):
    routine = result.get("final_routine") or {}
    left, right = st.columns(2, gap="large")
    for col, key, title, sub in [(left,"AM","☀️ Morning routine","Daytime steps generated from the approved candidate set."),(right,"PM","🌙 Evening routine","Keep the routine gradual; follow product labels.")]:
        with col:
            st.markdown(f"### {title}")
            st.caption(sub)
            steps = [x for x in routine.get(key, []) if x]
            if not steps:
                st.info("No steps were generated for this period.")
            for i, step in enumerate(steps, 1):
                render_product_card(step, i, step.get("explanation"))
    st.caption(routine.get("disclaimer", "Educational prototype only; not medical advice."))

def render_safety(result):
    safety = result.get("safety_result") or {}
    if not safety:
        st.info("Safety audit appears after a plan has been generated.")
        return
    summary = safety.get("check_summary", {})
    a,b,c,d = st.columns(4)
    a.metric("Audit checks", summary.get("total", len(safety.get("checks",[]))))
    b.metric("Passed", summary.get("passed", 0))
    c.metric("Failed", summary.get("failed", 0))
    d.metric("Plan status", "APPROVED" if safety.get("approved") else "NOT APPROVED")
    for check in safety.get("checks", []):
        passed = bool(check.get("passed"))
        label = str(check.get("check", "check")).replace("_", " ").title()
        with st.expander(f"{'✅' if passed else '⚠️'} {label} · {'Passed' if passed else 'Needs review'}" + (f" · {check.get('product_id')}" if check.get("product_id") else "")):
            st.write({k:v for k,v in check.items() if k not in {"check", "passed"}} or "No additional details.")
    st.markdown("#### Product-level audit")
    audits = safety.get("product_audit", [])
    if audits:
        rows=[]
        for row in audits:
            rows.append({"Product ID":row.get("product_id"),"Product":row.get("name"),"Category":row.get("category"),"Price (₹)":row.get("price_inr"),"Decision":row.get("decision"),"Source IDs":", ".join(row.get("source_ids",[]))})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if safety.get("reasons"):
        st.markdown("#### Validation feedback")
        for reason in safety["reasons"]:
            st.warning(reason)
    if safety.get("approved"):
        st.success("All configured prototype checks passed. This is a rule-based software check, not a clinical safety certification.")
    else:
        st.error("The current candidate plan was not approved. The routine is withheld unless the orchestrator finds an approved replacement plan.")

def render_attempt_comparison(result):
    attempts = result.get("attempt_history", [])
    if not attempts:
        st.info("No product validation attempt has been recorded yet.")
        return
    rows=[]
    for a in attempts:
        rows.append({"Attempt":a.get("attempt"),"Products":", ".join(a.get("product_ids",[])),"Total (₹)":a.get("total_cost_inr"),"Safety": "Approved" if a.get("approved") else "Rejected","Rejected IDs":", ".join(a.get("rejected_product_ids",[])),"Feedback":"; ".join(a.get("reasons",[]))})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if len(attempts)>1:
        st.success(f"The planner executed {len(attempts)} validation attempts and used feedback between attempts.")
    else:
        st.caption("One attempt was sufficient for this profile; the feedback loop remains available when a rejection occurs.")

# ---------------- Sidebar and profile wizard ----------------
with st.sidebar:
    st.markdown("# ✦ SkinSage")
    st.caption("SKINCARE INTELLIGENCE STUDIO")
    st.toggle("⚙ View technical insights", value=False, key="skinsage_show_technical", help="Optional: reveal the real agent timeline, planner decisions, validation attempts, and agent outputs inline. This does not change how the system runs.")
    st.caption("Off by default · User-friendly experience")
    st.markdown("---")
    st.markdown("### 01 · Your profile")
    existing = st.session_state.get("skinsage_profile", {})
    with st.form("profile_wizard", clear_on_submit=False):
        skin_type = st.selectbox("Skin type", SKIN_TYPES, index=SKIN_TYPES.index(existing.get("skin_type", "combination")) if existing.get("skin_type", "combination") in SKIN_TYPES else 2)
        concern = st.selectbox("Primary concern", CONCERNS, index=CONCERNS.index(existing.get("concern", "acne")) if existing.get("concern", "acne") in CONCERNS else 0)
        budget = st.slider("Routine budget", 300, 3500, int(existing.get("budget_inr",1500)), 100, format="₹%d")
        pref = st.selectbox("Planning preference", PREFERENCES, index=PREFERENCES.index(existing.get("routine_preference","balanced fit")) if existing.get("routine_preference","balanced fit") in PREFERENCES else 0, help="Ranking preference only. Safety checks remain a hard constraint.")
        allergies = st.multiselect("Ingredients to avoid", AVOID_OPTIONS, default=[x for x in existing.get("allergies",[]) if x in AVOID_OPTIONS])
        current_text = st.text_input("Current active ingredients", value=", ".join(existing.get("current_ingredient_names",[])), placeholder="e.g. salicylic acid, retinol")
        submitted = st.form_submit_button("✦ Generate / Replan", use_container_width=True)
    st.markdown("---")
    st.markdown("**Workflow**")
    st.markdown("Research → Select → Validate → Replan if needed → Generate")
    st.caption("Local TF-IDF retrieval · Synthetic product catalogue · No paid API")
    st.caption("Educational prototype · Not medical advice")

# Run actual agent workflow on submit, with callback-driven live execution in the page area.
# Save the submitted profile and schedule the workflow to run
# after the hero, navigation, and scope note have been rendered.
if submitted:
    new_profile = profile_from_form(
        skin_type, concern, budget, pref, allergies, current_text
    )
    st.session_state["skinsage_profile"] = new_profile
    st.session_state.pop("skinsage_whatif", None)
    st.session_state["skinsage_run_pending"] = True

result = st.session_state.get("skinsage_result")
profile = st.session_state.get("skinsage_profile")

# ---------------- Header and navigation ----------------
st.markdown('''<div class="hero"><div class="eyebrow">Personal care · Multi-agent AI · Explainable planning</div><div class="hero-title">Your routine, thoughtfully<br>put together.</div><div class="hero-copy">Build a routine around your preferences, compare suitable options, and review clear safety guidance. Curious about how the system works? Turn on Technical Insights whenever you want to explore the details.</div><span class="pill">✦ Source-aware research</span><span class="pill">◈ Safety as a hard gate</span><span class="pill">⌁ Feedback-driven replanning</span></div>''', unsafe_allow_html=True)

pages = ["Home", "My Skin Profile", "Routine Planner", "Safety & Comparison", "Research Explorer", "What-if Simulator", "Evaluation Centre"]
if "skinsage_page" not in st.session_state: st.session_state["skinsage_page"] = "Home"
if st.session_state.get("skinsage_page") == "Agent Control Centre":
    st.session_state["skinsage_page"] = "Home"
selected_page = st.radio("Navigation", pages, horizontal=True, label_visibility="collapsed", key="skinsage_page")
technical_on = bool(st.session_state.get("skinsage_show_technical", False))
st.markdown("<div class='panel' style='background:#fffdf8;border-color:#eee6d8'><div class='panel-title'>A note on scope</div><div class='panel-copy'>SkinSage is an educational prototype, not medical advice. Product names and prices are synthetic. It does not diagnose skin conditions. High-risk concerns trigger a referral gate, and configured ingredient-pair warnings are conservative demo rules rather than universal contraindications.</div></div>", unsafe_allow_html=True)

# Execute the workflow below the hero and navigation
if st.session_state.pop("skinsage_run_pending", False):
    new_profile = st.session_state["skinsage_profile"]

    with st.spinner("Executing the multi-agent workflow..."):
        live_slot = st.empty()
        new_result = run_with_live_ui(
            new_profile,
            live_slot,
            st.session_state.get("skinsage_show_technical", False),
        )

    st.session_state["skinsage_result"] = new_result
    st.session_state["skinsage_last_run"] = new_profile.copy()

# Refresh values after the workflow finishes
result = st.session_state.get("skinsage_result")
profile = st.session_state.get("skinsage_profile")

# ---------------- Pages ----------------
if selected_page == "Home":
    st.markdown("## Your planning overview")
    if not result:
        st.info("Complete your profile in the sidebar and choose **Generate / Replan** to build your routine.")
        cols=st.columns(3)
        cards=[("01 · Understand","Start with your preferences","Your skin type, concern, budget, and preferences guide the plan."),("02 · Review","Check the options","Products are checked against the constraints configured in this prototype."),("03 · Refine","Adjust when needed","If validation rejects a selection, the planner can try an alternative.")]
        for col,(k,t,d) in zip(cols,cards):
            with col: st.markdown(f'<div class="panel"><div class="kicker">{k}</div><div class="panel-title">{t}</div><div class="panel-copy">{d}</div></div>',unsafe_allow_html=True)
    elif result.get("referral_required"):
        st.error(result.get("referral_message", "This concern is outside the prototype's scope."))
        st.markdown("#### Why no routine was generated")
        st.write("The referral gate takes priority over product selection. Routine generation is blocked for this concern.")
        render_user_progress(result.get("workflow_events", []), completed=True)
        if technical_on: render_technical_insights(result, "home_referral_technical")
    elif result.get("final_routine"):
        safety=result.get("safety_result",{}); total=int(safety.get("total_cost_inr",0)); budget_value=int((profile or {}).get("budget_inr",0))
        a,b,c,d=st.columns(4)
        a.metric("Products selected",len({p.get("product_id") for p in result.get("candidate_products",[])}))
        b.metric("Estimated total",f"₹{total}")
        c.metric("Budget remaining",f"₹{max(0,budget_value-total)}")
        d.metric("Planning passes",len(result.get("attempt_history",[])))
        st.success("Your routine is ready after passing the configured validation checks.")
        st.markdown("### Your plan at a glance")
        st.write(f"Profile: **{esc((profile or {}).get('skin_type',''))} skin** · Concern: **{esc((profile or {}).get('concern',''))}** · Preference: **{esc((profile or {}).get('routine_preference','balanced fit'))}**")
        st.markdown("### Planning progress")
        render_user_progress(result.get("workflow_events", []), completed=True)
        if technical_on: render_technical_insights(result, "home_technical")
    else:
        st.error("No approved routine is available. SkinSage withheld the routine rather than bypassing validation.")
        for reason in result.get("rejection_reasons",[]): st.warning(reason)
        render_user_progress(result.get("workflow_events", []), completed=True)
        if technical_on: render_technical_insights(result, "home_technical_blocked")

elif selected_page == "My Skin Profile":
    st.markdown("## My Skin Profile")
    st.caption("This summary reflects the profile used by the most recent run. Edit values in the sidebar and choose Generate / Replan to execute the agents again.")
    if not profile:
        st.info("No profile saved yet. Use the sidebar profile wizard.")
    else:
        cols=st.columns(3)
        cols[0].metric("Skin type",str(profile.get("skin_type","—")).title())
        cols[1].metric("Budget",f"₹{profile.get('budget_inr',0)}")
        cols[2].metric("Preference",str(profile.get("routine_preference","balanced fit")).title())
        st.markdown("### Profile details")
        st.dataframe(pd.DataFrame([{"Attribute":"Primary concern","Value":profile.get("concern")},{"Attribute":"Ingredients to avoid","Value":", ".join(profile.get("allergies",[])) or "None entered"},{"Attribute":"Current active ingredients","Value":", ".join(profile.get("current_ingredient_names",[])) or "None entered"}]), use_container_width=True, hide_index=True)
        st.info("Profile values are used as planning inputs. They are not a diagnosis or a medical record.")

elif selected_page == "Routine Planner":
    st.markdown("## Routine Planner")
    if result and result.get("final_routine"):
        routine=result["final_routine"]; safety=result.get("safety_result",{}); total=int(safety.get("total_cost_inr",0)); budget_value=int((profile or {}).get("budget_inr",0))
        a,b,c,d=st.columns(4); a.metric("Total cost",f"₹{total}"); b.metric("Budget remaining",f"₹{max(0,budget_value-total)}"); c.metric("Steps",sum(len([x for x in routine.get(k,[]) if x]) for k in ["AM","PM"])); d.metric("Source IDs",sum(bool(x.get("source_ids")) for k in ["AM","PM"] for x in routine.get(k,[]) if x))
        st.success("Your routine passed the configured validation checks.")
        render_user_progress(result.get("workflow_events", []), completed=True)
        render_routine(result)
        with st.expander("View product details"):
            st.dataframe(pd.DataFrame([{"Product":p.get("name"),"Category":p.get("category"),"Price (₹)":p.get("price_inr"),"Key ingredients":", ".join(p.get("ingredients",[]))} for p in result.get("candidate_products",[])]),use_container_width=True,hide_index=True)
        if technical_on: render_technical_insights(result, "routine_technical")
    elif result and result.get("referral_required"):
        st.error("Routine generation blocked by the referral gate."); st.write(result.get("referral_message"))
    else: st.info("Generate a plan from the sidebar to see the approved AM/PM routine here.")

elif selected_page == "Safety & Comparison":
    st.markdown("## Safety audit & candidate comparison")
    if not result: st.info("Generate a routine to see its safety summary and any required adjustments.")
    else:
        safety = result.get("safety_result") or {}
        if result.get("referral_required"):
            st.warning(result.get("referral_message", "Please consult a qualified dermatologist."))
        elif safety:
            if safety.get("approved"):
                st.success("The current selection passed the prototype's configured checks. This is not a clinical safety certification.")
            else:
                st.error("The current selection was not approved. SkinSage withholds the routine unless a revised selection passes validation.")
            st.metric("Estimated total", f"₹{safety.get('total_cost_inr', 0)}")
            for reason in safety.get("reasons", []): st.warning(reason)
        if technical_on:
            st.markdown("### Detailed validation audit")
            render_safety(result)
            st.markdown("### Before-and-after replanning")
            render_attempt_comparison(result)
            st.markdown("### Candidate ranking")
            candidates=result.get("routine_comparison",[])
            if candidates:
                df=pd.DataFrame([{"Selected": "✓" if x.get("selected") else "Alternative","Product ID":x.get("product_id"),"Product":x.get("name"),"Price (₹)":x.get("price_inr"),"Heuristic score":x.get("score"),"Score basis":x.get("score_basis")} for x in candidates])
                st.dataframe(df,use_container_width=True,hide_index=True)
                st.caption("Ranking is heuristic and preference-aware. A ranking score is not a clinical efficacy score and never overrides a failed safety gate.")
            else: st.caption("No comparison candidates were recorded for this run.")
        else:
            st.caption("Turn on **View technical insights** in the sidebar to inspect detailed checks, rejected product IDs, and replanning history.")

elif selected_page == "Research Explorer":
    st.markdown("## Research Explorer")
    st.caption("Browse the local research library and see the knowledge entries retrieved for the active profile.")
    try:
        kb=__import__("json").loads((__import__("pathlib").Path(__file__).resolve().parent/"data"/"knowledge_base.json").read_text(encoding="utf-8"))
    except Exception: kb=[]
    search=st.text_input("Search topics, ingredients, or phrases",placeholder="e.g. sunscreen, sensitive skin, retinol")
    retrieved_ids={x.get("id") for x in (result or {}).get("retrieved_sources",[])}
    filtered=[x for x in kb if not search or search.lower() in (x.get("topic","")+" "+x.get("text","")+" "+" ".join(x.get("tags",[]))).lower()]
    st.write(f"Showing **{len(filtered)}** of **{len(kb)}** local knowledge entries.")
    for item in filtered:
        is_retrieved=item.get("id") in retrieved_ids
        with st.expander(f"{'✦ Retrieved for this profile · ' if is_retrieved else ''}{item.get('id')} — {item.get('topic')}"):
            st.write(item.get("text"))
            st.caption("Tags: "+", ".join(item.get("tags",[])))
            st.caption("Source: "+str(item.get("source_name","Local knowledge base")))
            if item.get("source_url"):
                st.link_button("Open referenced source",item["source_url"])
            if is_retrieved and technical_on:
                hit=next((x for x in result.get("retrieved_sources",[]) if x.get("id")==item.get("id")),{})
                st.metric("Retrieval relevance score",f"{hit.get('score',0):.3f}")
    st.warning("A knowledge ID establishes traceability to this local entry; it does not independently prove that every claim is authoritative or clinically verified.")

elif selected_page == "What-if Simulator":
    st.markdown("## What if my preferences change?")
    st.caption("This runs the same orchestrator with a modified profile and compares actual outputs with your current run.")
    base=profile or {"skin_type":"combination","concern":"acne","budget_inr":1500,"routine_preference":"balanced fit","allergies":[],"current_ingredient_names":[]}
    with st.form("whatif_form"):
        x1,x2=st.columns(2)
        with x1:
            wf_skin=st.selectbox("Skin type",SKIN_TYPES,index=SKIN_TYPES.index(base.get("skin_type","combination")) if base.get("skin_type","combination") in SKIN_TYPES else 2)
            wf_concern=st.selectbox("Primary concern",CONCERNS,index=CONCERNS.index(base.get("concern","acne")) if base.get("concern","acne") in CONCERNS else 0)
            wf_budget=st.slider("Budget (₹)",300,3500,int(base.get("budget_inr",1500)),100)
        with x2:
            wf_pref=st.selectbox("Planning preference",PREFERENCES,index=PREFERENCES.index(base.get("routine_preference","balanced fit")) if base.get("routine_preference","balanced fit") in PREFERENCES else 0)
            wf_allergies=st.multiselect("Ingredients to avoid",AVOID_OPTIONS,default=[x for x in base.get("allergies",[]) if x in AVOID_OPTIONS],key="whatif_avoid")
            wf_current=st.text_input("Current active ingredients",value=", ".join(base.get("current_ingredient_names",[])),key="whatif_current")
        do_whatif=st.form_submit_button("↻ Recalculate scenario")
    if do_whatif:
        wf_profile=profile_from_form(wf_skin,wf_concern,wf_budget,wf_pref,wf_allergies,wf_current)
        with st.spinner("Executing agents for the changed scenario..."):
            live=st.empty(); wf_result=run_with_live_ui(wf_profile,live,st.session_state.get("skinsage_show_technical", False))
        st.session_state["skinsage_whatif"]=wf_result; st.session_state["skinsage_whatif_profile"]=wf_profile
    wf=st.session_state.get("skinsage_whatif")
    if wf:
        st.markdown("### Scenario result")
        if wf.get("referral_required"): st.error(wf.get("referral_message"))
        elif wf.get("final_routine"):
            s=wf.get("safety_result",{}); a,b,c=st.columns(3); a.metric("Plan status","Approved"); a2=int(s.get("total_cost_inr",0)); b.metric("Total cost",f"₹{a2}"); c.metric("Validation attempts",len(wf.get("attempt_history",[])))
            st.write("Selected products: "+", ".join(p.get("name","") for p in wf.get("candidate_products",[])))
        else:
            st.error("No routine approved; the system withheld the final plan.")
            for r in wf.get("rejection_reasons",[]): st.warning(r)
        st.markdown("### Original vs changed scenario")
        orig=result or {}; orig_ids={p.get("product_id") for p in orig.get("candidate_products",[])}; new_ids={p.get("product_id") for p in wf.get("candidate_products",[])}
        old_total=(orig.get("safety_result") or {}).get("total_cost_inr"); new_total=(wf.get("safety_result") or {}).get("total_cost_inr")
        q1,q2,q3=st.columns(3); q1.metric("Products changed",len(orig_ids.symmetric_difference(new_ids))); q2.metric("Original total",f"₹{old_total}" if old_total is not None else "—"); q3.metric("Scenario total",f"₹{new_total}" if new_total is not None else "—")
        st.write("Added: "+(", ".join(sorted(new_ids-orig_ids)) or "None")); st.write("Removed: "+(", ".join(sorted(orig_ids-new_ids)) or "None"))
        if technical_on:
            render_technical_insights(wf, "whatif_technical")
        else:
            st.caption("The scenario was run through the same planning workflow. Turn on Technical Insights to inspect its detailed decisions and event history.")
    elif not result: st.info("You can run a what-if scenario now, or create a baseline profile first for a more useful comparison.")

elif selected_page == "Evaluation Centre":
    st.markdown("## Evaluation Centre")
    if not technical_on:
        st.info("This page is intended for project evaluation. Turn on **View technical insights** in the sidebar to reveal detailed system metrics and test traces.")
    st.caption("Reproducible, local software checks. These metrics are not clinical performance measures.")
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="panel"><div class="panel-title">Retrieval benchmark</div><div class="panel-copy">A hit means at least one expected knowledge ID appears in the top three results for a hand-authored query.</div></div>',unsafe_allow_html=True)
        if st.button("Run retrieval benchmark",key="run_retrieval"):
            metrics=evaluate_retrieval(top_k=3); st.session_state["retrieval_eval"]=metrics
        metrics=st.session_state.get("retrieval_eval")
        if metrics:
            st.metric("Top-3 hit rate",f"{metrics['passed']}/{metrics['total']} · {metrics['accuracy']:.0%}")
            st.dataframe(metrics["details"],use_container_width=True,hide_index=True)
    with c2:
        st.markdown('<div class="panel"><div class="panel-title">End-to-end scenarios</div><div class="panel-copy">Runs standard, sensitive-skin, tight-budget, ingredient-avoidance, existing-active and referral scenarios.</div></div>',unsafe_allow_html=True)
        if st.button("Run full scenario suite",key="run_scenarios"):
            st.session_state["system_eval"]=evaluate_system()
        suite=st.session_state.get("system_eval")
        if suite:
            st.metric("Scenario pass rate",f"{suite['passed']}/{suite['total']} · {suite['accuracy']:.0%}")
            m1,m2=st.columns(2); m1.metric("Approved-plan safety rate",f"{suite['safety_approval_rate']:.0%}"); m2.metric("Approved-plan budget compliance",f"{suite['budget_compliance_rate']:.0%}")
            st.dataframe(suite["details"],use_container_width=True,hide_index=True)
    if st.session_state.get("retrieval_eval") and st.session_state.get("system_eval"):
        r=st.session_state["retrieval_eval"]; e=st.session_state["system_eval"]
        st.markdown("### Run summary")
        st.bar_chart(pd.DataFrame({"Metric":["Retrieval hit rate","Scenario pass rate"],"Rate":[r["accuracy"],e["accuracy"]]}).set_index("Metric"))
        st.caption("Small hand-authored benchmark; expand with held-out scenarios before making general performance claims.")

st.markdown('<div class="footer">SKINSAGE · Student-built multi-agent AI proof of concept · Synthetic product catalogue · Not medical advice</div>',unsafe_allow_html=True)
