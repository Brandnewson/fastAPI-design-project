"""
RAG (Retrieval-Augmented Generation) infrastructure.

This module handles:
- Vector database initialization and management
- Document embedding and storage
- Similarity search for aerodynamic designs
- Integration with OpenAI embeddings API

The RAG pipeline allows us to:
1. Embed aerodynamic knowledge (airfoils, reference designs)
2. Store vectors in Chroma vector database
3. Retrieve similar designs when given a new wing specification
4. Provide context-aware recommendations to the LLM
"""
import logging
import time
from typing import Optional

import chromadb
from openai import OpenAI

from app.core.config import Settings, get_settings
from app.models import AeroPerformanceEstimate, SimilarConfigurationResult

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Handles all RAG operations for aerodynamic design retrieval.
    
    Responsibilities:
    - Initialize and manage Chroma vector database
    - Embed documents and create metadata
    - Perform similarity searches
    - Format results for API consumption
    
    Design pattern: Singleton pattern with dependency injection
    """

    def __init__(self, settings: Settings):
        """
        Initialize RAG engine with settings and OpenAI client.
        
        Args:
            settings: Application settings containing API keys and config
            
        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        self.settings = settings
        
        if settings.embedding_provider == "openai":
            if not settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY must be configured when using OpenAI embeddings. "
                    "Set it in .env file or switch to EMBEDDING_PROVIDER=local."
                )
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
        self._chroma_client: Optional[chromadb.Client] = None
        self._collection = None
        logger.info("RAG Engine initialized")

    @property
    def chroma_client(self) -> chromadb.Client:
        """
        Lazy-load Chroma client.
        
        Returns:
            chromadb.Client: Initialized Chroma client
        """
        if self._chroma_client is None:
            self._chroma_client = chromadb.PersistentClient(
                path=str(self.settings.chroma_path)
            )
            logger.debug(f"Chroma client initialized at {self.settings.chroma_path}")
        return self._chroma_client

    @property
    def collection(self):
        """
        Get or create the aerodynamic data collection.
        
        Returns:
            chromadb.Collection: The collection for storing aerodynamic data
        """
        if self._collection is None:
            self._collection = self.chroma_client.get_or_create_collection(
                name=self.settings.rag_collection_name,
                metadata={
                    "description": "Wing aerodynamic design reference collection",
                    "embedding_model": self.settings.embedding_model
                }
            )
            logger.debug(f"Collection '{self.settings.rag_collection_name}' retrieved/created")
        return self._collection

    def embed_text(self, text: str) -> list[float]:
        """
        Embed text using the configured embedding provider.
        
        Args:
            text: Text to embed
            
        Returns:
            list[float]: Embedding vector
            
        Raises:
            Exception: If embedding call fails
        """
        if self.settings.embedding_provider == "local":
            return self._local_embed(text)

        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.settings.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding failed for text: {text[:50]}... Error: {e}")
            raise

    def _local_embed(self, text: str) -> list[float]:
        """
        Generate a deterministic local embedding for offline development.

        This is a simple hash-based embedding suitable for demos and tests.
        It is NOT semantically meaningful like OpenAI embeddings.
        """
        import hashlib
        import random

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest, "big")
        rng = random.Random(seed)

        dim = self.settings.embedding_dimension
        return [rng.uniform(-1.0, 1.0) for _ in range(dim)]

    def add_airfoil(
        self,
        airfoil_name: str,
        description: str,
        metadata: dict,
        document_id: str
    ) -> None:
        """
        Add an airfoil profile to the vector database.
        
        Args:
            airfoil_name: Name of the airfoil (e.g., "NACA 23012")
            description: Aerodynamic characteristics and design notes
            metadata: Additional metadata (thickness, camber, etc.)
            document_id: Unique identifier for this document
            
        Raises:
            Exception: If database operation fails
        """
        try:
            embedding = self.embed_text(description)
            self.collection.add(
                ids=[document_id],
                embeddings=[embedding],
                documents=[description],
                metadatas=[{
                    "airfoil_name": airfoil_name,
                    **metadata
                }]
            )
            logger.debug(f"Added airfoil: {airfoil_name}")
        except Exception as e:
            logger.error(f"Failed to add airfoil {airfoil_name}: {e}")
            raise

    def search_similar(
        self,
        query_text: str,
        limit: Optional[int] = None
    ) -> list[tuple[str, float, dict]]:
        """
        Search for similar aerodynamic designs via semantic similarity.
        
        Args:
            query_text: Description of the desired wing characteristics
            limit: Maximum number of results (uses config default if None)
            
        Returns:
            list of tuples: (document, similarity_score, metadata)
            
        Details:
            - Embeds query using same model as indexed documents
            - Performs cosine similarity search in vector space
            - Returns results sorted by relevance (highest first)
            - Filters by configured similarity threshold
        """
        if limit is None:
            limit = self.settings.rag_top_k_results
            
        try:
            query_embedding = self.embed_text(query_text)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            # Format results as (document, score, metadata) tuples
            formatted_results = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for doc, distance, metadata in zip(
                    results["documents"][0],
                    results["distances"][0],
                    results["metadatas"][0]
                ):
                    # Chroma returns distance; convert to similarity (1 - distance)
                    similarity = 1 - distance
                    
                    # Filter by threshold
                    if similarity >= self.settings.rag_similarity_threshold:
                        formatted_results.append((doc, similarity, metadata))
            
            logger.debug(f"Search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def clear_collection(self) -> None:
        """
        Clear all documents from the collection.
        
        Uses for testing and data reset scenarios.
        Be careful: this is destructive.
        """
        try:
            # Get all IDs and delete them
            all_data = self.collection.get()
            if all_data and all_data["ids"]:
                self.collection.delete(ids=all_data["ids"])
            logger.info("Collection cleared")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise


# Global RAG engine instance
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine(settings: Optional[Settings] = None) -> RAGEngine:
    """
    Get or initialize the global RAG engine (singleton pattern).
    
    Args:
        settings: Application settings (optional, uses get_settings() if None)
        
    Returns:
        RAGEngine: Initialized RAG engine instance
        
    Example:
        >>> engine = get_rag_engine()
        >>> results = engine.search_similar("NACA airfoil for 45kg downforce")
    """
    global _rag_engine
    if _rag_engine is None:
        if settings is None:
            settings = get_settings()
        _rag_engine = RAGEngine(settings)
    return _rag_engine


def reset_rag_engine() -> None:
    """
    Reset the global RAG engine (primarily for testing).
    """
    global _rag_engine
    _rag_engine = None
