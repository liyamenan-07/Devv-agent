from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_webhook_secret: str
    github_token: str
    google_api_key: str
    gemini_model: str = "gemini-1.5-pro"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
