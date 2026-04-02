from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Finance Dashboard API"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str

    model_config = {"env_file": ".env"}


settings = Settings()
