# ==============================================================================
# scheduler/config.py - Configuration du service
# ==============================================================================

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Configuration du service Scheduler.
    
    Charge depuis variables d'environnement ou fichier .env
    """
    
    # API Gateway (pour les appels HTTP)
    API_GATEWAY_URL: str = "http://api-gateway:8000"
    API_GATEWAY_SECRET: str = ""  # Secret header d'authentification
    SCHEDULER_SECRET: str = ""  # Secret pour endpoint cleanup
    
    # Database (optionnel, si accès direct nécessaire)
    DATABASE_URL: Optional[str] = None
    
    # Redis (optionnel, pour lock/cache)
    REDIS_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Scheduler
    SCHEDULER_TIMEZONE: str = "UTC"
    
    # Key rotation job
    KEY_ROTATION_SCHEDULE_HOUR: int = 2  # Chaque nuit à 2h UTC
    KEY_ROTATION_SCHEDULE_MINUTE: int = 0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

if not settings.SCHEDULER_SECRET:
    raise RuntimeError(
        "SCHEDULER_SECRET is not set. "
        "Define it in environment or .env file before starting the scheduler."
    )
