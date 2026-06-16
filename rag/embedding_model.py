from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Singleton wrapper for SentenceTransformer.
    Adds medical-aware embedding helpers.
    """
    _model = None

    @classmethod
    def get_model(cls):
        """Load model once and reuse across requests"""
        if cls._model is None:
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model

    @classmethod
    def embed_text(cls, text: str):
        """
        Embed a single piece of medical text safely.
        """
        model = cls.get_model()
        return model.encode([text], normalize_embeddings=True)
