import streamlit as st
import requests
import json

# Streamlit Page Config
st.set_page_config(
    page_title="OpsMind — AI Incident Response Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

    /* Hide Streamlit Header, Toolbar, Deploy Button & Footer */
    #MainMenu {visibility: hidden; display: none !important;}
    header {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    button[title="Deploy"] {display: none !important;}

    .stApp {
        background-color: #030712;
        color: #f3f4f6;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Command Center Header */
    .hud-header {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(3, 7, 18, 0.98) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -10px rgba(0, 242, 254, 0.15);
    }
    
    .hud-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .hud-subtitle {
        color: #94a3b8;
        font-size: 0.98rem;
        margin-top: 6px;
    }

    /* Telemetry KPI Metric Cards */
    .kpi-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.7);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .kpi-label {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    .kpi-value {
        color: #f8fafc;
        font-size: 1.3rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
    }

    /* Memory Match Banners */
    .banner-warm-glow {
        background: linear-gradient(135deg, rgba(6, 95, 70, 0.7) 0%, rgba(4, 120, 87, 0.5) 100%);
        border: 1px solid #10b981;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.25);
        color: #6ee7b7;
        padding: 18px 24px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 20px;
    }

    .banner-cold-glow {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid #64748b;
        color: #cbd5e1;
        padding: 18px 24px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.05rem;
        margin-bottom: 20px;
    }

    .memory-card-box {
        background: rgba(30, 27, 75, 0.6);
        border-left: 4px solid #818cf8;
        border-top: 1px solid rgba(99, 102, 241, 0.3);
        border-right: 1px solid rgba(99, 102, 241, 0.3);
        border-bottom: 1px solid rgba(99, 102, 241, 0.3);
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        color: #e0e7ff;
        font-size: 0.92rem;
        line-height: 1.5;
    }

    .memory-card-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: #a5b4fc;
        font-weight: 700;
        margin-bottom: 6px;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# Backend URL Configuration
BACKEND_URL = "http://localhost:8000"

# Initialize Session State Variables
if "service" not in st.session_state:
    st.session_state["service"] = "checkout-service"
if "latency" not in st.session_state:
    st.session_state["latency"] = "8200ms"
if "error_rate" not in st.session_state:
    st.session_state["error_rate"] = "45.2%"
if "db_connections" not in st.session_state:
    st.session_state["db_connections"] = "100% (Pool Exhausted)"
if "log_excerpt" not in st.session_state:
    st.session_state["log_excerpt"] = (
        "2026-09-29 14:30:02 ERROR [checkout-service] HikariPool-1 - Connection is not available, "
        "request timed out after 30000ms. Active connections: 100/100, waiting threads: 45."
    )
if "triage_result" not in st.session_state:
    st.session_state["triage_result"] = None

# Top Header Banner
st.markdown("""
<div class="hud-header">
    <div class="hud-title">⚡ OpsMind — AI Incident Response Agent</div>
    <div class="hud-subtitle">Autonomous SRE Triage & Remediation Platform powered by Vectorize Hindsight Persistent Memory</div>
</div>
""", unsafe_allow_html=True)

# Telemetry KPI Overview Cards
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Target Service</div>
        <div class="kpi-value" style="color: #38bdf8;">{st.session_state['service']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Latency (p95/p99)</div>
        <div class="kpi-value" style="color: #f59e0b;">{st.session_state['latency']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Error Rate</div>
        <div class="kpi-value" style="color: #ef4444;">{st.session_state['error_rate']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">DB Connections</div>
        <div class="kpi-value" style="color: #ec4899;">{st.session_state['db_connections']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Two-Column Triage View
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 🚨 Telemetry Alert Controls")
    st.caption("Select a preset scenario or customize parameters to simulate incoming incident telemetry:")
    
    # 3 Preset Action Buttons
    preset_c1, preset_c2, preset_c3 = st.columns(3)
    
    with preset_c1:
        if st.button("🧊 Novel Incident\n(Billing Engine Timeout)", use_container_width=True):
            st.session_state["service"] = "billing-engine"
            st.session_state["latency"] = "16500ms"
            st.session_state["error_rate"] = "78.9%"
            st.session_state["db_connections"] = "12%"
            st.session_state["log_excerpt"] = (
                "2026-09-29 20:00:15 ERROR [billing-engine] PaymentWebhookException: Gateway signature "
                "verification failed. Connection reset by peer after 16500ms waiting for auth.payments.internal:443."
            )
            st.rerun()

    with preset_c2:
        if st.button("🔥 Recurring Incident\n(Database Pool Exhausted)", use_container_width=True):
            st.session_state["service"] = "checkout-service"
            st.session_state["latency"] = "8200ms"
            st.session_state["error_rate"] = "45.2%"
            st.session_state["db_connections"] = "100% (Pool Exhausted)"
            st.session_state["log_excerpt"] = (
                "2026-09-29 14:30:02 ERROR [checkout-service] HikariPool-1 - Connection is not available, "
                "request timed out after 30000ms. Active connections: 100/100, waiting threads: 45."
            )
            st.rerun()

    with preset_c3:
        if st.button("⚡ Cache Cascade\n(Redis Eviction Spike)", use_container_width=True):
            st.session_state["service"] = "catalog-api"
            st.session_state["latency"] = "3200ms"
            st.session_state["error_rate"] = "38.9%"
            st.session_state["db_connections"] = "28%"
            st.session_state["log_excerpt"] = (
                "2026-09-28 09:15:22 WARN [catalog-api] Redis eviction policy volatile-lru triggered. "
                "15,000 keys evicted in 5 seconds. Cache hit ratio dropped from 94% to 11%."
            )
            st.rerun()

    st.markdown("---")

    # Alert Inputs Form
    with st.form("triage_form"):
        st.markdown("### ⚙️ Incident Triage Parameters")
        service_name = st.text_input("Service Identifier", value=st.session_state["service"])
        
        input_c1, input_c2 = st.columns(2)
        with input_c1:
            latency_val = st.text_input("Observed Latency", value=st.session_state["latency"])
            error_rate_val = st.text_input("Error Rate (%)", value=st.session_state["error_rate"])
        with input_c2:
            db_conn_val = st.text_input("DB Connection Pool %", value=st.session_state["db_connections"])

        logs_val = st.text_area("Application Error Log Excerpt", value=st.session_state["log_excerpt"], height=130)

        analyze_btn = st.form_submit_button("🔍 Analyze Incident", use_container_width=True, type="primary")

    if analyze_btn:
        payload = {
            "service": service_name,
            "error_rate": error_rate_val,
            "latency": latency_val,
            "db_connections": db_conn_val,
            "log_excerpt": logs_val
        }
        with st.spinner("Searching Hindsight Memory Bank & Synthesizing Diagnosis..."):
            try:
                res = requests.post(f"{BACKEND_URL}/api/triage", json=payload, timeout=30)
                if res.status_code == 200:
                    st.session_state["triage_result"] = res.json()
                else:
                    st.error(f"Backend API error ({res.status_code}): {res.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend server at {BACKEND_URL}: {e}")

with col_right:
    st.markdown("### 🧠 Agent Intelligence & Memory Inspector")
    
    triage_data = st.session_state.get("triage_result")
    
    if triage_data:
        memory_found = triage_data.get("memory_found", False)
        recalled_mems = triage_data.get("recalled_memories", [])
        diagnosis = triage_data.get("diagnosis", "")
        recommended_action = triage_data.get("recommended_action", "")

        # Memory Match Banner
        if memory_found:
            st.markdown(
                f'<div class="banner-warm-glow">🟢 <b>RECURRING INCIDENT DETECTED</b> — Hindsight Recalled {len(recalled_mems)} Past Post-Mortem Fixes</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="banner-cold-glow">⚪ <b>NOVEL INCIDENT DETECTED</b> — No Historical Precedent Found in Hindsight Memory</div>',
                unsafe_allow_html=True
            )

        # Recalled Memories Container
        with st.expander("📌 Recalled Incident Post-Mortems from Hindsight Memory", expanded=True):
            if recalled_mems:
                for idx, mem in enumerate(recalled_mems, 1):
                    st.markdown(f"""
                    <div class="memory-card-box">
                        <div class="memory-card-header">Hindsight Memory Record #{idx}</div>
                        {mem}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No past incident post-mortems matched this telemetry vector in Hindsight memory.")

        # Diagnosis & Remediation Tabs
        tab_diag, tab_action = st.tabs(["🔬 Root Cause Diagnosis", "🛠️ Actionable Remediation Runbook"])

        with tab_diag:
            st.info(diagnosis)

        with tab_action:
            st.success(recommended_action)

    else:
        st.info("Select a preset scenario on the left or click **Analyze Incident** to inspect the AI agent's memory triage output.")

# Bottom Section: Post-Mortem Feedback Loop
st.markdown("---")
st.markdown("### 📝 Post-Mortem Feedback Loop")
st.caption("Commit verified incident resolutions to Hindsight memory bank to continuously expand agent domain expertise.")

with st.form("resolve_form"):
    res_c1, res_c2 = st.columns(2)
    with res_c1:
        inc_id = st.text_input("Incident ID Tag", value="INC-2026-004")
        target_service = st.text_input("Target Affected Service", value=st.session_state["service"])
        symptoms_sum = st.text_area(
            "Symptoms & Observed Impact",
            value=f"High latency ({st.session_state['latency']}) and error rate spike ({st.session_state['error_rate']}).",
            height=90
        )
    with res_c2:
        root_cause_input = st.text_area(
            "Verified Root Cause Analysis",
            value="OAuth2 authentication server token validation timeout due to expired SSL certificate and low replica count.",
            height=90
        )
        resolution_steps_input = st.text_area(
            "Remediation Steps Executed",
            value="1. Renewed SSL certificate on auth.iam.internal\n2. Scaled auth-service replicas from 2 to 6\n3. Restarted auth pods.",
            height=90
        )
        was_succ = st.checkbox("Resolution Verified & Successful", value=True)

    commit_btn = st.form_submit_button("💾 Commit Resolution to Hindsight Memory", use_container_width=True, type="primary")

if commit_btn:
    resolve_payload = {
        "incident_id": inc_id,
        "service": target_service,
        "symptoms_summary": symptoms_sum,
        "root_cause": root_cause_input,
        "resolution_steps": resolution_steps_input,
        "was_successful": was_succ
    }
    with st.spinner("Persisting incident post-mortem into Hindsight Memory Bank..."):
        try:
            res = requests.post(f"{BACKEND_URL}/api/resolve", json=resolve_payload, timeout=30)
            if res.status_code == 200:
                st.toast("✅ Incident Post-Mortem committed to Hindsight Memory!", icon="🧠")
                st.success("Successfully saved post-mortem resolution to Hindsight Persistent Memory!")
                st.json(res.json())
            else:
                st.error(f"Failed to commit resolution ({res.status_code}): {res.text}")
        except Exception as e:
            st.error(f"Error communicating with backend server: {e}")
