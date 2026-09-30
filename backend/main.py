from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import AlertRequest, TriageResponse, ResolutionRequest, ResolutionResponse
from backend.memory_client import HindsightMemoryClient
from backend.llm_client import OllamaClient

app = FastAPI(
    title="OpsMind Backend Service",
    description="AI Incident Response Agent powered by Hindsight Persistent Memory and Ollama Local Inference",
    version="1.0.0"
)

# Enable CORS for local Streamlit frontend & web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Memory and LLM clients
memory_client = HindsightMemoryClient()
llm_client = OllamaClient()


@app.get("/health")
def health_check():
    """Health-check endpoint returning system status."""
    return {
        "status": "ok",
        "service": "OpsMind Backend",
        "memory_client": "active",
        "ollama_client": "active"
    }


@app.post("/api/triage", response_model=TriageResponse)
def triage_alert(alert: AlertRequest):
    """
    Triage incoming incident alert:
    1. Synthesize alert symptoms into a memory search query.
    2. Recall historical matching incidents from Hindsight memory.
    3. Generate root cause diagnosis and recommended remediation steps.
    """
    try:
        # Synthesize alert attributes into search query string
        query_str = (
            f"Service: {alert.service} | Error Rate: {alert.error_rate} | "
            f"Latency: {alert.latency} | DB Conn: {alert.db_connections} | "
            f"Log: {alert.log_excerpt}"
        )

        # 1. Recall past memories from Hindsight
        recalled_memories = memory_client.recall_memories(query=query_str, top_k=3)
        memory_found = len(recalled_memories) > 0

        # 2. Generate diagnosis and recommendations via Ollama / Fail-safe synthesis
        diagnosis, recommended_action = llm_client.generate_diagnosis(
            alert_query=query_str,
            recalled_memories=recalled_memories
        )

        return TriageResponse(
            diagnosis=diagnosis,
            recalled_memories=recalled_memories,
            memory_found=memory_found,
            recommended_action=recommended_action
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing incident triage: {str(e)}")


@app.post("/api/resolve", response_model=ResolutionResponse)
def resolve_incident(req: ResolutionRequest):
    """
    Post-mortem feedback loop:
    Format the resolution summary and store it in Hindsight persistent memory.
    """
    try:
        stored_entry = (
            f"Incident {req.incident_id} [{req.service}]: "
            f"Symptoms: {req.symptoms_summary}. "
            f"Root Cause: {req.root_cause}. "
            f"Resolution: {req.resolution_steps}. "
            f"Successful: {req.was_successful}"
        )

        # Commit entry to Hindsight memory
        success = memory_client.store_memory(content=stored_entry)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store memory entry in Hindsight.")

        return ResolutionResponse(
            status="success",
            stored_entry=stored_entry
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error committing resolution: {str(e)}")
