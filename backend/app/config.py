import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BACKEND_DIR / "app"

load_dotenv(dotenv_path=BACKEND_DIR / ".env")


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


settings = Settings()
