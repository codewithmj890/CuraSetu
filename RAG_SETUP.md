# RAG System Installation Guide

## Quick Setup

1. **Install RAG Dependencies**
   ```bash
   pip install sentence-transformers faiss-cpu numpy
   ```

2. **Verify RAG System**
   ```bash
   python test_rag.py
   ```

3. **Start Django Server**
   ```bash
   python manage.py runserver
   ```

## What Changed

### New Architecture
- **Before**: Direct symptom matching from JSON
- **After**: RAG-powered semantic search with FAISS

### New Files Added
- `rag/embedding_model.py` - Singleton embedding model
- `rag/faiss_index.py` - FAISS vector store loader  
- `rag/retriever.py` - Medical knowledge retriever
- `data/curasetu_faiss.index` - Vector embeddings
- `data/curasetu_metadata.json` - Medical knowledge chunks

### Modified Files
- `chatbot/services.py` - Added RAG integration
- `requirements.txt` - Added RAG dependencies

## How It Works

1. **User Query**: "I have fever and headache"
2. **Embedding**: Convert to vector using SentenceTransformer
3. **Search**: Find similar medical chunks in FAISS index
4. **Format**: Display structured medical information
5. **Safety**: Include medical disclaimers

## Fallback System

- If RAG fails → Falls back to original disease matching
- If no matches → Shows safe "consult doctor" message
- Zero breaking changes to existing functionality

## Benefits

✅ **Grounded Responses**: Uses verified medical data
✅ **No Hallucinations**: Only returns retrieved information  
✅ **Explainable**: Shows source and structured data
✅ **Fast**: FAISS provides millisecond search
✅ **Safe**: Includes medical disclaimers
✅ **Scalable**: Easy to add more medical knowledge