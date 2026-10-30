"""
Configuration manager for AI-Powered Smart Campus Issue Management System.
Loads environment variables and provides centralized settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file if present
load_dotenv(BASE_DIR / ".env")


class Config:
    """Central configuration class."""

    BASE_DIR: Path = BASE_DIR

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "smart_campus")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # AWS Bedrock
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID: str = os.getenv(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"
    )
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AI_ENABLED: bool = os.getenv("AI_ENABLED", "false").lower() in ("true", "1", "yes")

    # Application Settings
    APP_SECRET_KEY: str = os.getenv(
        "APP_SECRET_KEY", "smartcampus-btech-dbms-secret-key-2026"
    )
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))

    @classmethod
    def get_db_uri(cls) -> str:
        """Returns SQLAlchemy MySQL connection URI."""
        return (
            f"mysql+mysqlconnector://{cls.DB_USER}:{cls.DB_PASSWORD}@"
            f"{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )

    @classmethod
    def is_ai_configured(cls) -> bool:
        """Check if AWS Bedrock credentials and flag are present."""
        if not cls.AI_ENABLED:
            return False
        # If IAM role or AWS CLI credentials are used, access key might be optional,
        # but region and model ID are always required.
        return bool(cls.AWS_REGION and cls.BEDROCK_MODEL_ID)


# Ensure upload directory exists
Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
