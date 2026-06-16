import numpy as np
from rag.embedding_model import EmbeddingModel
from rag.faiss_index import FaissStore


class MedicalRetriever:
    """
    Retrieves clinically relevant medical knowledge chunks
    with explainable metadata.
    """

    def __init__(self):
        self.model = EmbeddingModel()
        self.store = FaissStore()

    def retrieve(self, query: str, top_k: int = 5):
        """
        Retrieve top-k relevant medical chunks.

        Returns enriched metadata for reasoning.
        """
        # Embed user query
        query_embedding = self.model.embed_text(query)
        query_embedding = np.array(query_embedding).astype("float32")

        # FAISS search
        results = self.store.search(query_embedding, top_k)

        # Safety filter
        cleaned = []
        for r in results:
            if "text" in r and len(r["text"].strip()) > 10:
                cleaned.append(r)

        return cleaned
