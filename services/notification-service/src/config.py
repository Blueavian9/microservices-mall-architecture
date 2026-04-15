from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    nats_url: str = "nats://nats:4222"

    class Config:
        env_file = ".env"

settings = Settings()
