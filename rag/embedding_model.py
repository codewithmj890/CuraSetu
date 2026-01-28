from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    """Singleton pattern for SentenceTransformer model to prevent memory leaks"""
    _model = None

    @classmethod
    def get_model(cls):
        """Load model once and reuse across requests"""
        if cls._model is None:
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model