import voyageai
from typing import List, Optional
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.client = voyageai.Client(api_key=settings.VOYAGE_API_KEY)
        self.model = settings.VOYAGE_MODEL
        self.dimension = settings.VOYAGE_EMBEDDING_DIM
    
    def embed_texts(self, texts: List[str], input_type: str = "document") -> List[List[float]]:
        if not texts:
            return []
        result = self.client.embed(texts, model=self.model, input_type=input_type)
        return result.embeddings
    
    def embed_query(self, query: str) -> List[float]:
        result = self.client.embed([query], model=self.model, input_type="query")
        return result.embeddings[0]
    
    def embed_template(self, name: str, description: str, form_type: str, required_fields: dict) -> List[float]:
        text = f"Template: {name}\nDescription: {description}\nType: {form_type}\nFields: {', '.join(required_fields.keys())}"
        return self.embed_texts([text])[0]
    
    def embed_policy_chunk(self, chunk_text: str) -> List[float]:
        return self.embed_texts([chunk_text])[0]


embedding_service = EmbeddingService()