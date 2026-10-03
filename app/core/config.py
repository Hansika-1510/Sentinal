from typing import List, Optional
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
