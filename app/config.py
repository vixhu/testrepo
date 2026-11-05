from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    access_secret: str
    temp_secret: str
    refresh_secret: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    reset_token_expire_minutes: int
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    email_from_name: str = "Indication Instruments"
    docs_enabled: bool = False
    trust_proxy: bool = True
    cors_origins: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()