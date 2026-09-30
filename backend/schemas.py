from pydantic import BaseModel, Field
from typing import List, Optional


class AlertRequest(BaseModel):
    """Pydantic model representing an incoming telemetry alert."""
    service: str = Field(..., description="Name of the affected service")
    error_rate: str = Field(..., description="Current error rate percentage or description")
    latency: str = Field(..., description="Observed latency (e.g. 8200ms or 95th percentile)")
    db_connections: str = Field(..., description="Database connection utilization percentage or count")
    log_excerpt: str = Field(..., description="Relevant application error log snippet")


class TriageResponse(BaseModel):
    """Pydantic model representing the triage analysis returned by the agent."""
    diagnosis: str = Field(..., description="Root cause diagnosis produced by Ollama or fail-safe engine")
    recalled_memories: List[str] = Field(default_factory=list, description="List of historical memories recalled from Hindsight")
    memory_found: bool = Field(..., description="Flag indicating if relevant historical memory was found")
    recommended_action: str = Field(..., description="Actionable runbook steps for remediation")


class ResolutionRequest(BaseModel):
    """Pydantic model representing a post-mortem incident resolution to commit."""
    incident_id: str = Field(..., description="Unique incident identifier (e.g. INC-2026-001)")
    service: str = Field(..., description="Target service name")
    symptoms_summary: str = Field(..., description="Summary of observed symptoms")
    root_cause: str = Field(..., description="Identified root cause")
    resolution_steps: str = Field(..., description="Steps taken to resolve the incident")
    was_successful: bool = Field(default=True, description="Whether the resolution was successful")


class ResolutionResponse(BaseModel):
    """Pydantic model representing the confirmation of a stored resolution."""
    status: str = Field(..., description="Status of the store operation (e.g. 'success')")
    stored_entry: str = Field(..., description="Formatted post-mortem string committed to Hindsight")
