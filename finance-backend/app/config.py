from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Finance Dashboard API"
    secret_key: str = "change-this-in-production-use-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./finance.db"

    class Config:
        env_file = ".env"


settings = Settings()
