"""
Tests for qa_agent.py - Question answering functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.qa_agent import answer_with_rag


class TestQAAgent:
    """Test QA agent functionality."""
    
    @patch('src.qa_agent.OpenAI')
    def test_answer_with_rag_with_context(self, mock_openai_class):
        """Test QA agent with provided context."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "John Doe"
        mock_client.chat.completions.create.return_value = mock_response
        
        context_docs = ["Patient Name: John Doe\nDiagnosis: Hypertension"]
        result = answer_with_rag("Who is the patient?", context_docs)
        
        assert isinstance(result, str)
        assert "John" in result or "Doe" in result or len(result) > 0
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.qa_agent.retrieve_context')
    @patch('src.qa_agent.OpenAI')
    def test_answer_with_rag_auto_retrieve(self, mock_openai_class, mock_retrieve):
        """Test QA agent with automatic context retrieval."""
        mock_retrieve.return_value = ["Patient Name: Jane Doe"]
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Jane Doe"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = answer_with_rag("Who is the patient?")
        
        assert isinstance(result, str)
        mock_retrieve.assert_called_once_with("Who is the patient?")
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.qa_agent.OpenAI')
    def test_answer_with_rag_with_list_context(self, mock_openai_class):
        """Test QA agent with list of context documents."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Answer"
        mock_client.chat.completions.create.return_value = mock_response
        
        context_docs = ["Doc 1", "Doc 2", "Doc 3"]
        result = answer_with_rag("Test question?", context_docs)
        
        assert isinstance(result, str)
        # Verify context was joined
        call_args = mock_client.chat.completions.create.call_args
        assert "Doc 1" in str(call_args) or "Doc 2" in str(call_args)
    
    @patch('src.qa_agent.OpenAI')
    def test_answer_with_rag_with_string_context(self, mock_openai_class):
        """Test QA agent with string context."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Answer"
        mock_client.chat.completions.create.return_value = mock_response
        
        context_docs = "Single context string"
        result = answer_with_rag("Test question?", context_docs)
        
        assert isinstance(result, str)
    
    @patch('src.qa_agent.OpenAI')
    def test_answer_with_rag_handles_api_error(self, mock_openai_class):
        """Test that QA agent handles API errors gracefully."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        context_docs = ["Test context"]
        
        with pytest.raises(Exception):
            answer_with_rag("Test question?", context_docs)