from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = False
    DATABASE_URL: str
    SECRET_KEY: str = "test-secret-key-for-testing"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    GOOGLE_CLIENT_ID: str = "test-google-client-id"
    GOOGLE_CLIENT_SECRET: str = "test-google-client-secret"

    APPLE_CLIENT_ID: str = "test-apple-client-id"
    APPLE_TEAM_ID: str = "test-apple-team-id"
    APPLE_KEY_ID: str = "test-apple-key-id"

    IP_API_KEY: str = "test-ip-api-key"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
