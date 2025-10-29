"""
Tests for rag_indexer.py - Vector indexing and retrieval functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rag_indexer import build_index, retrieve_context, GLOBAL_INDEX


class TestRAGIndexer:
    """Test RAG indexing functionality."""
    
    def setup_method(self):
        """Reset global index before each test."""
        global GLOBAL_INDEX
        import src.rag_indexer
        src.rag_indexer.GLOBAL_INDEX = None
    
    @patch('src.rag_indexer.OpenAIEmbeddings')
    @patch('src.rag_indexer.Chroma')
    def test_build_index_with_tuples(self, mock_chroma_class, mock_embeddings_class):
        """Test building index with tuple format."""
        mock_embeddings = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings
        
        mock_chroma = MagicMock()
        mock_chroma_class.from_texts.return_value = mock_chroma
        
        docs = [("doc1", "Text content 1"), ("doc2", "Text content 2")]
        result = build_index(docs)
        
        assert result == mock_chroma
        mock_chroma_class.from_texts.assert_called_once()
    
    @patch('src.rag_indexer.OpenAIEmbeddings')
    @patch('src.rag_indexer.Chroma')
    def test_build_index_with_dicts(self, mock_chroma_class, mock_embeddings_class):
        """Test building index with dict format."""
        mock_embeddings = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings
        
        mock_chroma = MagicMock()
        mock_chroma_class.from_texts.return_value = mock_chroma
        
        docs = [
            {"doc_id": "doc1", "text": "Text content 1"},
            {"doc_id": "doc2", "text": "Text content 2"}
        ]
        result = build_index(docs)
        
        assert result == mock_chroma
        mock_chroma_class.from_texts.assert_called_once()
    
    @patch('src.rag_indexer.OpenAIEmbeddings')
    @patch('src.rag_indexer.Chroma')
    def test_build_index_adds_to_existing(self, mock_chroma_class, mock_embeddings_class):
        """Test that building index adds to existing global index."""
        mock_embeddings = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings
        mock_embeddings.embed_query.return_value = [0.1] * 384  # Mock embedding vector
        
        mock_chroma = MagicMock()
        mock_chroma._collection = MagicMock()
        mock_chroma._collection.add = MagicMock()
        mock_chroma_class.from_texts.return_value = mock_chroma
        
        # First build
        docs1 = [("doc1", "Text 1")]
        build_index(docs1)
        
        # Second build should add to existing
        docs2 = [("doc2", "Text 2")]
        build_index(docs2)
        
        # Should call add on collection
        assert mock_chroma._collection.add.called
    
    def test_retrieve_context_without_index(self):
        """Test that retrieve_context raises error when no index exists."""
        import src.rag_indexer
        src.rag_indexer.GLOBAL_INDEX = None
        
        with pytest.raises(ValueError, match="No index available"):
            retrieve_context("test query")
    
    @patch('src.rag_indexer.GLOBAL_INDEX')
    def test_retrieve_context_with_index(self, mock_index):
        """Test retrieving context from existing index."""
        mock_index.similarity_search.return_value = [
            MagicMock(page_content="Result 1"),
            MagicMock(page_content="Result 2"),
            MagicMock(page_content="Result 3")
        ]
        
        import src.rag_indexer
        src.rag_indexer.GLOBAL_INDEX = mock_index
        
        result = retrieve_context("test query", k=3)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert "Result 1" in result
        mock_index.similarity_search.assert_called_once_with("test query", k=3)
    
    @patch('src.rag_indexer.GLOBAL_INDEX')
    def test_retrieve_context_with_custom_k(self, mock_index):
        """Test retrieving context with custom k parameter."""
        mock_index.similarity_search.return_value = [
            MagicMock(page_content="Result 1")
        ]
        
        import src.rag_indexer
        src.rag_indexer.GLOBAL_INDEX = mock_index
        
        result = retrieve_context("test query", k=1)
        
        assert len(result) == 1
        mock_index.similarity_search.assert_called_once_with("test query", k=1)