from typing import List, Dict, Optional, Any
from backend.services.vectorizer import Vectorizer


class RAGService:
    
    def __init__(self):
        self.vectorizer = Vectorizer()
    
    async def search(self, query: str, top_k: int = 5, filter_by: Optional[Dict[str, Any]] = None) -> List[Dict]:
        results = await self.vectorizer.search(query, top_k=top_k, filter_by=filter_by)
        return results
    
    async def query(self, query: str, top_k: int = 5, filter_by: Optional[Dict[str, Any]] = None) -> Dict:
        results = await self.search(query, top_k=top_k, filter_by=filter_by)
        
        if not results:
            return {
                "context": "",
                "sources": []
            }
        
        context_parts = []
        sources = []
        seen_sources = set()
        
        for i, result in enumerate(results, 1):
            text = result['text']
            metadata = result['metadata']
            source = metadata.get('source', 'Unknown')
            page = metadata.get('page', 'N/A')
            
            context_parts.append(f"[{i}] {text}")
            
            source_key = f"{source}_p{page}"
            if source_key not in seen_sources:
                sources.append({
                    'source': source,
                    'file_path': metadata.get('file_path', ''),
                    'page': page,
                    'chunk_index': metadata.get('chunk_index', 0),
                    'relevance_score': 1.0 - result.get('distance', 0.0) if result.get('distance') else None
                })
                seen_sources.add(source_key)
        
        context = "\n\n".join(context_parts)
        
        return {
            "context": context,
            "sources": sources
        }
    
    async def format_context_for_prompt(self, query: str, top_k: int = 5) -> str:
        rag_result = await self.query(query, top_k=top_k)
        
        if not rag_result["context"]:
            return ""
        
        formatted = "Relevant document excerpts:\n\n"
        formatted += rag_result["context"]
        formatted += "\n\nUse the above context to answer the following question. If the context doesn't contain relevant information, say so.\n\n"
        formatted += f"Question: {query}\n\n"
        
        return formatted
