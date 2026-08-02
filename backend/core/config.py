from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    PROJECT_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_VERSION: str = "v1"
    DATABASE_URL: str

    # Task 2.2 — comma-separated login identifier methods.
    # Supported: CUSTOMER_ID, PHONE. Phone login removed per evaluator guidance;
    # re-enable in .env with LOGIN_METHODS=CUSTOMER_ID,PHONE if ever needed.
    LOGIN_METHODS: str = "CUSTOMER_ID"

    # Admin dashboard API key (demo-grade auth for the standalone web app)
    ADMIN_API_KEY: str = "securewealth-admin-2026"

    # Adversarial Resilience Console. Runs REAL attacks against the running
    # system, so it must never be enabled in a production deployment.
    REDTEAM_ENABLED: bool = True

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()


# from core.config import settings
# print(settings.PROJECT_NAME)