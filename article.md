# OpsMind: An Autonomous AI SRE Agent Powered by Persistent Memory

When a high-severity production outage hits at 3:00 AM, the last thing an on-call SRE needs is an AI assistant that greets them with a blank slate and asks what HikariCP is. Most LLM-based incident response tools treat every alert as an isolated prompt engineering exercise, forcing engineers to manually paste log snippets and re-explain failure modes that were already diagnosed, fixed, and documented six months ago.

We built **OpsMind** to eliminate this stateless inertia. OpsMind is an autonomous incident response platform designed to maintain long-term, structured memory across system failures. Rather than relying on simple context windows or static documentation searches, OpsMind integrates a persistent memory layer to retain post-mortem root causes, recall historical failure patterns during active alerts, and generate actionable remediation runbooks.

---

## System Architecture: How OpsMind Hangs Together

OpsMind is structured as a decoupled, modular system engineered for low latency, zero external API key leakage, and high operational resilience. 

```
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

The system consists of three core components:

1. **FastAPI Ingestion and Orchestration Layer (`backend/main.py`):** Serves as the central API gateway. It exposes `/api/triage` for alert telemetry processing and `/api/resolve` for post-mortem record retention.
2. **Persistent Agent Memory Layer (`backend/memory_client.py`):** Connects to the [Vectorize agent memory](https://vectorize.io/what-is-agent-memory) engine to execute structured memory retention and retrieval operations against named memory banks.
3. **Local Inference Execution Engine (`backend/llm_client.py`):** Interfaces with a local Ollama instance (`qwen2.5:3b`) to synthesize root-cause diagnoses without transmitting internal telemetry to external LLM providers. Includes an embedded fail-safe synthesis fallback to guarantee uptime if local LLM workers experience resource contention.

---

## Beyond RAG: Why Incident Response Demands True Agent Memory

When we initially evaluated standard Retrieval-Augmented Generation (RAG) for incident triage, we quickly encountered fundamental limitations. Standard RAG relies on naive vector similarity (e.g., cosine distance over fixed-size text chunks). In an SRE context, this approach breaks down for three reasons:

* **Log Noise and Token Dilution:** Raw stack traces, thread dumps, and timestamped log lines dilute vector space. Two completely different incidents can share 90% of their vocabulary (timestamps, thread IDs, log levels) while differing in the single line that identifies the root cause.
* **Lack of Temporal and Fact Awareness:** Naive vector indexes do not distinguish between a past resolution that worked versus an abandoned mitigation attempt documented in the same ticket.
* **Context Loss Across Outages:** Standard chat interfaces reset state between sessions. Even if an engineer spent hours debugging a Redis cache eviction cascade last week, a fresh chat session starts from scratch.

To solve this, we integrated [Hindsight docs](https://hindsight.vectorize.io/)-compliant persistent memory. Rather than treating past incidents as static text files in a vector store, OpsMind uses Hindsight to treat post-mortems as an evolving graph of temporal facts, service relationships, and verified remediation steps.

When an alert is received, OpsMind queries Hindsight using a hybrid retrieval engine combining semantic vectors, BM25 keyword matching, and service entity filtering. If a match exists, the agent injects past resolution context into the diagnostic prompt. If no match exists (a "cold start"), the agent falls back to baseline telemetry analysis and prompts the engineer for post-mortem feedback once resolved—closing the learning loop.

---

## Code-Backed Implementation Walkthrough

### 1. Hindsight Persistent Memory Client (`backend/memory_client.py`)

The `HindsightMemoryClient` class manages all memory communications with Vectorize Hindsight endpoints. It formats post-mortem records into structured documents and queries memory banks using score-weighted relevance filters.

```python
import json
import logging
import re
from pathlib import Path
from typing import List
import requests
from backend.config import HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL, HINDSIGHT_BANK_ID

logger = logging.getLogger("opsmind.memory")

class HindsightMemoryClient:
    """Client interfacing with Vectorize Hindsight persistent memory API."""

    def __init__(self):
        self.api_key = HINDSIGHT_API_KEY
        self.base_url = HINDSIGHT_BASE_URL.rstrip("/")
        self.bank_id = HINDSIGHT_BANK_ID
        self._local_memories: List[dict] = []
        self._load_sample_incidents()

    def recall_memories(self, query: str, top_k: int = 3) -> List[str]:
        """Recall matching historical incident post-mortems from Hindsight."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key and self.api_key != "your_hindsight_api_key_here":
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key

        payload = {"bank_id": self.bank_id, "query": query, "top_k": top_k}
        endpoints = [
            f"{self.base_url}/default/banks/{self.bank_id}/recall",
            f"{self.base_url}/banks/{self.bank_id}/recall",
            f"{self.base_url}/v1/default/banks/{self.bank_id}/recall"
        ]

        for url in endpoints:
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=0.8)
                if response.status_code == 200:
                    raw_list = response.json().get("memories") or response.json().get("results") or []
                    memories = [item if isinstance(item, str) else item.get("content", "") for item in raw_list]
                    if memories:
                        return memories[:top_k]
            except Exception as e:
                logger.debug(f"Recall attempt at {url} failed: {e}")
                continue

        # Dynamic local fallback for offline/resilience execution
        return self._local_dynamic_recall(query, top_k)
```

As shown in the implementation open-sourced on [Hindsight GitHub](https://github.com/vectorize-io/hindsight), the memory recall pipeline queries configured memory banks and extracts high-confidence historical matches before falling back to local cached state if network connectivity is disrupted.

### 2. Local LLM Execution & Fail-Safe Fallback (`backend/llm_client.py`)

To maintain absolute data privacy and eliminate third-party API costs during incident triage, OpsMind uses Ollama for local LLM inference. If the local Ollama process is unresponsive under heavy system load, the client seamlessly switches to a structured fail-safe synthesis engine.

```python
import logging
from typing import List, Tuple
import requests
from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger("opsmind.llm")

class OllamaClient:
    """Local LLM client with structured fail-safe fallback synthesis."""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL.rstrip("/")
        self.model = OLLAMA_MODEL

    def generate_diagnosis(self, alert_query: str, recalled_memories: List[str]) -> Tuple[str, str]:
        context_str = "\n---\n".join(recalled_memories) if recalled_memories else ""

        if recalled_memories:
            prompt = (
                "You are a senior SRE. Given these matching historical incidents from Hindsight memory:\n"
                f"{context_str}\n\n"
                f"Diagnose the current alert:\n{alert_query}\n\n"
                "Provide a clear root-cause diagnosis and recommended remediation steps.\n"
                "Format your response with: DIAGNOSIS: and RECOMMENDED ACTIONS:"
            )
        else:
            prompt = (
                "You are a senior SRE. No historical precedent exists in Hindsight memory for this incident.\n"
                f"Diagnose the current alert:\n{alert_query}\n\n"
                "Format your response with: DIAGNOSIS: and RECOMMENDED ACTIONS:"
            )

        try:
            url = f"{self.base_url}/api/generate"
            payload = {"model": self.model, "prompt": prompt, "stream": False}
            response = requests.post(url, json=payload, timeout=3.0)
            if response.status_code == 200:
                result_text = response.json().get("response", "")
                if result_text:
                    return self._parse_llm_output(result_text)
        except Exception as e:
            logger.warning(f"Ollama local inference unavailable ({e}). Triggering fail-safe synthesis.")

        return self._generate_failsafe_fallback(alert_query, recalled_memories)
```

### 3. FastAPI Orchestration & Post-Mortem Retention (`backend/main.py`)

The `/api/resolve` endpoint acts as the primary feedback loop. When an engineer resolves a novel outage, the post-mortem record is formatted and committed to Hindsight memory.

```python
from fastapi import FastAPI, HTTPException
from backend.schemas import AlertRequest, TriageResponse, ResolutionRequest, ResolutionResponse
from backend.memory_client import HindsightMemoryClient
from backend.llm_client import OllamaClient

app = FastAPI(title="OpsMind Service", version="1.0.0")

memory_client = HindsightMemoryClient()
llm_client = OllamaClient()

@app.post("/api/triage", response_model=TriageResponse)
def triage_alert(alert: AlertRequest):
    query_str = (
        f"Service: {alert.service} | Error Rate: {alert.error_rate} | "
        f"Latency: {alert.latency} | DB Conn: {alert.db_connections} | "
        f"Log: {alert.log_excerpt}"
    )
    recalled_memories = memory_client.recall_memories(query=query_str, top_k=3)
    memory_found = len(recalled_memories) > 0

    diagnosis, recommended_action = llm_client.generate_diagnosis(query_str, recalled_memories)

    return TriageResponse(
        diagnosis=diagnosis,
        recalled_memories=recalled_memories,
        memory_found=memory_found,
        recommended_action=recommended_action
    )

@app.post("/api/resolve", response_model=ResolutionResponse)
def resolve_incident(req: ResolutionRequest):
    stored_entry = (
        f"Incident {req.incident_id} [{req.service}]: "
        f"Symptoms: {req.symptoms_summary}. "
        f"Root Cause: {req.root_cause}. "
        f"Resolution: {req.resolution_steps}. "
        f"Successful: {req.was_successful}"
    )
    success = memory_client.store_memory(content=stored_entry)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store post-mortem in Hindsight.")

    return ResolutionResponse(status="success", stored_entry=stored_entry)
```

---

## System Behavior & Real-World Interaction Flow

To illustrate how OpsMind functions in production, consider a multi-stage operational scenario involving a microservices cluster:

### Scenario 1: Novel Failure Mode (Cold Start)

An alert triggers on a newly deployed billing worker:
```json
POST /api/triage
{
  "service": "billing-engine",
  "error_rate": "78.9%",
  "latency": "16500ms",
  "db_connections": "12%",
  "log_excerpt": "ERROR [billing-engine] PaymentWebhookException: Gateway signature verification failed. Connection reset by peer after 16500ms waiting for auth.payments.internal:443."
}
```

**OpsMind Evaluation:**
1. OpsMind queries Hindsight memory bank for `billing-engine` failure signatures.
2. Hindsight returns 0 matching records (`memory_found = False`).
3. The system returns a baseline diagnostic analysis acknowledging that no historical precedent exists.

```json
Response:
{
  "memory_found": false,
  "recalled_memories": [],
  "diagnosis": "[Cold Start Analysis] No historical precedent found in Hindsight memory for billing-engine webhook verification timeouts. Telemetry indicates network socket reset or SSL handshake failure.",
  "recommended_action": "1. Verify network egress rules to auth.payments.internal.\n2. Inspect gateway SSL certificate expiry.\n3. Check worker thread pool saturation."
}
```

### Scenario 2: Retaining the Post-Mortem

The on-call SRE investigates, identifies an expired SSL certificate on the payment gateway, renews the certificate, scales the worker pool, and commits the post-mortem via `/api/resolve`:

```json
POST /api/resolve
{
  "incident_id": "INC-2026-004",
  "service": "billing-engine",
  "symptoms_summary": "High latency (16500ms) and 78.9% webhook verification failure rate.",
  "root_cause": "Expired SSL certificate on auth.payments.internal endpoint causing TCP connection resets.",
  "resolution_steps": "1. Renewed wildcard SSL cert on auth.payments.internal.\n2. Scaled billing-engine pods from 2 to 6.\n3. Restarted worker pods.",
  "was_successful": true
}
```

OpsMind passes this structured record to Hindsight's `retain` pipeline, indexing the service entity, failure symptom, and remediation steps.

### Scenario 3: Recurring Failure (Warm Memory Match)

Two weeks later, an ISP degradation causes similar socket timeouts on `billing-engine`. The telemetry alert is re-triggered:

```json
POST /api/triage
{
  "service": "billing-engine",
  "error_rate": "82.1%",
  "latency": "17100ms",
  "db_connections": "14%",
  "log_excerpt": "ERROR [billing-engine] PaymentWebhookException: Connection reset by peer after 17100ms waiting for auth.payments.internal:443."
}
```

**OpsMind Evaluation:**
1. OpsMind queries Hindsight memory.
2. Hindsight matches `billing-engine` and the network socket timeout pattern against `INC-2026-004`.
3. OpsMind returns `memory_found = True`, pulling the exact historical post-mortem directly into the triage response:

```json
Response:
{
  "memory_found": true,
  "recalled_memories": [
    "Incident INC-2026-004 [billing-engine]: Symptoms: High latency (16500ms) and 78.9% webhook verification failure rate. Root Cause: Expired SSL certificate on auth.payments.internal endpoint causing TCP connection resets. Resolution: 1. Renewed wildcard SSL cert on auth.payments.internal. 2. Scaled billing-engine pods from 2 to 6. 3. Restarted worker pods. Successful: True"
  ],
  "diagnosis": "Hindsight memory matched historical precedent INC-2026-004. Current telemetry strongly correlates with past SSL certificate/network socket timeout failures on auth.payments.internal.",
  "recommended_action": "1. Verify SSL cert validity on auth.payments.internal endpoint.\n2. Scale billing-engine worker pods to absorb queue backlog.\n3. Verify network gateway routing rules."
}
```

---

## Lessons Learned: Engineering Takeaways

Building OpsMind reinforced several key principles for engineering teams building operational AI tooling:

1. **State Must Outlive Session Boundaries:** Chatbot interfaces that clear context on page refresh are useless for SRE teams. Agent memory must be decoupled into durable, queryable infrastructure.
2. **Vector Similarity Search Is Not Enough:** Pure embedding distance fails on structured telemetry. Effective agent memory requires hybrid retrieval combining entity extraction, keyword matching, and temporal ranking.
3. **Fail-Safe Fallbacks Are Non-Negotiable:** Production management tools cannot crash when an upstream LLM times out. Embedding structured fallback synthesis directly into API clients ensures 100% system availability.
4. **Post-Mortems Are First-Class Write Operations:** AI agents in production should not merely consume data; they must provide explicit mechanisms for human operators to commit verified resolutions back into the system's memory bank.
5. **Local Inference Protects Infrastructure Privacy:** Running local models via Ollama allows teams to process internal logs, stack traces, and system architecture details without streaming proprietary telemetry to public cloud APIs.
