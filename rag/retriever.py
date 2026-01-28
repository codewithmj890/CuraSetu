import numpy as np
from rag.embedding_model import EmbeddingModel
from rag.faiss_index import FaissStore

class MedicalRetriever:
    """Retrieves relevant medical knowledge chunks for user queries"""
    
    def __init__(self):
        """Initialize embedding model and FAISS store"""
        self.model = EmbeddingModel.get_model()
        self.store = FaissStore()

    def retrieve(self, query, top_k=5):
        """
        Retrieve top-k most relevant medical chunks for a query
        
        Args:
            query (str): User's symptom description
            top_k (int): Number of chunks to retrieve
            
        Returns:
            list: List of medical knowledge chunks with metadata
        """
        # Generate embedding for user query
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")
        
        # Search FAISS index for similar chunks
        return self.store.search(query_embedding, top_k)