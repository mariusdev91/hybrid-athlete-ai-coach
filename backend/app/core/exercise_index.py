import json
import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.core.vector_store import vector_store
from app.utils.normalizer import normalize_text


logger = logging.getLogger(__name__)


def load_exercises():
    with settings.EXERCISES_DB_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_text_representation(exercise):
    parts = [
        exercise["name"],
        " ".join(exercise.get("primary_muscles", [])),
        " ".join(exercise.get("secondary_muscles", [])),
        exercise.get("equipment", "") or "",
        " ".join(exercise.get("instructions", [])),
    ]
    return normalize_text(" ".join(filter(None, parts)))


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


def rebuild_vector_store(persist=True):
    exercises = load_exercises()
    texts = [build_text_representation(exercise) for exercise in exercises]
    embeddings = get_embedding_model().encode(texts, convert_to_numpy=True)

    vector_store.reset(dim=embeddings.shape[1])
    vector_store.add_many(embeddings, exercises)

    if persist:
        settings.VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
        vector_store.save(settings.VECTOR_INDEX_PATH, settings.VECTOR_METADATA_PATH)
        np.save(settings.VECTOR_EMBEDDINGS_PATH, embeddings)

    return vector_store.count


def bootstrap_vector_store():
    status = {
        "ready": False,
        "count": vector_store.count,
        "source": "uninitialized",
    }

    try:
        if vector_store.load(settings.VECTOR_INDEX_PATH, settings.VECTOR_METADATA_PATH):
            status.update(
                ready=vector_store.is_ready,
                count=vector_store.count,
                source="disk",
            )
            return status

        if settings.EXERCISES_DB_PATH.exists():
            count = rebuild_vector_store(persist=True)
            status.update(ready=True, count=count, source="generated")
            return status

        status.update(source="missing-exercises-db")
        return status
    except Exception as exc:
        logger.exception("Vector store bootstrap failed.")
        status.update(source="error", error=str(exc))
        return status
