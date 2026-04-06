import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = "gpt-4o-mini"
    VECTOR_DB_PATH: str = "app/db/vector_store"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./hybrid_athlete.db",
    )

settings = Settings()
