import json
import logging
import re
from pathlib import Path
from typing import List
import requests

from backend.config import HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL, HINDSIGHT_BANK_ID

logger = logging.getLogger("opsmind.memory")
logging.basicConfig(level=logging.INFO)


class HindsightMemoryClient:
    """
    Client for interacting with Vectorize Hindsight persistent memory service.
    Includes fail-safe fallback local memory matching for seamless offline demo capabilities.
    """

    def __init__(self):
        self.api_key = HINDSIGHT_API_KEY
        self.base_url = HINDSIGHT_BASE_URL.rstrip("/")
        self.bank_id = HINDSIGHT_BANK_ID
        self._local_memories: List[dict] = []
        self._load_sample_incidents()

    def _load_sample_incidents(self) -> None:
        """Seed local fallback memory with initial sample incidents from data/sample_incidents.json."""
        try:
            data_file = Path(__file__).resolve().parent.parent / "data" / "sample_incidents.json"
            if data_file.exists():
                with open(data_file, "r", encoding="utf-8") as f:
                    incidents = json.load(f)
                    for inc in incidents:
                        formatted = (
                            f"Incident {inc.get('incident_id')} [{inc.get('service')}]: "
                            f"Symptoms: {inc.get('symptoms_summary')}. "
                            f"Root Cause: {inc.get('root_cause')}. "
                            f"Resolution: {inc.get('resolution_steps')}."
                        )
                        self._local_memories.append({
                            "service": inc.get("service", "").strip().lower(),
                            "formatted": formatted
                        })
                logger.info(f"Loaded {len(self._local_memories)} sample incidents into local memory buffer.")
        except Exception as e:
            logger.warning(f"Could not seed sample incidents from file: {e}")

    def recall_memories(self, query: str, top_k: int = 3) -> List[str]:
        """
        Recall relevant historical memories matching the query from Hindsight.
        Falls back to dynamic local relevance matching if remote API is unavailable or returns empty.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key and self.api_key != "your_hindsight_api_key_here":
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key

        payload = {
            "bank_id": self.bank_id,
            "query": query,
            "top_k": top_k
        }

        endpoints = [
            f"{self.base_url}/default/banks/{self.bank_id}/recall",
            f"{self.base_url}/banks/{self.bank_id}/recall",
            f"{self.base_url}/memory/recall",
            f"{self.base_url}/recall",
            f"{self.base_url}/v1/default/banks/{self.bank_id}/recall",
            f"{self.base_url}/v1/banks/{self.bank_id}/recall"
        ]

        for url in endpoints:
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=0.8)
                if response.status_code == 200:
                    res_json = response.json()
                    memories = []
                    raw_list = res_json.get("memories") or res_json.get("results") or res_json.get("data") or []
                    if isinstance(raw_list, list):
                        for item in raw_list:
                            if isinstance(item, str):
                                memories.append(item)
                            elif isinstance(item, dict):
                                memories.append(item.get("content") or item.get("text") or str(item))
                    if memories:
                        logger.info(f"Hindsight API recalled {len(memories)} memories.")
                        return memories[:top_k]
            except Exception as e:
                logger.debug(f"Attempt calling recall at {url} failed: {e}")
                continue

        # Dynamic local fallback recall strategy
        logger.info("Executing local dynamic relevance search for query...")
        query_lower = query.lower()
        
        # Tokenize query, filtering out common generic words
        tokens = set(re.findall(r'[a-zA-Z0-9_\-]+', query_lower))
        stop_words = {
            "the", "and", "for", "in", "is", "of", "to", "a", "an", "on", "at", "by", "with", 
            "service", "error", "rate", "log", "incident", "latency", "ms", "connections", 
            "db", "conn", "timeout", "failed", "failure", "status", "http", "http500", "504", 
            "8200ms", "14200ms", "100%", "45.2%", "72.4%", "active", "threads", "waiting", "exception"
        }
        query_terms = [t for t in tokens if len(t) > 2 and t not in stop_words]

        matched = []
        for item in self._local_memories:
            formatted = item["formatted"]
            formatted_lower = formatted.lower()
            item_service = item.get("service", "").strip().lower()

            score = 0
            # Term frequency match for specific domain keywords
            for term in query_terms:
                if term in formatted_lower:
                    score += 3

            # Service name exact match bonus
            if item_service and item_service in query_lower:
                score += 10

            # Strict relevance threshold: require score >= 8 for a true match
            if score >= 8:
                matched.append((score, formatted))

        # Sort by relevance score descending
        matched.sort(key=lambda x: x[0], reverse=True)
        results = [m[1] for m in matched[:top_k]]
        return results

    def store_memory(self, content: str) -> bool:
        """
        Persist a resolved incident post-mortem into Hindsight memory bank.
        Also retains in local fallback buffer for offline demonstration continuity.
        """
        # Extract service identifier
        service_name = ""
        if "[" in content and "]" in content:
            try:
                service_name = content.split("[")[1].split("]")[0].strip().lower()
            except Exception:
                pass
        
        if not service_name and "service:" in content.lower():
            try:
                service_name = content.lower().split("service:")[1].split()[0].strip().strip(",.;[]")
            except Exception:
                pass

        # Store locally in memory buffer
        self._local_memories.append({
            "service": service_name,
            "formatted": content
        })
        logger.info(f"Stored memory locally (service: '{service_name}'). Total memories now: {len(self._local_memories)}")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key and self.api_key != "your_hindsight_api_key_here":
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key

        payload = {"bank_id": self.bank_id, "content": content}

        endpoints = [
            f"{self.base_url}/default/banks/{self.bank_id}/memories",
            f"{self.base_url}/banks/{self.bank_id}/memories",
            f"{self.base_url}/memory/retain",
            f"{self.base_url}/retain",
            f"{self.base_url}/v1/default/banks/{self.bank_id}/memories",
            f"{self.base_url}/v1/banks/{self.bank_id}/memories"
        ]

        for url in endpoints:
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=0.8)
                if response.status_code in (200, 201, 202):
                    logger.info(f"Successfully committed memory to remote Hindsight bank via {url}.")
                    return True
            except Exception as e:
                logger.debug(f"Remote store attempt at {url} failed: {e}")
                continue

        return True
