"""
OfferWise Expert System — Streamlit Application
Grey-themed UI: sidebar navigation, score cards, verdict banner,
step-by-step form. Emojis limited to tick (checkmark) and red-alert only.
"""

# Fix import path so app works from any working directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import json
from datetime import datetime

from knowledge_base import QUESTIONS, RULES, THRESHOLDS, validate_knowledge_base
from inference_engine import InferenceEngine
from analyzer import OfferAnalyzer


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OfferWise",
    page_icon="O",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ── Global CSS — Grey Theme ───────────────────────────────────────────────────
CSS = """
<style>
/* ---- Base ---- */
html, body, [class*="css"] { font-family: 'Segoe UI', system-ui, sans-serif; }

/* ---- Sidebar shell ---- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2d3748 0%, #3d4a5c 100%);
    border-right: 1px solid #4a5568;
}
/* General text in sidebar (headers, captions, labels) is light */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
    color: #e2e8f0;
}
[data-testid="stSidebar"] hr { border-color: #4a5568 !important; }

/* ---- Navigation boxes / buttons: BLACK text so it is 100% readable ---- */
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] button *,
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stSidebar"] button[kind="secondary"] *,
[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
[data-testid="stSidebar"] [data-testid="baseButton-secondary"] * {
    color: #000000 !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] button:hover,
[data-testid="stSidebar"] button:hover *,
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stButton > button:hover * {
    color: #000000 !important;
}

/* ---- Page banner ---- */
.top-banner {
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 50%, #2d3748 100%);
    border-radius: 12px;
    padding: 1.8rem 2rem 1.4rem 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
    border: 1px solid #4a5568;
}
.top-banner h1 {
    color: #f7fafc;
    font-size: 2rem;
    margin: 0;
    letter-spacing: -0.3px;
    font-weight: 700;
}
.top-banner p {
    color: #a0aec0;
    font-size: 0.92rem;
    margin: 0.35rem 0 0 0;
}

/* ---- Verdict cards ---- */
.verdict-card {
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin: 1rem 0;
    text-align: center;
    box-shadow: 0 2px 16px rgba(0,0,0,0.09);
    animation: fadeIn 0.4s ease;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: none; }
}
.verdict-high-risk    { background: #fff5f5; border-left: 5px solid #e53e3e; color: #9b2c2c; }
.verdict-investigate  { background: #fffdf0; border-left: 5px solid #d69e2e; color: #744210; }
.verdict-conditions   { background: #ebf8ff; border-left: 5px solid #3182ce; color: #2c5282; }
.verdict-strong       { background: #f0fff4; border-left: 5px solid #38a169; color: #22543d; }
.verdict-insufficient { background: #f7fafc; border-left: 5px solid #a0aec0; color: #4a5568; }
.verdict-card .vtitle  { font-size: 1.4rem; font-weight: 800; margin: 0; }
.verdict-card .vreason { font-size: 0.88rem; margin-top: 0.4rem; opacity: 0.8; }

/* ---- Score cards ---- */
.score-grid {
    display: flex;
    gap: 0.9rem;
    flex-wrap: wrap;
    justify-content: center;
    margin: 1rem 0;
}
.score-card {
    background: #f7fafc;
    border-radius: 10px;
    padding: 1.1rem 0.9rem;
    text-align: center;
    min-width: 110px;
    flex: 1;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
}
.score-card .sc-label {
    font-size: 0.7rem;
    color: #718096;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.score-card .sc-value {
    font-size: 1.9rem;
    font-weight: 800;
    margin: 0.25rem 0;
}
.score-card .sc-bar-bg {
    background: #e2e8f0;
    border-radius: 4px;
    height: 5px;
    margin-top: 0.4rem;
}
.score-card .sc-bar { height: 5px; border-radius: 4px; }

/* ---- Section headings ---- */
.section-head {
    font-size: 1rem;
    font-weight: 700;
    color: #2d3748;
    padding: 0.5rem 0;
    border-bottom: 2px solid #e2e8f0;
    margin: 1.3rem 0 0.7rem 0;
    letter-spacing: 0.01em;
    text-transform: uppercase;
}

/* ---- Rule rows ---- */
.rule-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.65rem 0;
    border-bottom: 1px solid #f0f4f8;
}
.rule-badge {
    font-size: 0.6rem;
    font-weight: 700;
    padding: 0.18rem 0.45rem;
    border-radius: 20px;
    white-space: nowrap;
    margin-top: 0.1rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.sev-critical { background: #fed7d7; color: #9b2c2c; }
.sev-high     { background: #feebc8; color: #7b341e; }
.sev-medium   { background: #fefcbf; color: #744210; }
.sev-low      { background: #c6f6d5; color: #22543d; }

/* ---- What-if comparison boxes ---- */
.wi-box {
    border-radius: 10px;
    padding: 1.1rem;
    text-align: center;
    border: 1px solid #e2e8f0;
    background: #f7fafc;
}
.wi-box .wi-label {
    font-size: 0.72rem;
    color: #718096;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.4rem;
}

/* ---- Disclaimer ---- */
.disclaimer {
    background: #f7fafc;
    border-left: 4px solid #a0aec0;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    color: #718096;
    font-size: 0.8rem;
    margin-top: 1.5rem;
    line-height: 1.6;
}

/* ---- Mobile tweaks ---- */
@media (max-width: 600px) {
    .score-grid { gap: 0.4rem; }
    .score-card { min-width: 75px; padding: 0.7rem 0.4rem; }
    .score-card .sc-value { font-size: 1.3rem; }
    .top-banner h1 { font-size: 1.5rem; }
}

/* ---- Main content width ---- */
.block-container { max-width: 760px !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def initialize_session_state():
    """Make sure all session state keys exist before first render."""
    defaults = {
        'page': 'Assess',
        'assessment_result': None,
        'user_inputs': {},
        'whatif_result': None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def run_assessment(user_facts: dict) -> dict:
    """
    Run the full expert-system pipeline.
    1. InferenceEngine does forward chaining over user facts.
    2. OfferAnalyzer converts fired rules to scores, verdict, recommendations.
    Returns combined result dict.
    """
    engine = InferenceEngine(RULES)
    inference_result = engine.run(user_facts)
    analyzer = OfferAnalyzer()
    analysis = analyzer.analyze(inference_result, user_facts)
    return {
        'analysis': analysis,
        'inference': inference_result,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


# Verdict metadata: (label_prefix, css_class, hex_color)
# Only tick (checkmark) and red-alert emojis are used here.
VERDICT_META = {
    'High Risk':                   ('🚨', 'verdict-high-risk',    '#e53e3e'),
    'Needs Further Investigation': ('--', 'verdict-investigate',  '#d69e2e'),
    'Suitable With Conditions':    ('✅', 'verdict-conditions',   '#3182ce'),
    'Strongly Suitable':           ('✅', 'verdict-strong',       '#38a169'),
    'Insufficient Information':    ('--', 'verdict-insufficient', '#a0aec0'),
}


def render_verdict_card(verdict: str, reason: str):
    """Render an animated verdict card. Only tick/alert symbols used."""
    prefix, css_cls, _ = VERDICT_META.get(verdict, ('--', 'verdict-insufficient', '#a0aec0'))
    # Show prefix only when it's an actual symbol (not the placeholder --)
    display_prefix = f"<div style='font-size:1.5rem;margin-bottom:0.3rem;'>{prefix}</div>" \
                     if prefix != '--' else ''
    st.markdown(
        f"""
        <div class="verdict-card {css_cls}">
            {display_prefix}
            <div class="vtitle">{verdict}</div>
            <div class="vreason">{reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_cards(scores: dict):
    """Render 4 score cards with inline progress bars. No emojis."""
    color_map = {
        'Compensation':       '#5a67d8',
        'Career Growth':      '#38a169',
        'Working Conditions': '#d69e2e',
        'Legitimacy':         '#3182ce',
    }
    cards_html = '<div class="score-grid">'
    for label, score in scores.items():
        color = color_map.get(label, '#718096')
        bar_color = '#38a169' if score >= 65 else ('#d69e2e' if score >= 40 else '#e53e3e')
        cards_html += f"""
        <div class="score-card">
            <div class="sc-label">{label}</div>
            <div class="sc-value" style="color:{color};">{score}</div>
            <div class="sc-bar-bg">
                <div class="sc-bar" style="width:{score}%;background:{bar_color};"></div>
            </div>
        </div>"""
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


def section_head(title: str):
    """Render a styled section heading — no emoji."""
    st.markdown(f'<div class="section-head">{title}</div>', unsafe_allow_html=True)


def render_rule_row(fired: dict):
    """Render one fired rule as a compact styled row. No emojis."""
    sev = fired['severity']
    sev_cls = {
        'Critical': 'sev-critical',
        'High':     'sev-high',
        'Medium':   'sev-medium',
        'Low':      'sev-low',
    }.get(sev, 'sev-low')
    facts_str = ', '.join(f'{k}={v}' for k, v in fired['matched_facts'].items())
    st.markdown(
        f"""
        <div class="rule-row">
            <span class="rule-badge {sev_cls}">{sev}</span>
            <div>
                <strong>{fired['rule_id']} — {fired['rule_name']}</strong><br>
                <span style="color:#4a5568;font-size:0.84rem;">{fired['explanation']}</span><br>
                <span style="color:#a0aec0;font-size:0.76rem;">Facts: {facts_str}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    """Sidebar with nav buttons and a live status strip. No emojis."""
    with st.sidebar:
        st.markdown("## OfferWise")
        st.markdown("*Rule-Based Job Offer Evaluator*")
        st.markdown("---")

        # Navigation pages — labels intentionally have no emojis
        pages = [
            ("Assess",          "Fill in your offer details"),
            ("Results",         "View your assessment"),
            ("What-If",         "Experiment with changes"),
            ("Knowledge Base",  "Browse all 50 rules"),
        ]

        for label, tip in pages:
            is_active = st.session_state.page == label
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                label,
                key=f"nav_{label}",
                use_container_width=True,
                type=btn_type,
                help=tip,
            ):
                st.session_state.page = label
                st.rerun()

        st.markdown("---")

        # Mini status strip
        if st.session_state.assessment_result:
            verdict = st.session_state.assessment_result['analysis']['verdict']
            prefix, _, color = VERDICT_META.get(verdict, ('', '', '#a0aec0'))
            # Show tick or alert only
            sym = f"{prefix} " if prefix not in ('', '--') else ''
            st.markdown(
                f"**Last Result**  \n"
                f"<span style='color:{color};font-weight:700;font-size:0.9rem;'>"
                f"{sym}{verdict}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("No assessment yet.")

        st.markdown("---")
        st.caption("IAI Lab Project — Rule-Based Expert System")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ASSESS
# ═══════════════════════════════════════════════════════════════════════════════

def page_assess():
    """Assessment form — grouped questions, no emojis in labels."""
    st.markdown(
        '<div class="top-banner">'
        '<h1>Assess Your Offer</h1>'
        '<p>Answer honestly. "Not sure" is always a valid option — it is treated as unknown.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form(key="assessment_form", border=False):

        # Group 1: Basic Details
        section_head("Basic Details")
        c1, c2 = st.columns(2)
        with c1:
            emp_type = st.selectbox(
                QUESTIONS[0]['text'], QUESTIONS[0]['options'],
                help=QUESTIONS[0]['help'], key='q_employment_type',
            )
        with c2:
            work_mode = st.selectbox(
                QUESTIONS[1]['text'], QUESTIONS[1]['options'],
                help=QUESTIONS[1]['help'], key='q_work_mode',
            )

        # Group 2: Compensation
        section_head("Compensation")
        c1, c2 = st.columns(2)
        with c1:
            monthly_pay = st.number_input(
                QUESTIONS[3]['text'], min_value=0, max_value=500_000,
                value=0, step=5_000, help=QUESTIONS[3]['help'], key='q_monthly_pay',
            )
        with c2:
            paid_on_time = st.selectbox(
                QUESTIONS[4]['text'], QUESTIONS[4]['options'],
                help=QUESTIONS[4]['help'], key='q_paid_on_time',
            )

        # Group 3: Workload and Conditions
        section_head("Workload and Conditions")
        c1, c2 = st.columns(2)
        with c1:
            weekly_hours = st.number_input(
                QUESTIONS[2]['text'], min_value=0, max_value=80,
                value=40, step=5, help=QUESTIONS[2]['help'], key='q_weekly_hours',
            )
        with c2:
            # Commute only shown for on-site / hybrid roles
            if work_mode in ['On-site', 'Hybrid']:
                commute_time = st.number_input(
                    QUESTIONS[9]['text'], min_value=0, max_value=300,
                    value=0, step=15, help=QUESTIONS[9]['help'], key='q_commute_time',
                )
            else:
                # Remote or unknown: commute is not applicable
                # Set to None so the engine treats it as unknown (no fact to match)
                commute_time = None
                st.info("Commute time is not applicable for Remote work.")

        # Group 4: Career Development
        section_head("Career Development")
        c1, c2 = st.columns(2)
        with c1:
            learning = st.selectbox(
                QUESTIONS[5]['text'], QUESTIONS[5]['options'],
                help=QUESTIONS[5]['help'], key='q_learning_opportunity',
            )
            career_rel = st.selectbox(
                QUESTIONS[7]['text'], QUESTIONS[7]['options'],
                help=QUESTIONS[7]['help'], key='q_career_relevance',
            )
        with c2:
            mentorship = st.selectbox(
                QUESTIONS[6]['text'], QUESTIONS[6]['options'],
                help=QUESTIONS[6]['help'], key='q_mentorship',
            )
            fulltime = st.selectbox(
                QUESTIONS[8]['text'], QUESTIONS[8]['options'],
                help=QUESTIONS[8]['help'], key='q_fulltime_chance',
            )

        # Group 5: Legitimacy and Red Flags
        section_head("Legitimacy and Red Flags")
        c1, c2 = st.columns(2)
        with c1:
            contract = st.selectbox(
                QUESTIONS[10]['text'], QUESTIONS[10]['options'],
                help=QUESTIONS[10]['help'], key='q_written_contract',
            )
            clear_resp = st.selectbox(
                QUESTIONS[11]['text'], QUESTIONS[11]['options'],
                help=QUESTIONS[11]['help'], key='q_clear_responsibilities',
            )
            upfront = st.selectbox(
                QUESTIONS[12]['text'], QUESTIONS[12]['options'],
                help=QUESTIONS[12]['help'], key='q_upfront_payment',
            )
        with c2:
            sensitive = st.selectbox(
                QUESTIONS[13]['text'], QUESTIONS[13]['options'],
                help=QUESTIONS[13]['help'], key='q_sensitive_docs_early',
            )
            pressure = st.selectbox(
                QUESTIONS[14]['text'], QUESTIONS[14]['options'],
                help=QUESTIONS[14]['help'], key='q_hiring_pressure',
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Submit button — no emoji in label
        submitted = st.form_submit_button(
            "Analyse Offer",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            user_inputs = {
                'employment_type':       emp_type,
                'work_mode':             work_mode,
                'weekly_hours':          weekly_hours,
                'monthly_pay':           monthly_pay,
                'paid_on_time':          paid_on_time,
                'learning_opportunity':  learning,
                'mentorship':            mentorship,
                'career_relevance':      career_rel,
                'fulltime_chance':       fulltime,
                'commute_time':          commute_time,
                'written_contract':      contract,
                'clear_responsibilities': clear_resp,
                'upfront_payment':       upfront,
                'sensitive_docs_early':  sensitive,
                'hiring_pressure':       pressure,
            }

            with st.spinner("Running expert system..."):
                st.session_state.user_inputs = user_inputs
                st.session_state.assessment_result = run_assessment(user_inputs)

            # Auto-navigate to Results after submission
            st.session_state.page = 'Results'
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

def page_results():
    """Full assessment result page. Tick and alert symbols allowed; no other emojis."""
    st.markdown(
        '<div class="top-banner">'
        '<h1>Assessment Results</h1>'
        '<p>Your offer has been evaluated against 50 expert rules.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.assessment_result:
        st.info("Complete the Assess form first, then come back here.")
        if st.button("Go to Assess", type="primary"):
            st.session_state.page = 'Assess'
            st.rerun()
        return

    result    = st.session_state.assessment_result
    analysis  = result['analysis']
    inference = result['inference']

    # Verdict card
    render_verdict_card(analysis['verdict'], analysis['verdict_reason'])

    # Quick stat row
    c1, c2, c3 = st.columns(3)
    c1.metric("Rules Triggered", analysis['total_rules_fired'])
    c2.metric("Critical Issues",  analysis['critical_issues'])
    c3.metric("Unknowns",         analysis['unknown_count'])

    # Score cards + bar chart
    section_head("Category Scores")
    render_score_cards(analysis['scores'])
    score_df = pd.DataFrame({
        'Category': list(analysis['scores'].keys()),
        'Score':    list(analysis['scores'].values()),
    }).set_index('Category')
    st.bar_chart(score_df, height=200)

    # Positive factors — use tick symbol (checkmark)
    if analysis['positive_factors']:
        section_head("Positive Factors")
        for factor in analysis['positive_factors']:
            st.success(f"✅  {factor}")

    # Risk factors — use alert symbol for critical
    if analysis['risk_factors']:
        section_head("Risk Factors")
        for risk in analysis['risk_factors']:
            if '[Critical]' in risk:
                st.error(f"🚨  {risk}")
            else:
                # Non-critical risks: plain warning box, no emoji
                st.warning(risk)

    # Recommendations
    section_head("Recommendations")
    for i, rec in enumerate(analysis['recommendations'], 1):
        st.markdown(f"**{i}.** {rec}")

    # Questions to ask employer
    if analysis['employer_questions']:
        section_head("Questions to Ask the Employer")
        for q in analysis['employer_questions']:
            st.markdown(f"- {q}")

    # Fired rules trace
    section_head("Why This Result?")
    with st.expander(
        f"See all {len(inference['fired_rules'])} triggered rules", expanded=False
    ):
        for fired in sorted(inference['fired_rules'], key=lambda r: r['firing_order']):
            render_rule_row(fired)
        if inference['overridden_rules']:
            st.markdown("**Conflict-resolution overrides:**")
            for ov in inference['overridden_rules']:
                st.markdown(
                    f"- `{ov['rule_id']}` {ov['rule_name']} "
                    f"*(reason: {ov['reason']})*"
                )

    # Download JSON
    section_head("Download Report")
    json_payload = {
        'timestamp':          result['timestamp'],
        'verdict':            analysis['verdict'],
        'verdict_reason':     analysis['verdict_reason'],
        'scores':             analysis['scores'],
        'positive_factors':   analysis['positive_factors'],
        'risk_factors':       analysis['risk_factors'],
        'recommendations':    analysis['recommendations'],
        'employer_questions': analysis['employer_questions'],
        'rules_fired':        [r['rule_id'] for r in inference['fired_rules']],
    }
    st.download_button(
        label="Download Full Report (JSON)",
        data=json.dumps(json_payload, indent=2),
        file_name=f"offerwise_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        key='btn_download_json',
        use_container_width=True,
    )

    # Disclaimer — no emojis
    st.markdown(
        '<div class="disclaimer">'
        '<strong>Disclaimer:</strong> OfferWise is a heuristic educational tool built on '
        'rule-based logic. It cannot guarantee an offer is genuine or that any company is '
        'legitimate. Always conduct your own due diligence and consult trusted advisors '
        'before accepting any offer.'
        '</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: WHAT-IF
# ═══════════════════════════════════════════════════════════════════════════════

def page_whatif():
    """What-If analysis page. No emojis except tick/alert in verdict display."""
    st.markdown(
        '<div class="top-banner">'
        '<h1>What-If Analysis</h1>'
        '<p>Adjust key parameters to see how the verdict changes.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.assessment_result:
        st.info("Run an assessment first, then explore What-If scenarios.")
        if st.button("Go to Assess", type="primary"):
            st.session_state.page = 'Assess'
            st.rerun()
        return

    original = st.session_state.user_inputs

    section_head("Change These Parameters")

    c1, c2, c3 = st.columns(3)
    with c1:
        new_pay = st.number_input(
            "Monthly Pay (PKR)",
            min_value=0, max_value=500_000,
            value=int(original.get('monthly_pay', 0) or 0),
            step=5_000, key='wi_pay',
        )
    with c2:
        new_hours = st.number_input(
            "Weekly Hours",
            min_value=0, max_value=80,
            value=int(original.get('weekly_hours', 40) or 40),
            step=5, key='wi_hours',
        )
    with c3:
        contract_opts = ['Yes', 'No', 'Verbal only', 'Not sure']
        cur_contract  = original.get('written_contract', 'Not sure')
        new_contract  = st.selectbox(
            "Written Contract?",
            options=contract_opts,
            index=contract_opts.index(cur_contract) if cur_contract in contract_opts else 3,
            key='wi_contract',
        )

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button(
        "Run What-If", type="primary", use_container_width=True, key='btn_whatif'
    )

    if run_btn:
        modified = original.copy()
        modified['monthly_pay']      = new_pay
        modified['weekly_hours']     = new_hours
        modified['written_contract'] = new_contract
        with st.spinner("Re-running engine..."):
            st.session_state.whatif_result = run_assessment(modified)

    if st.session_state.whatif_result:
        wi     = st.session_state.whatif_result
        orig_v = st.session_state.assessment_result['analysis']['verdict']
        new_v  = wi['analysis']['verdict']

        section_head("Before vs After")
        c1, c2 = st.columns(2)
        with c1:
            prefix, _, color = VERDICT_META.get(orig_v, ('', '', '#a0aec0'))
            sym = f"{prefix} " if prefix not in ('', '--') else ''
            st.markdown(
                f'<div class="wi-box">'
                f'<div class="wi-label">Original</div>'
                f'<span style="font-size:1.3rem;font-weight:800;color:{color};">'
                f'{sym}{orig_v}</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            prefix, _, color = VERDICT_META.get(new_v, ('', '', '#a0aec0'))
            sym = f"{prefix} " if prefix not in ('', '--') else ''
            st.markdown(
                f'<div class="wi-box">'
                f'<div class="wi-label">What-If</div>'
                f'<span style="font-size:1.3rem;font-weight:800;color:{color};">'
                f'{sym}{new_v}</span></div>',
                unsafe_allow_html=True,
            )

        # Score delta table
        section_head("Score Changes")
        orig_scores = st.session_state.assessment_result['analysis']['scores']
        new_scores  = wi['analysis']['scores']
        rows = []
        for cat in orig_scores:
            delta = new_scores[cat] - orig_scores[cat]
            arrow = "up" if delta > 0 else ("down" if delta < 0 else "no change")
            rows.append({
                'Category': cat,
                'Before':   orig_scores[cat],
                'After':    new_scores[cat],
                'Change':   f"{delta:+d} ({arrow})",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Rule changes
        section_head("Rule Changes")
        orig_ids = {r['rule_id'] for r in
                    st.session_state.assessment_result['inference']['fired_rules']}
        new_ids  = {r['rule_id'] for r in wi['inference']['fired_rules']}
        added    = new_ids  - orig_ids
        removed  = orig_ids - new_ids

        if added:
            st.markdown("**Rules newly triggered:**")
            for rid in sorted(added):
                rule = next(r for r in wi['inference']['fired_rules']
                            if r['rule_id'] == rid)
                st.markdown(f"- `{rid}` {rule['rule_name']} — _{rule['explanation']}_")
        if removed:
            st.markdown("**Rules no longer triggered:**")
            for rid in sorted(removed):
                rule = next(
                    r for r in
                    st.session_state.assessment_result['inference']['fired_rules']
                    if r['rule_id'] == rid
                )
                st.markdown(f"- `{rid}` {rule['rule_name']} — _{rule['explanation']}_")
        if not added and not removed:
            st.info("No change in triggered rules for these parameter values.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════════════════

def page_knowledge_base():
    """Browse all 50 rules with search and filter. No emojis."""
    st.markdown(
        f'<div class="top-banner">'
        f'<h1>Knowledge Base</h1>'
        f'<p>All <strong>{len(RULES)} expert rules</strong> that power the system.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Category stat row
    cats = [
        'Compensation', 'Career Growth', 'Workload and Conditions',
        'Legitimacy Red Flags', 'Overall Verdict',
    ]
    c_cols = st.columns(len(cats))
    for col, cat in zip(c_cols, cats):
        count = sum(1 for r in RULES if r['category'] == cat)
        col.metric(cat.split()[0], count)   # First word as short label

    # Search and filter controls
    section_head("Search and Filter")
    c1, c2 = st.columns([3, 1])
    with c1:
        search = st.text_input(
            "Search rules by name, explanation, or conditions",
            "", key='kb_search', placeholder="e.g. upfront payment",
        )
    with c2:
        all_cats   = ['All'] + cats
        sel_cat    = st.selectbox("Category", all_cats, key='kb_cat')

    sev_filter = st.multiselect(
        "Severity filter",
        ['Critical', 'High', 'Medium', 'Low'],
        default=['Critical', 'High', 'Medium', 'Low'],
        key='kb_sev',
    )

    # Apply filters
    filtered = RULES
    if sel_cat != 'All':
        filtered = [r for r in filtered if r['category'] == sel_cat]
    if sev_filter:
        filtered = [r for r in filtered if r['severity'] in sev_filter]
    if search:
        s = search.lower()
        filtered = [
            r for r in filtered
            if s in r['name'].lower()
            or s in r['explanation'].lower()
            or s in str(r['conditions']).lower()
        ]

    st.caption(f"Showing {len(filtered)} of {len(RULES)} rules")

    # Rules table
    rows = []
    for r in filtered:
        rows.append({
            'ID':          r['id'],
            'Rule Name':   r['name'],
            'Category':    r['category'],
            'Severity':    r['severity'],
            'Priority':    r['priority'],
            'Conclusion':  f"{r['conclusion']['fact']} = {r['conclusion']['value']}",
            'Explanation': r['explanation'],
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'ID':       st.column_config.TextColumn(width='small'),
            'Priority': st.column_config.NumberColumn(width='small', format='%d/10'),
            'Severity': st.column_config.TextColumn(width='small'),
        },
    )

    # Thresholds
    section_head("System Thresholds")
    with st.expander("View all PKR and numeric thresholds", expanded=False):
        th_rows = [{'Setting': k, 'Value': v} for k, v in THRESHOLDS.items()]
        st.dataframe(pd.DataFrame(th_rows), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Entry point: initialise state, render sidebar, route to active page."""
    initialize_session_state()
    render_sidebar()

    page = st.session_state.page
    if page == 'Assess':
        page_assess()
    elif page == 'Results':
        page_results()
    elif page == 'What-If':
        page_whatif()
    elif page == 'Knowledge Base':
        page_knowledge_base()

    # Silently validate KB; show errors in sidebar if any
    is_valid, errors = validate_knowledge_base()
    if not is_valid:
        with st.sidebar:
            st.error("KB validation errors:")
            for err in errors:
                st.write(f"- {err}")


if __name__ == '__main__':
    main()
