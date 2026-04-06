import json
import numpy as np
import faiss
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "db" / "vector_store"


class ExerciseVectorStore:
    def __init__(self):
        self.embeddings = np.load(BASE_DIR / "embeddings.npy")
        self.index = faiss.read_index(str(BASE_DIR / "index.faiss"))

        with open(BASE_DIR / "metadata.json", "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def search(self, embedding, k=5):
        distances, indices = self.index.search(embedding, k)
        results = []
        for idx in indices[0]:
            results.append(self.metadata[idx])
        return results


vector_store = ExerciseVectorStore()
