import json

import faiss
import numpy as np


class VectorStore:
    def __init__(self, dim=384):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadata = []

    @property
    def count(self):
        return len(self.metadata)

    @property
    def is_ready(self):
        return self.index.ntotal > 0 and self.index.ntotal == len(self.metadata)

    def reset(self, dim=None):
        if dim is not None:
            self.dim = dim
        self.index = faiss.IndexFlatL2(self.dim)
        self.metadata = []

    def _coerce_embedding(self, embedding):
        if isinstance(embedding, list):
            embedding = np.asarray(embedding, dtype="float32")
        elif not isinstance(embedding, np.ndarray):
            embedding = np.asarray(embedding, dtype="float32")

        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)

        return embedding.astype("float32")

    def add(self, embedding, metadata):
        embedding = self._coerce_embedding(embedding)
        self.index.add(embedding)
        self.metadata.append(metadata)

    def add_many(self, embeddings, metadata_items):
        embeddings = self._coerce_embedding(embeddings)
        self.index.add(embeddings)
        self.metadata.extend(metadata_items)

    def load(self, index_path, metadata_path):
        if not index_path.exists() or not metadata_path.exists():
            return False

        self.index = faiss.read_index(str(index_path))
        self.dim = self.index.d
        with metadata_path.open("r", encoding="utf-8") as handle:
            self.metadata = json.load(handle)
        return True

    def save(self, index_path, metadata_path):
        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_path))
        with metadata_path.open("w", encoding="utf-8") as handle:
            json.dump(self.metadata, handle, indent=2, ensure_ascii=False)

    def search(self, embedding, k=5):
        if not self.is_ready or k <= 0:
            return []

        embedding = self._coerce_embedding(embedding)
        distances, indices = self.index.search(embedding, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            item = self.metadata[idx]
            item = {**item, "distance": float(dist)}
            results.append(item)

        return results


vector_store = VectorStore()
