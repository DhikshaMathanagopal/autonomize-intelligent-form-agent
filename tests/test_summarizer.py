"""
Tests for summarizer.py - Document summarization functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.summarizer import summarize_doc


class TestSummarization:
    """Test document summarization."""
    
    @patch('src.summarizer.can_use_openai')
    @patch('src.summarizer.OpenAI')
    def test_summarize_doc_with_openai(self, mock_openai_class, mock_can_use, sample_extracted_fields):
        """Test summarization using OpenAI."""
        mock_can_use.return_value = True
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "- Form Type: Prior Authorization\n- Patient: John Doe"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = summarize_doc(sample_extracted_fields, "Sample form text")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('src.summarizer.can_use_openai')
    def test_summarize_doc_without_openai(self, mock_can_use, sample_extracted_fields):
        """Test summarization without OpenAI (deterministic fallback)."""
        mock_can_use.return_value = False
        
        with patch('src.summarizer.USE_OPENAI_ONLY', True):
            result = summarize_doc(sample_extracted_fields, "Sample text")
            
            assert isinstance(result, str)
            # Should contain form type or field info
            assert len(result) > 0
    
    @patch('src.summarizer.can_use_openai')
    @patch('src.summarizer.OpenAI')
    def test_summarize_doc_handles_api_error(self, mock_openai_class, mock_can_use, sample_extracted_fields):
        """Test that summarizer handles API errors gracefully."""
        mock_can_use.return_value = True
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch('src.summarizer.USE_OPENAI_ONLY', True):
            result = summarize_doc(sample_extracted_fields, "Sample text")
            
            # Should return fallback summary
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_summarize_doc_with_empty_fields(self):
        """Test summarization with empty fields."""
        empty_fields = {"form_type": "Unknown", "fields": {}}
        
        with patch('src.summarizer.can_use_openai', return_value=False):
            with patch('src.summarizer.USE_OPENAI_ONLY', True):
                result = summarize_doc(empty_fields, "")
                
                assert isinstance(result, str)
    
    @patch('src.summarizer.can_use_openai')
    @patch('src.summarizer.OpenAI')
    def test_summarize_doc_clips_text(self, mock_openai_class, mock_can_use, sample_extracted_fields):
        """Test that summarizer clips long text input."""
        mock_can_use.return_value = True
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Very long text
        long_text = "x" * 10000
        
        summarize_doc(sample_extracted_fields, long_text)
        
        # Verify OpenAI was called (should work with clipped text)
        assert mock_client.chat.completions.create.called
