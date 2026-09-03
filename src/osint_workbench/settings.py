from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OSINT_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://osint:osint@postgres:5432/osint"
    redis_url: str = "redis://redis:6379/0"
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me"
    bind_host: str = "127.0.0.1"
    bind_port: int = 8088
