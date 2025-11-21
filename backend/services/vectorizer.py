import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import asyncio
from pathlib import Path

from backend.config import settings


class Vectorizer:
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.db_path = Path(settings.CHROMA_DB_PATH)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.model = SentenceTransformer(self.model_name)
        
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    async def add_documents(self, chunks: List[Dict]) -> None:
        if not chunks:
            return
        
        texts = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        embeddings = await self._generate_embeddings(texts)
        
        ids = [f"{meta['source']}_{meta['chunk_index']}" for meta in metadatas]
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()
        )
        return embeddings
    
    async def search(self, query: str, top_k: int = 5, filter_by: Optional[Dict] = None) -> List[Dict]:
        query_embedding = await self._generate_embeddings([query])
        
        where = None
        if filter_by:
            where = filter_by
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where
        )
        
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    async def list_documents(self) -> List[Dict]:
        all_docs = self.collection.get()
        
        unique_sources = {}
        for i, metadata in enumerate(all_docs['metadatas']):
            source = metadata.get('source', 'unknown')
            if source not in unique_sources:
                unique_sources[source] = {
                    'source': source,
                    'file_path': metadata.get('file_path', ''),
                    'total_chunks': 0,
                    'pages': set()
                }
            unique_sources[source]['total_chunks'] += 1
            if 'page' in metadata:
                unique_sources[source]['pages'].add(metadata['page'])
        
        documents = []
        for source_info in unique_sources.values():
            documents.append({
                'source': source_info['source'],
                'file_path': source_info['file_path'],
                'total_chunks': source_info['total_chunks'],
                'page_range': f"{min(source_info['pages'])}-{max(source_info['pages'])}" if source_info['pages'] else "N/A"
            })
        
        return documents
    
    def reset_collection(self) -> None:
        self.client.delete_collection(name="documents")
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_collection_count(self) -> int:
        return self.collection.count()
