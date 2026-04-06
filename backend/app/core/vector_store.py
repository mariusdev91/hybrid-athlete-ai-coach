import faiss
import numpy as np


class VectorStore:
    def __init__(self, dim=384):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadata = []

    def add(self, embedding, metadata):
        # Convert list → numpy array
        if isinstance(embedding, list):
            embedding = np.array(embedding).astype("float32")

        # Ensure shape is (1, dim)
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)

        self.index.add(embedding)
        self.metadata.append(metadata)

    def search(self, embedding, k=5):
        # Convert list → numpy array
        if isinstance(embedding, list):
            embedding = np.array(embedding).astype("float32")

        # Ensure shape is (1, dim)
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)

        distances, indices = self.index.search(embedding, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            item = self.metadata[idx]
            item = {**item, "distance": float(dist)}
            results.append(item)

        return results


# GLOBAL SINGLETON
vector_store = VectorStore()
