from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "AI Software Incident Response Agent"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./incident_response.db"
    REDIS_URL: Optional[str] = None

    # LLM & Robin Settings
    LLM_PROVIDER: str = "mock"  # "openrouter", "ollama", "mock"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = "https://openrouter.ai/api/v1"
    LLM_MODEL: Optional[str] = "openrouter/free"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # LLM request resilience. Free tiers answer 429 before the model ever runs, and because
    # the autonomous pipeline swallows investigation failures, one 429 would otherwise leave
    # an incident with no RCA. Retries are bounded so ingest latency stays predictable.
    # The token budget must clear the reasoning tokens a reasoning model spends internally
    # before it emits any JSON: the RCA schema alone is ~10k characters, and at a 4096 cap
    # the model spent 3712 on reasoning and returned a truncated object.
    LLM_MAX_TOKENS: int = Field(default=16000, ge=1024)
    # Total attempts per request, including the first one (not "retries after the first").
    # Bounded below by 1: zero attempts would raise before ever making a request.
    LLM_MAX_ATTEMPTS: int = Field(default=4, ge=1)
    LLM_RETRY_BASE_DELAY_SECONDS: float = Field(default=1.0, ge=0)
    LLM_RETRY_MAX_DELAY_SECONDS: float = Field(default=20.0, gt=0)

    # External Integrations
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    ROBIN_REVIEW_URL: Optional[str] = None
    ROBIN_REVIEW_API_KEY: Optional[str] = None

    # Incident Thresholds & Anomaly Rules
    HTTP_500_ERROR_THRESHOLD: int = 5
    HTTP_500_WINDOW_SECONDS: int = 60
    ERROR_RATE_THRESHOLD_PERCENT: float = 20.0
    DEPLOYMENT_ANOMALY_WINDOW_SECONDS: int = 600  # 10 minutes
    HEALTH_CHECK_FAILURE_CONSECUTIVE: int = 2

    # Autonomous Closed-Loop Pipeline
    # Sentinel detects automatically; these control whether the stages after it also run
    # without a human clicking "investigate". Execution still always requires approval.
    AUTO_INVESTIGATE_ON_INCIDENT: bool = True
    # Severity gate for auto-investigation. Severity is deterministic and known before any
    # LLM call, so this caps spend. Rows are compared upper-cased.
    AUTO_INVESTIGATE_SEVERITIES: List[str] = ["HIGH", "CRITICAL"]
    AUTO_PROPOSE_REMEDIATION: bool = True
    # Overall ceiling for one autonomous run, covering every LLM call plus its retry
    # budget. Individual calls are bounded on their own, but the total can otherwise run
    # into minutes and hold the ingest request open. On timeout the incident is left
    # DETECTED for manual triage rather than being silently half-investigated.
    # Must be positive: a zero or negative ceiling would time out before the run starts.
    AUTO_RESPONSE_TIMEOUT_SECONDS: float = Field(default=120.0, gt=0)

    # Operational Action Execution Allowlist
    ALLOWED_OPERATIONAL_ACTIONS: List[str] = [
        "rollback_deployment",
        "restart_service",
        "disable_feature_flag",
        "scale_replicas",
        "clear_cache",
        "switch_traffic_routing"
    ]

    # Redaction Keys
    SENSITIVE_KEY_PATTERNS: List[str] = [
        "token", "secret", "password", "api_key", "authorization", "bearer"
    ]


settings = Settings()
