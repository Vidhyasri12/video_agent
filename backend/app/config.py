import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI CCTV Video Intelligence & Summarization System"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000
    SECRET_KEY: str = "super-secret-jwt-key-change-in-production"
    ENVIRONMENT: str = "production"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cctv_intelligence"
    DATABASE_URL: Optional[str] = None

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    # Vector Search
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # VLM & Detection Config
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.45
    CAPTION_INTERVAL_SECONDS: int = 10
    STORAGE_DIR: str = "./storage"

    # NVIDIA VSS Agent Configuration
    NVIDIA_API_KEY: str = ""
    NVIDIA_VSS_URL: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    NVIDIA_VSS_MODEL: str = "meta/llama-3.2-11b-vision-instruct"

    # Camera & VMS Provider Settings
    CAMERA_PROVIDER: str = "vigi"
    CONNECTION_TYPE: str = "local_vms"  # local_vms, vigi_nvr, standalone_camera, cloud_api
    
    # Feature Flags
    ENABLE_EXPERIMENTAL_CLOUD_APIS: bool = True
    ENABLE_MOCK_PROVIDER: bool = False

    # TP-Link VIGI & Cloudflare Tunnel Settings
    VIGI_VMS_HOST: str = "127.0.0.1"
    VIGI_VMS_PORT: int = 8554
    VIGI_VMS_USERNAME: str = "admin"
    VIGI_VMS_PASSWORD: str = "Gt@102020"
    VIGI_VMS_RTSP_URL: str = "rtsp://admin:Gt%40102020@127.0.0.1:8554/live/1/1/avm"
    CLOUDFLARE_HOSTNAME: str = "nvr1.goodwindco.in"

    RTSP_CONNECT_TIMEOUT: float = 5.0
    MAX_AUTH_RETRIES: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_sanitized_config(self) -> Dict[str, Any]:
        """Returns safe configuration dictionary redacting sensitive passwords and tokens."""
        return {
            "project_name": self.PROJECT_NAME,
            "environment": self.ENVIRONMENT,
            "camera_provider": self.CAMERA_PROVIDER,
            "connection_type": self.CONNECTION_TYPE,
            "vigi_vms_host": self.VIGI_VMS_HOST,
            "vigi_vms_port": self.VIGI_VMS_PORT,
            "vigi_vms_username": self.VIGI_VMS_USERNAME,
            "vigi_vms_password_set": bool(self.VIGI_VMS_PASSWORD),
            "vigi_vms_rtsp_url_configured": bool(self.VIGI_VMS_RTSP_URL),
            "cloudflare_hostname": self.CLOUDFLARE_HOSTNAME,
            "enable_experimental_cloud_apis": self.ENABLE_EXPERIMENTAL_CLOUD_APIS,
            "enable_mock_provider": self.ENABLE_MOCK_PROVIDER
        }

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_sync_database_url(self) -> str:
        url = self.get_database_url()
        return url.replace("postgresql+asyncpg://", "postgresql://")

    def get_redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

settings = Settings()
