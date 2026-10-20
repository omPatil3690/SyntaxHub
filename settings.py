"""
Single source of truth for environment configuration, shared by every
service. Import `settings` rather than reading os.environ directly
anywhere else in the codebase.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    # --- Database / cache ---
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://syntaxhub:syntaxhub@localhost:5432/syntaxhub",
        )
    )
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    # --- Embeddings (Phase 1/2) ---
    embedding_provider: str = field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "fake"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    embedding_dim: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIM", "1536")))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))

    # --- LLM router (Phase 8) ---
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "template"))
    # "template" = deterministic, rule-based patch generation, no API key, no network.
    # "openai"   = real LLM calls for cases the template engine doesn't cover.
    cheap_model: str = field(default_factory=lambda: os.getenv("CHEAP_MODEL", "gpt-4o-mini"))
    strong_model: str = field(default_factory=lambda: os.getenv("STRONG_MODEL", "gpt-4o"))

    # --- Ingestion (Phase 1) ---
    chunk_target_tokens: int = field(default_factory=lambda: int(os.getenv("CHUNK_TARGET_TOKENS", "400")))
    chunk_overlap_tokens: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP_TOKENS", "60")))
    request_timeout_s: float = field(default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT_S", "20")))
    crawl_concurrency: int = field(default_factory=lambda: int(os.getenv("CRAWL_CONCURRENCY", "5")))
    user_agent: str = "SyntaxHub-Ingestion/0.2 (+https://syntaxhub.dev)"

    # --- Repository scanning (Phase 5) ---
    clone_dir: str = field(default_factory=lambda: os.getenv("CLONE_DIR", "/tmp/syntaxhub_repos"))
    max_files_scanned: int = field(default_factory=lambda: int(os.getenv("MAX_FILES_SCANNED", "3000")))

    # --- Verification (Phase 9) ---
    verification_backend: str = field(default_factory=lambda: os.getenv("VERIFICATION_BACKEND", "local"))
    # "local"  = run node/npm or python syntax checks directly on the host (no Docker needed;
    #            this is what's used in this repo's own tests, and is fine for local dev).
    # "docker" = build an isolated container per migration run (real prod setting; needs Docker).
    max_repair_attempts: int = field(default_factory=lambda: int(os.getenv("MAX_REPAIR_ATTEMPTS", "3")))

    # --- GitHub integration (Phase 10) ---
    github_webhook_secret: str | None = field(default_factory=lambda: os.getenv("GITHUB_WEBHOOK_SECRET"))
    github_app_id: str | None = field(default_factory=lambda: os.getenv("GITHUB_APP_ID"))


settings = Settings()
