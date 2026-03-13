from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./mockflare.db"
    create_db: bool = True
    seed_data: str = ""
    dns_port: int = 10053
    dns_address: str = "0.0.0.0"
    dns_upstreams: list[str] = []  # e.g., ["8.8.8.8", "1.1.1.1"]
    nameservers: list[str] = ["ns1.mockflare.local", "ns2.mockflare.local"]


settings = Settings()
