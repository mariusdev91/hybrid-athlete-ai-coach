import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BACKEND_DIR / "app"

load_dotenv(dotenv_path=BACKEND_DIR / ".env")


def parse_csv_env(value: str, default: list[str]) -> list[str]:
    if not value:
        return default

    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    EXERCISES_DB_PATH: Path = APP_DIR / "db" / "exercises.json"
    VECTOR_DB_PATH: Path = APP_DIR / "db" / "vector_store"
    VECTOR_INDEX_PATH: Path = VECTOR_DB_PATH / "index.faiss"
    VECTOR_METADATA_PATH: Path = VECTOR_DB_PATH / "metadata.json"
    VECTOR_EMBEDDINGS_PATH: Path = VECTOR_DB_PATH / "embeddings.npy"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./hybrid_athlete.db",
    )
    CORS_ALLOWED_ORIGINS: list[str] = parse_csv_env(
        os.getenv("CORS_ALLOWED_ORIGINS", ""),
        [
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
    )
    CORS_ALLOWED_ORIGIN_REGEX: str = os.getenv(
        "CORS_ALLOWED_ORIGIN_REGEX",
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    )


settings = Settings()
