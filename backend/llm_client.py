import logging
from typing import List, Tuple
import requests

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger("opsmind.llm")


class OllamaClient:
    """
    Local LLM Client interfacing with Ollama for zero-API-key inference.
    Includes a fail-safe synthesis fallback if Ollama is not running locally.
    """

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL.rstrip("/")
        self.model = OLLAMA_MODEL

    def generate_diagnosis(self, alert_query: str, recalled_memories: List[str]) -> Tuple[str, str]:
        """
        Generate incident diagnosis and recommended remediation actions.
        Returns a tuple of (diagnosis_text, recommended_action_text).
        """
        context_str = "\n---\n".join(recalled_memories) if recalled_memories else ""

        if recalled_memories:
            prompt = (
                "You are a senior SRE. Given these matching historical incidents from Hindsight persistent memory:\n"
                f"{context_str}\n\n"
                f"Diagnose the current alert:\n{alert_query}\n\n"
                "Provide a clear root-cause diagnosis and recommend immediate remediation steps.\n"
                "Format your response with two sections:\n"
                "DIAGNOSIS:\n[Your concise diagnosis based on historical precedent]\n\n"
                "RECOMMENDED ACTIONS:\n[Step-by-step remediation steps]"
            )
        else:
            prompt = (
                "You are a senior SRE. No historical precedent exists in Hindsight persistent memory for this incident (Cold Start).\n"
                f"Diagnose the current alert:\n{alert_query}\n\n"
                "Provide generic diagnostic steps and state clearly that no past matching incident was found in Hindsight.\n"
                "Format your response with two sections:\n"
                "DIAGNOSIS:\n[Cold start diagnostic analysis]\n\n"
                "RECOMMENDED ACTIONS:\n[Standard SRE diagnostic and triage steps]"
            )

        # Try Ollama endpoint first
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=3.0)
            if response.status_code == 200:
                result_text = response.json().get("response", "")
                if result_text:
                    diagnosis, actions = self._parse_llm_output(result_text, bool(recalled_memories))
                    logger.info("Successfully generated diagnosis using Ollama local model.")
                    return diagnosis, actions
        except Exception as e:
            logger.warning(f"Ollama local inference unavailable ({e}). Triggering fail-safe synthesis fallback.")

        # Fail-Safe Synthesis Fallback
        return self._generate_failsafe_fallback(alert_query, recalled_memories)

    def _parse_llm_output(self, text: str, memory_found: bool) -> Tuple[str, str]:
        """Parse structured DIAGNOSIS and RECOMMENDED ACTIONS from LLM text output."""
        if "DIAGNOSIS:" in text and "RECOMMENDED ACTIONS:" in text:
            parts = text.split("RECOMMENDED ACTIONS:")
            diagnosis_part = parts[0].replace("DIAGNOSIS:", "").strip()
            actions_part = parts[1].strip()
            return diagnosis_part, actions_part
        else:
            # Simple line-based split heuristic if LLM didn't format headings exactly
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            midpoint = max(1, len(lines) // 2)
            diagnosis = " ".join(lines[:midpoint])
            actions = "\n".join(lines[midpoint:])
            return diagnosis, actions

    def _generate_failsafe_fallback(self, alert_query: str, recalled_memories: List[str]) -> Tuple[str, str]:
        """
        Structured fail-safe fallback synthesis when local Ollama server is offline.
        Ensures the hackathon evaluation and demo never crash.
        """
        if recalled_memories:
            primary_memory = recalled_memories[0]
            diagnosis = (
                "[Fail-Safe Direct Synthesis] Hindsight memory match identified matching historical precedent:\n"
                f"• Recalled Precedent: {primary_memory}\n"
                "• Analysis: Incoming alert metrics align with past failure patterns (e.g. database pool exhaustion, cache eviction, or webhook gateway timeout)."
            )
            actions = (
                "1. Scale connection pool / resources to accommodate peak demand (e.g., increase maxPoolSize or replica counts).\n"
                "2. Apply indexing or caching to mitigate bottleneck queries identified in past incident post-mortems.\n"
                "3. Perform controlled rolling restart of impacted service pods and monitor response times."
            )
        else:
            diagnosis = (
                "[Fail-Safe Fallback - Cold Start] No historical precedent found in Hindsight persistent memory for this alert pattern.\n"
                "Initial triage indicates an isolated or novel service failure requiring immediate telemetry investigation."
            )
            actions = (
                "1. Inspect active error traces and tail application logs for unhandled exceptions.\n"
                "2. Check node-level CPU, memory, network I/O, and database connection pools.\n"
                "3. Perform incident post-mortem upon resolution and commit details to Hindsight to build future memory context."
            )

        return diagnosis, actions
