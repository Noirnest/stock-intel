
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"

    # Auth
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://stock_intel:stock_intel_dev@localhost:5432/stock_intel"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # SEC EDGAR (compliant access)
    SEC_USER_AGENT_APP: str = "StockIntelDashboard/1.0"
    SEC_USER_AGENT_EMAIL: str = "dev@example.com"
    SEC_RATE_LIMIT_PER_SECOND: int = 8

    # Provider selection
    NEWS_PROVIDER: str = "mock"
    NEWS_API_KEY: str = ""
    ANALYST_PROVIDER: str = "mock"
    ANALYST_API_KEY: str = ""
    PRICE_PROVIDER: str = "mock"
    PRICE_API_KEY: str = ""

    # Alerts
    SLACK_WEBHOOK_URL: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    @property
    def sec_user_agent(self) -> str:
        return f"{self.SEC_USER_AGENT_APP} contact:{self.SEC_USER_AGENT_EMAIL}"


settings = Settings()
