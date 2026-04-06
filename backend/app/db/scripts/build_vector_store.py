import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss


BASE_DIR = Path(__file__).resolve().parent.parent
EXERCISES_FILE = BASE_DIR / "exercises.json"
VECTOR_DIR = BASE_DIR / "vector_store"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_exercises():
    with open(EXERCISES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_text_representation(ex):
    parts = [
        ex["name"],
        " ".join(ex.get("primary_muscles", [])),
        " ".join(ex.get("secondary_muscles", [])),
        ex.get("equipment", "") or "",
        " ".join(ex.get("instructions", [])),
    ]
    return " ".join(parts)


def build_vector_store():
    VECTOR_DIR.mkdir(exist_ok=True)

    exercises = load_exercises()
    model = SentenceTransformer(MODEL_NAME)

    texts = [build_text_representation(ex) for ex in exercises]
    embeddings = model.encode(texts, convert_to_numpy=True)

    # Save embeddings
    np.save(VECTOR_DIR / "embeddings.npy", embeddings)

    # Save metadata
    with open(VECTOR_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(exercises, f, indent=2, ensure_ascii=False)

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, str(VECTOR_DIR / "index.faiss"))

    print(f"Vector store built successfully → {VECTOR_DIR}")


if __name__ == "__main__":
    build_vector_store()
