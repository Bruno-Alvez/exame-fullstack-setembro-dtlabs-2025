from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DeviceWatch"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql://devicewatch:devicewatch123@localhost:5432/devicewatch"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Device Simulator
    SIMULATOR_DEVICE_COUNT: int = 10
    SIMULATOR_FAILURE_RATE: float = 0.05
    SIMULATOR_SCENARIO: str = "mixed"
    
    # Health Scoring Weights
    HEALTH_CPU_WEIGHT: float = 0.25
    HEALTH_RAM_WEIGHT: float = 0.25
    HEALTH_TEMP_WEIGHT: float = 0.30
    HEALTH_DISK_WEIGHT: float = 0.15
    HEALTH_CONNECTIVITY_WEIGHT: float = 0.05
    
    # Alert Settings
    ALERT_DEFAULT_DURATION_MINUTES: int = 5
    ALERT_MAX_CONDITIONS: int = 5
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Environment-specific overrides
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1",
        "devicewatch.local",
        "*.devicewatch.local"
    ]
elif settings.ENVIRONMENT == "testing":
    settings.DATABASE_URL = "postgresql://devicewatch:devicewatch123@localhost:5432/devicewatch_test"
    settings.REDIS_URL = "redis://localhost:6379/1"

