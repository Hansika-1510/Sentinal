import asyncio
import json
import math
import random
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LLMIntegrationException


class LLMProvider(ABC):
    @abstractmethod
    async def generate_structured(self, prompt: str, schema_class: Type[BaseModel], system_prompt: Optional[str] = None) -> BaseModel:
        """Generates structured output strictly validated against a Pydantic schema."""
        pass

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates text output."""
        pass


class EmbeddingProvider(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Generates embedding vector for text."""
        pass


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM provider for local development, tests, and offline hackathon demos."""
    
    async def generate_structured(self, prompt: str, schema_class: Type[BaseModel], system_prompt: Optional[str] = None) -> BaseModel:
        logger.info(f"MockLLM generating structured response for schema {schema_class.__name__}")
        
        prompt_lower = prompt.lower()
        
        if "postmortem" in prompt_lower or "postmortem" in schema_class.__name__.lower():
            data = {
                "incident_id": "INC-DEMO-01",
                "title": "Payment Service Outage due to Database Connection Pool Starvation",
                "service": "payment-service",
                "severity": "CRITICAL",
                "duration_minutes": 14.5,
                "summary": "Payment Service encountered an outage following deployment v1.8.3 due to an undersized DB connection pool.",
                "impact": {
                    "affected_users": 120,
                    "failed_transactions": 34,
                    "error_rate_peak_percent": 88.0
                },
                "timeline": [
                    {"time": "15:00:00", "event": "Deployment v1.8.3 deployed to production", "is_observed": True},
                    {"time": "15:01:20", "event": "Sentinel detected HTTP 500 error spike (18 errors in 60s)", "is_observed": True},
                    {"time": "15:01:45", "event": "Investigator Agent identified DB connection pool regression", "is_observed": False},
                    {"time": "15:03:10", "event": "Response Planner proposed rollback action ACT-ROLLBACK", "is_observed": False},
                    {"time": "15:04:00", "event": "Human operator approved rollback action", "is_observed": True},
                    {"time": "15:05:30", "event": "Remediation executor rolled back to v1.8.2", "is_observed": True},
                    {"time": "15:10:00", "event": "Sentinel verified recovery: 0 errors and health check 200 OK", "is_observed": True},
                    {"time": "15:14:30", "event": "Incident marked RESOLVED", "is_observed": True}
                ],
                "root_cause": "Configuration change in DatabasePool.java in commit a1b2c3d reduced maxPoolSize from 50 to 2.",
                "contributing_factors": [
                    "Lack of automated load testing in staging environment for connection pool bounds",
                    "CodeGuard warning was not set to block level before deployment"
                ],
                "detection_method": "Sentinel automated anomaly detection (HTTP_500_SPIKE rule)",
                "actions_taken": [
                    {"action": "ROLLBACK", "target": "payment-service v1.8.2", "result": "SUCCESS"}
                ],
                "recovery_verification": {
                    "status": "VERIFIED",
                    "error_rate_after": 0.0,
                    "health_check_status": "HEALTHY",
                    "monitoring_window_seconds": 120
                },
                "lessons_learned": [
                    "Connection pool settings must have strict minimum bound validation in CI/CD pipeline",
                    "Pre-deployment synthetic load test should verify connection acquisition under concurrency"
                ],
                "preventive_recommendations": [
                    "Add CodeGuard lint rule to BLOCK PRs that reduce connection pool limits below 20",
                    "Add Prometheus alert for HikariCP active connection saturation > 80%"
                ]
            }
            return schema_class.model_validate(data)

        if "investigation" in prompt_lower or "root cause" in prompt_lower or "rca" in schema_class.__name__.lower():
            is_payment = "payment" in prompt_lower or "pool" in prompt_lower or "timeout" in prompt_lower or "500" in prompt_lower
            
            if is_payment:
                data = {
                    "summary": "Payment Service encountered high HTTP 500 error rates immediately following deployment v1.8.3 due to database connection pool starvation.",
                    "primary_hypothesis": {
                        "cause": "Database connection pool max limit misconfigured from 50 to 2 in deployment v1.8.3, causing connection timeouts under normal traffic.",
                        "confidence": "HIGH",
                        "explanation": "Runtime logs indicate pool acquisition timeout exceptions at DatabasePool.java:48, exactly coinciding with commit a1b2c3d.",
                        "evidence": [
                            {
                                "type": "deployment",
                                "reference": "v1.8.3",
                                "explanation": "Deployment v1.8.3 was deployed 3 minutes prior to error spike.",
                                "is_observed": True
                            },
                            {
                                "type": "code_review",
                                "reference": "CR-DB-POOL",
                                "explanation": "CodeGuard flagged pool max size change with severity HIGH.",
                                "is_observed": True
                            },
                            {
                                "type": "log",
                                "reference": "ERR-POOL-TIMEOUT",
                                "explanation": "Observed 18 ConnectionTimeoutException logs across worker nodes.",
                                "is_observed": True
                            }
                        ],
                        "contradicting_evidence": []
                    },
                    "alternative_hypotheses": [
                        {
                            "cause": "Upstream Stripe API outage causing gateway timeouts.",
                            "confidence": "LOW",
                            "explanation": "External status checks for payment processor are nominal, making third-party outage unlikely.",
                            "evidence": [],
                            "contradicting_evidence": [
                                {
                                    "type": "health_check",
                                    "reference": "STRIPE-STATUS-200",
                                    "explanation": "External Stripe ping response returned 200 OK.",
                                    "is_observed": True
                                }
                            ]
                        }
                    ],
                    "affected_services": ["payment-service", "order-service", "api-gateway"],
                    "blast_radius": {
                        "failing_service": "payment-service",
                        "direct_impact": [
                            {
                                "service_name": "payment-service",
                                "impact_type": "DIRECT",
                                "affected_features": ["Checkout Payment API", "Subscription Renewal"],
                                "affected_user_journeys": ["User checkout flow", "Merchant billing"],
                                "database_dependencies": ["payment_db (PostgreSQL)"],
                                "external_api_dependencies": ["Stripe API"]
                            }
                        ],
                        "downstream_impact": [
                            {
                                "service_name": "order-service",
                                "impact_type": "DOWNSTREAM",
                                "affected_features": ["Order Finalization"],
                                "affected_user_journeys": ["Order Placement"],
                                "database_dependencies": [],
                                "external_api_dependencies": []
                            }
                        ],
                        "total_affected_services": 2,
                        "critical_user_journeys_impacted": ["User checkout flow", "Order Placement"]
                    },
                    "fix_guidance": {
                        "repository": "payment-service-repo",
                        "file": "src/main/java/com/company/payment/config/DatabasePool.java",
                        "line_start": 42,
                        "line_end": 48,
                        "problem": "Connection pool maximum size was reduced to 2 with 1000ms acquisition timeout.",
                        "why": "Concurrent requests exhaust all available pool connections within 10ms, causing incoming threads to throw ConnectionTimeoutException.",
                        "recommended_change": "Restore maxPoolSize to 50 and set connectionTimeout to 30000ms. Implement connection pool monitoring metrics.",
                        "expected_behavior": "Payment requests will acquire DB connections under 5ms, eliminating 500 status codes.",
                        "evidence": [
                            {
                                "type": "commit",
                                "reference": "a1b2c3d",
                                "explanation": "Diff in commit a1b2c3d altered maxPoolSize = 2.",
                                "is_observed": True
                            }
                        ],
                        "confidence": "HIGH",
                        "validation_steps": [
                            "Run integration test suite with 50 concurrent checkout requests.",
                            "Verify HikariCP connection pool metrics dashboard.",
                            "Run 'devguard review-staged' before committing."
                        ],
                        "disclaimer": "AI Fix Advisor provides developer guidance only. Source code modifications must be implemented manually by developers and verified via CodeGuard."
                    },
                    "recommended_actions": [
                        {
                            "type": "ROLLBACK",
                            "risk_level": "MEDIUM",
                            "reason": "Immediate mitigation: Roll back payment-service deployment v1.8.3 to previous healthy version v1.8.2.",
                            "expected_impact": "Estimated impact: Restores connection pool capacity immediately and clears 500 error spike (AI-assisted assessment).",
                            "possible_side_effects": ["Temporary 2-second connection drop during pod rollout"],
                            "rollback_path": "Re-deploy v1.8.3 if rollback fails.",
                            "requires_approval": True,
                            "evidence": [
                                {
                                    "type": "deployment",
                                    "reference": "v1.8.3",
                                    "explanation": "Regression introduced in v1.8.3",
                                    "is_observed": True
                                }
                            ]
                        },
                        {
                            "type": "RESTART_SERVICE",
                            "risk_level": "LOW",
                            "reason": "Restart pods to temporarily flush stalled pool connections.",
                            "expected_impact": "Estimated impact: Temporary 30s relief until pool is saturated again.",
                            "possible_side_effects": ["Brief request queueing"],
                            "rollback_path": "None needed.",
                            "requires_approval": False,
                            "evidence": []
                        }
                    ]
                }
            else:
                data = {
                    "summary": "Service anomaly detected based on runtime error events.",
                    "primary_hypothesis": {
                        "cause": "Service runtime fault or configuration anomaly.",
                        "confidence": "MEDIUM",
                        "explanation": "Observed error logs matching error pattern.",
                        "evidence": [
                            {
                                "type": "log",
                                "reference": "LOG-ERR-GENERIC",
                                "explanation": "Runtime logs indicate elevated error rate.",
                                "is_observed": True
                            }
                        ],
                        "contradicting_evidence": []
                    },
                    "alternative_hypotheses": [],
                    "affected_services": ["auth-service"],
                    "blast_radius": {
                        "failing_service": "auth-service",
                        "direct_impact": [],
                        "downstream_impact": [],
                        "total_affected_services": 1,
                        "critical_user_journeys_impacted": ["User Login"]
                    },
                    "fix_guidance": None,
                    "recommended_actions": [
                        {
                            "type": "RESTART_SERVICE",
                            "risk_level": "LOW",
                            "reason": "Restart service instance to recover from transient deadlock.",
                            "expected_impact": "Restores service operation.",
                            "possible_side_effects": [],
                            "rollback_path": "No rollback required.",
                            "requires_approval": False,
                            "evidence": []
                        }
                    ]
                }
            return schema_class.model_validate(data)

        if "postmortem" in prompt_lower or "postmortem" in schema_class.__name__.lower():
            data = {
                "incident_id": "INC-DEMO-01",
                "title": "Payment Service Outage due to Database Connection Pool Starvation",
                "service": "payment-service",
                "severity": "CRITICAL",
                "duration_minutes": 14.5,
                "summary": "Payment Service encountered an outage following deployment v1.8.3 due to an undersized DB connection pool.",
                "impact": {
                    "affected_users": 120,
                    "failed_transactions": 34,
                    "error_rate_peak_percent": 88.0
                },
                "timeline": [
                    {"time": "15:00:00", "event": "Deployment v1.8.3 deployed to production", "is_observed": True},
                    {"time": "15:01:20", "event": "Sentinel detected HTTP 500 error spike (18 errors in 60s)", "is_observed": True},
                    {"time": "15:01:45", "event": "Investigator Agent identified DB connection pool regression", "is_observed": False},
                    {"time": "15:03:10", "event": "Response Planner proposed rollback action ACT-ROLLBACK", "is_observed": False},
                    {"time": "15:04:00", "event": "Human operator approved rollback action", "is_observed": True},
                    {"time": "15:05:30", "event": "Remediation executor rolled back to v1.8.2", "is_observed": True},
                    {"time": "15:10:00", "event": "Sentinel verified recovery: 0 errors and health check 200 OK", "is_observed": True},
                    {"time": "15:14:30", "event": "Incident marked RESOLVED", "is_observed": True}
                ],
                "root_cause": "Configuration change in DatabasePool.java in commit a1b2c3d reduced maxPoolSize from 50 to 2.",
                "contributing_factors": [
                    "Lack of automated load testing in staging environment for connection pool bounds",
                    "CodeGuard warning was not set to block level before deployment"
                ],
                "detection_method": "Sentinel automated anomaly detection (HTTP_500_SPIKE rule)",
                "actions_taken": [
                    {"action": "ROLLBACK", "target": "payment-service v1.8.2", "result": "SUCCESS"}
                ],
                "recovery_verification": {
                    "status": "VERIFIED",
                    "error_rate_after": 0.0,
                    "health_check_status": "HEALTHY",
                    "monitoring_window_seconds": 120
                },
                "lessons_learned": [
                    "Connection pool settings must have strict minimum bound validation in CI/CD pipeline",
                    "Pre-deployment synthetic load test should verify connection acquisition under concurrency"
                ],
                "preventive_recommendations": [
                    "Add CodeGuard lint rule to BLOCK PRs that reduce connection pool limits below 20",
                    "Add Prometheus alert for HikariCP active connection saturation > 80%"
                ]
            }
            return schema_class.model_validate(data)

        # Generic fallback instance if any other schema is requested
        return schema_class()

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "Mock LLM text generation response."


class OpenRouterLLMProvider(LLMProvider):
    # Statuses worth retrying: 429 is rate limiting (a retry is the whole fix), the 5xx set
    # is provider-side flakiness. Everything else is a request bug that retrying would repeat.
    RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet", base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    @staticmethod
    def _retry_delay(attempt: int, response: Optional[httpx.Response] = None) -> float:
        """Exponential backoff with jitter, bounded by config. Honours Retry-After when sent."""
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return max(0.0, min(float(retry_after), settings.LLM_RETRY_MAX_DELAY_SECONDS))
                except ValueError:
                    pass
        base = settings.LLM_RETRY_BASE_DELAY_SECONDS * (2 ** attempt)
        return min(base + random.uniform(0, base / 2), settings.LLM_RETRY_MAX_DELAY_SECONDS)

    async def _post(self, client: httpx.AsyncClient, url: str, payload: dict, headers: dict) -> httpx.Response:
        """POST with bounded retries on rate limiting, transient 5xx, and timeouts.

        The autonomous pipeline treats an investigation failure as non-fatal, so an
        unretried 429 surfaces to the operator as an incident with no RCA. Retries are
        bounded so a bad provider still fails fast rather than hanging the ingest request.
        """
        attempts = max(1, settings.LLM_MAX_ATTEMPTS)
        for attempt in range(attempts):
            is_last = attempt >= attempts - 1
            try:
                response = await client.post(url, json=payload, headers=headers)
            except httpx.TransportError:
                # TransportError already covers TimeoutException (it is a subclass), so it
                # is the only name needed here: connect errors, read timeouts, protocol
                # errors, and pool exhaustion all arrive through this one base class.
                if is_last:
                    raise
                delay = self._retry_delay(attempt)
                logger.warning(
                    f"OpenRouter request failed to connect; retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{attempts})"
                )
                await asyncio.sleep(delay)
                continue

            if response.status_code in self.RETRYABLE_STATUSES and not is_last:
                delay = self._retry_delay(attempt, response)
                logger.warning(
                    f"OpenRouter returned {response.status_code}; retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{attempts})"
                )
                await asyncio.sleep(delay)
                continue

            return response

        raise LLMIntegrationException("LLM request failed after exhausting retries")  # pragma: no cover

    async def generate_structured(self, prompt: str, schema_class: Type[BaseModel], system_prompt: Optional[str] = None) -> BaseModel:
        schema_json = json.dumps(schema_class.model_json_schema(), indent=2)
        sys_prompt = (system_prompt or "") + f"\n\nYou MUST return a single JSON object conforming strictly to this JSON Schema:\n{schema_json}\nDo not include any explanation or markdown formatting other than pure JSON."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://incident-agent.local",
            "X-Title": "AI Software Incident Response Agent"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": settings.LLM_MAX_TOKENS
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await self._post(client, f"{self.base_url}/chat/completions", payload, headers)
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]
                content = choice["message"].get("content")
                if not content:
                    # Reasoning models return content=None when max_tokens is exhausted by
                    # the reasoning pass, so name the cause rather than failing on json.loads.
                    raise LLMIntegrationException(
                        f"LLM returned no content (finish_reason={choice.get('finish_reason')!r}); "
                        f"the response was likely truncated by max_tokens={settings.LLM_MAX_TOKENS}"
                    )
                try:
                    parsed_json = json.loads(content)
                except json.JSONDecodeError as e:
                    raise LLMIntegrationException(
                        f"LLM returned unparseable JSON (finish_reason={choice.get('finish_reason')!r}): {e}"
                    )
                return schema_class.model_validate(parsed_json)
            except Exception as e:
                logger.error(f"OpenRouter LLM request failed: {str(e)}", exc_info=True)
                raise LLMIntegrationException(str(e))

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "messages": messages, "max_tokens": settings.LLM_MAX_TOKENS}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await self._post(client, f"{self.base_url}/chat/completions", payload, headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                raise LLMIntegrationException(str(e))


class OllamaLLMProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model

    async def generate_structured(self, prompt: str, schema_class: Type[BaseModel], system_prompt: Optional[str] = None) -> BaseModel:
        schema_json = json.dumps(schema_class.model_json_schema())
        sys_prompt = (system_prompt or "") + f"\nRespond in JSON conforming to schema: {schema_json}"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": sys_prompt,
            "format": "json",
            "stream": False
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                parsed = json.loads(data.get("response", "{}"))
                return schema_class.model_validate(parsed)
            except Exception as e:
                logger.error(f"Ollama structured generation error: {str(e)}")
                raise LLMIntegrationException(str(e))

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                return resp.json().get("response", "")
            except Exception as e:
                raise LLMIntegrationException(str(e))


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """
    Computes a deterministic normalized 128-dimensional embedding vector for any string text.
    Provides reliable, zero-dependency cosine similarity search for historical incidents.
    """
    async def get_embedding(self, text: str) -> List[float]:
        import hashlib
        dim = 128
        vec = [0.0] * dim
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            for i in range(dim):
                bit = (h >> (i % 64)) & 1
                vec[i] += 1.0 if bit else -0.5

        # Normalize L2 norm
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))


def get_llm_provider() -> LLMProvider:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openrouter" and settings.OPENROUTER_API_KEY:
        return OpenRouterLLMProvider(
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.OPENROUTER_MODEL,
            base_url=settings.OPENROUTER_BASE_URL
        )
    elif provider == "ollama":
        return OllamaLLMProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL
        )
    return MockLLMProvider()


def get_embedding_provider() -> EmbeddingProvider:
    return DeterministicEmbeddingProvider()
