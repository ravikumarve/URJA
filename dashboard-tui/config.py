import os


class Settings:
    API_URL: str = os.getenv("URJA_API_URL", "http://localhost:8000/api/v1")
    POLL_INTERVAL: int = int(os.getenv("URJA_POLL_INTERVAL", "5"))


settings = Settings()
