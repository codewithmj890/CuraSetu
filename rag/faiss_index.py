import faiss
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

class FaissStore:
    """Read-only FAISS vector store for medical knowledge retrieval"""
    
    def __init__(self):
        """Load FAISS index and metadata from disk"""
        index_path = os.path.join(DATA_DIR, "curasetu_faiss.index")
        metadata_path = os.path.join(DATA_DIR, "curasetu_metadata.json")
        
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata not found at {metadata_path}")
            
        self.index = faiss.read_index(index_path)
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def search(self, query_vector, top_k=5):
        """Search for similar medical chunks"""
        distances, indices = self.index.search(query_vector, top_k)
        return [self.metadata[i] for i in indices[0] if i < len(self.metadata)]