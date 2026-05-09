from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    DATABASE_URL: str = "postgresql+asyncpg://stock_intel:stock_intel_dev@localhost:5432/stock_intel"
    REDIS_URL: str = "redis://localhost:6379/0"
    SEC_USER_AGENT_APP: str = "StockIntelDashboard/1.0"
    SEC_USER_AGENT_EMAIL: str = "dev@example.com"
    SEC_RATE_LIMIT_PER_SECOND: int = 8
    NEWS_PROVIDER: str = "mock"
    NEWS_API_KEY: str = ""
    ANALYST_PROVIDER: str = "mock"
    ANALYST_API_KEY: str = ""
    PRICE_PROVIDER: str = "mock"
    PRICE_API_KEY: str = ""
    SLACK_WEBHOOK_URL: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    @property
    def sec_user_agent(self) -> str:
        return f"{self.SEC_USER_AGENT_APP} contact:{self.SEC_USER_AGENT_EMAIL}"

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if "postgresql://" in url and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        return url

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")


settings = Settings()
