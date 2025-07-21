"""
Configuration settings for the NERV Geometry Engine API.

Uses Pydantic settings management for environment-based configuration
with validation and type hints.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application metadata
    app_name: str = "NERV Geometry Engine API"
    version: str = "0.1.0"
    description: str = "Industrial-grade gamified Euclidean geometry construction system"
    
    # Environment configuration
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API configuration
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: List[str] = Field(
        default=[
            "http://localhost:3000", "http://127.0.0.1:3000", 
            "http://localhost:3001", "http://127.0.0.1:3001",
            "http://localhost:8000", "http://127.0.0.1:8000",
            "http://localhost:8001", "http://127.0.0.1:8001",
            "file://*", "null"  # Allow local file access for development
        ],
        env="ALLOWED_HOSTS"
    )
    
    # Security
    secret_key: str = Field(
        default="nerv-dev-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database URLs
    database_url: str = Field(
        default="postgresql://nerv_user:nerv_password@localhost:5432/nerv",
        env="DATABASE_URL"
    )
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        env="NEO4J_URI"
    )
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="nervgeometry", env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    # Redis configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # AI Service Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # MAGI AI Assistants Configuration
    magi_melchior_model: str = Field(
        default="gpt-4", 
        env="MAGI_MELCHIOR_MODEL",
        description="Construction guidance model"
    )
    magi_balthasar_model: str = Field(
        default="claude-3-sonnet-20240229",
        env="MAGI_BALTHASAR_MODEL", 
        description="Proof verification model"
    )
    magi_casper_model: str = Field(
        default="gpt-4",
        env="MAGI_CASPER_MODEL",
        description="Pattern recognition model"
    )
    
    # Rust integration
    rust_lib_path: Optional[str] = Field(
        default=None,
        env="RUST_LIB_PATH",
        description="Path to Rust geometry library"
    )
    
    # WebSocket configuration
    websocket_max_connections: int = Field(default=100, env="WEBSOCKET_MAX_CONNECTIONS")
    websocket_ping_interval: int = Field(default=20, env="WEBSOCKET_PING_INTERVAL")
    
    # Performance settings
    worker_processes: int = Field(default=1, env="WORKER_PROCESSES")
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Development settings
    reload: bool = Field(default=True, env="RELOAD")
    
    @validator("allowed_hosts", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse comma-separated allowed hosts from environment variable."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is one of the allowed values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Ensure log level is valid."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v.upper()
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DevelopmentSettings(Settings):
    """Development-specific settings."""
    
    environment: str = "development"
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production-specific settings."""
    
    environment: str = "production" 
    debug: bool = False
    reload: bool = False
    log_level: str = "INFO"
    
    # Override defaults for production
    secret_key: str = Field(env="SECRET_KEY")  # Required in production
    allowed_hosts: List[str] = Field(env="ALLOWED_HOSTS")  # Required in production


class TestingSettings(Settings):
    """Testing-specific settings."""
    
    environment: str = "testing"
    debug: bool = True
    
    # Use in-memory/test databases
    database_url: str = "postgresql://test_user:test_pass@localhost:5433/test_nerv"
    neo4j_uri: str = "bolt://localhost:7688"  # Test Neo4j instance
    redis_url: str = "redis://localhost:6380"  # Test Redis instance


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    The settings are cached to avoid re-reading environment variables
    on every function call.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Export settings instance for easy access
settings = get_settings()