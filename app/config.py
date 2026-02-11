from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./mockflare.db"
    create_db: bool = True
    seed_data: str = ""


settings = Settings()
