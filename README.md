<div align="center">

# ⚡ OpsMind — Autonomous AI Incident Response Agent

**An AI-powered SRE Triage Platform built with Vectorize Hindsight Persistent Memory and Local LLM Inference.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25%2B-FF4B4B.svg)](https://streamlit.io/)
[![Hindsight](https://img.shields.io/badge/Memory-Vectorize%20Hindsight-6366F1.svg)](https://hindsight.vectorize.io/)
[![Ollama](https://img.shields.io/badge/Inference-Ollama%20Local-000000.svg)](https://ollama.ai/)

</div>

---

## 📌 Overview

**OpsMind** eliminates stateless inertia in site reliability engineering (SRE). Traditional LLM-based incident tools treat every production alert as an isolated prompt, forcing engineers to manually re-explain failure patterns that were already diagnosed and fixed months ago.

OpsMind integrates a **persistent long-term memory layer powered by Vectorize Hindsight**. When an alert hits, OpsMind recalls matching historical incident post-mortems to deliver instant, 1-2-3 remediation runbooks. When novel outages occur, engineers commit verified resolutions back into Hindsight memory—continuously expanding the platform's operational expertise over time.

---

## 🏗️ Architecture

```text
                                +-----------------------------------+
                                |     Streamlit Control Plane       |
                                |         (frontend/app.py)         |
                                +-----------------+-----------------+
                                                  |
                                            HTTP / JSON
                                                  |
                                                  v
                                +-----------------+-----------------+
                                |      FastAPI Server Backend       |
                                |        (backend/main.py)          |
                                +--------+----------------+---------+
                                         |                |
                       Recall / Retain   |                |  Generate Diagnosis
                                         v                v
                 +-----------------------+--+   +---------+-------------------+
                 | Hindsight Memory Client  |   |   Ollama Local LLM Client   |
                 | (backend/memory_client)  |   |    (backend/llm_client.py)  |
                 +--------------+-----------+   +-----------------------------+
                                |
                         REST / HTTP
                                |
                                v
                 +--------------+-----------+
                 |  Vectorize Hindsight API |
                 | (Persistent Memory Bank) |
                 +--------------------------+
```

---

## ✨ Key Features

- 🧠 **Persistent Agent Memory (Vectorize Hindsight):** Retains incident post-mortems and performs score-weighted relevance recalls across named memory banks.
- 🔒 **Zero-API-Key Local Inference (Ollama):** Runs root-cause diagnostics locally (`qwen2.5:3b`), keeping sensitive infrastructure logs inside your environment.
- ⚡ **Fail-Safe Fallback Synthesis:** Features an embedded direct memory synthesis fallback to guarantee 100% uptime if local LLM workers experience resource contention.
- 📝 **Post-Mortem Feedback Loop:** Serves as a continuous learning pipeline where resolved outages are committed back to Hindsight memory.
- 🖥️ **Dark Glassmorphism SRE Command Center:** High-contrast Streamlit dashboard with KPI metric cards, preset scenarios, and memory inspection banners.

---

## 📂 Project Structure

```text
OpsMind/
├── run.py                # Single-command Python launcher (Backend + Frontend)
├── run.bat               # One-click Windows batch launcher
├── requirements.txt      # Python package dependencies
├── .env.example         # Environment variable template
├── .gitignore            # Git exclusion rules
├── README.md             # GitHub repository documentation
├── article.md            # Technical blog post article
│
├── backend/
│   ├── __init__.py
│   ├── config.py         # Environment loader (.env)
│   ├── schemas.py        # Pydantic models (AlertRequest, TriageResponse, etc.)
│   ├── memory_client.py # Vectorize Hindsight API integration (retain & recall)
│   ├── llm_client.py    # Local Ollama client with fail-safe fallback
│   └── main.py          # FastAPI application server
│
├── frontend/
│   └── app.py            # Streamlit SRE Command Center control plane
│
├── .streamlit/
│   └── config.toml       # Streamlit theme & toolbar configuration
│
└── data/
    └── sample_incidents.json # Synthetic incident post-mortem dataset
```

---

## 🚀 Quickstart Guide

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/YOUR_USERNAME/OpsMind.git
cd OpsMind

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux / macOS:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Secrets

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Open `.env` and add your `HINDSIGHT_API_KEY`:

```env
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io/v1
HINDSIGHT_BANK_ID=opsmind-incidents
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

> **Note:** `HINDSIGHT_API_KEY` is the ONLY required API key in the entire project. Ollama runs locally without external LLM keys.

### 3. Launch Services (Single Command)

```bash
python run.py
```
*(Or double-click `run.bat` on Windows. This automatically launches both the Backend API on port 8000 and the Streamlit Dashboard on port 8501 concurrently!)*

- 💻 **Frontend UI:** `http://localhost:8501`
- ⚙️ **Backend API Docs:** `http://localhost:8000/docs`

---

## 📡 REST API Reference

### `POST /api/triage`
Triages incoming alert telemetry, queries Hindsight memory, and synthesizes root-cause diagnosis.

**Request Payload:**
```json
{
  "service": "checkout-service",
  "error_rate": "45.2%",
  "latency": "8200ms",
  "db_connections": "100% (Pool Exhausted)",
  "log_excerpt": "ERROR [checkout-service] HikariPool-1 - Connection is not available, request timed out after 30000ms."
}
```

### `POST /api/resolve`
Commits a verified incident post-mortem resolution into Hindsight persistent memory.

**Request Payload:**
```json
{
  "incident_id": "INC-2026-004",
  "service": "billing-engine",
  "symptoms_summary": "High latency (16500ms) and 78.9% webhook verification failure rate.",
  "root_cause": "Expired SSL certificate on gateway endpoint.",
  "resolution_steps": "1. Renewed SSL cert.\n2. Scaled worker pods from 2 to 6.",
  "was_successful": true
}
```

---

## 🧪 Testing Memory Learning Loop

1. **Test a Novel Outage (Cold Start):**
   - Click **`🧊 Novel Incident (Billing Engine Timeout)`** → Click **`🔍 Analyze Incident`**.
   - **Observe:** Slate banner `⚪ NOVEL INCIDENT DETECTED` appears showing no historical precedent exists in memory.
2. **Commit Post-Mortem Resolution:**
   - Scroll to **Post-Mortem Feedback Loop** and click **`💾 Commit Resolution to Hindsight Memory`**.
3. **Test Recurring Outage (Warm Memory Recall):**
   - Click **`🔍 Analyze Incident`** on `billing-engine` again.
   - **Observe:** Banner turns **GREEN** (`🟢 RECURRING INCIDENT DETECTED`), recalling your newly saved post-mortem fix!
