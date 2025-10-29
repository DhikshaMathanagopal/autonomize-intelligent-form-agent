"""
Tests for extractor.py - Field extraction functionality.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extractor import extract_fields


class TestFieldExtraction:
    """Test field extraction functionality."""
    
    @patch('src.extractor.can_use_openai')
    @patch('src.extractor.OpenAI')
    def test_extract_fields_with_openai(self, mock_openai_class, mock_can_use, sample_form_text):
        """Test field extraction using OpenAI."""
        mock_can_use.return_value = True
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "form_type": "Prior Authorization",
            "fields": {
                "Patient Name": "John Doe",
                "DOB": "02/14/1980",
                "Diagnosis": "Hypertension"
            }
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_fields(sample_form_text)
        
        assert "form_type" in result
        assert "fields" in result
        assert isinstance(result["fields"], dict)
        assert "Patient Name" in result["fields"]
    
    @patch('src.extractor.can_use_openai')
    def test_extract_fields_without_openai(self, mock_can_use, sample_form_text):
        """Test field extraction without OpenAI (returns minimal structure)."""
        mock_can_use.return_value = False
        
        result = extract_fields(sample_form_text)
        
        # Should still return proper structure
        assert "form_type" in result
        assert "fields" in result
        assert isinstance(result["fields"], dict)
    
    @patch('src.extractor.can_use_openai')
    @patch('src.extractor.OpenAI')
    def test_extract_fields_handles_json_decode_error(self, mock_openai_class, mock_can_use, sample_form_text):
        """Test that extractor handles JSON decode errors gracefully."""
        mock_can_use.return_value = True
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_fields(sample_form_text)
        
        # Should still return structure even with bad JSON
        assert "form_type" in result or "raw_text" in result
        assert isinstance(result, dict)
    
    @patch('src.extractor.can_use_openai')
    @patch('src.extractor.OpenAI')
    def test_extract_fields_handles_api_error(self, mock_openai_class, mock_can_use, sample_form_text):
        """Test that extractor handles API errors gracefully."""
        mock_can_use.return_value = True
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = extract_fields(sample_form_text)
        
        # Should return minimal structure on error
        assert isinstance(result, dict)
        assert "form_type" in result
        assert "fields" in result
    
    def test_extract_fields_structure_guarantee(self, sample_form_text):
        """Test that extract_fields always returns proper structure."""
        with patch('src.extractor.can_use_openai', return_value=False):
            result = extract_fields(sample_form_text)
            
            assert isinstance(result, dict)
            assert "form_type" in result
            assert "fields" in result
            assert isinstance(result["fields"], dict)
    
    @patch('src.extractor.can_use_openai')
    @patch('src.extractor.OpenAI')
    def test_extract_fields_refinement_when_weak(self, mock_openai_class, mock_can_use, sample_form_text):
        """Test that extractor refines extraction when result is weak."""
        mock_can_use.return_value = True
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # First call returns weak result (< 3 fields)
        weak_response = MagicMock()
        weak_response.choices = [MagicMock()]
        weak_response.choices[0].message.content = json.dumps({
            "form_type": "Test",
            "fields": {"Field1": "Value1"}
        })
        
        # Second call (refinement) returns better result
        refined_response = MagicMock()
        refined_response.choices = [MagicMock()]
        refined_response.choices[0].message.content = json.dumps({
            "form_type": "Prior Authorization",
            "fields": {
                "Patient Name": "John Doe",
                "DOB": "02/14/1980",
                "Diagnosis": "Hypertension",
                "Provider": "Dr. Smith"
            }
        })
        
        mock_client.chat.completions.create.side_effect = [weak_response, refined_response]
        
        result = extract_fields(sample_form_text)
        
        # Should have refined result
        assert len(result.get("fields", {})) >= 3