"""
Tests for reader.py - OCR and document loading functionality.
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.reader import (
    load_document_text,
    _read_pdf_text,
    _ocr_tesseract,
    HAS_EASYOCR,
    HAS_DONUT
)


class TestPDFReading:
    """Test PDF text extraction."""
    
    def test_read_pdf_text_exists(self, tmp_path):
        """Test _read_pdf_text with a mock PDF."""
        # Create a temporary text file (PDFs need proper structure, so we'll skip actual PDFs in unit tests)
        # This test verifies the function exists and handles errors gracefully
        result = _read_pdf_text("nonexistent.pdf")
        assert result == "" or isinstance(result, str)


class TestOCR:
    """Test OCR functions."""
    
    @patch('src.reader.pytesseract.image_to_string')
    @patch('src.reader.cv2.imread')
    def test_ocr_tesseract_basic(self, mock_imread, mock_tesseract):
        """Test Tesseract OCR function."""
        mock_imread.return_value = MagicMock()
        mock_tesseract.return_value = "Sample OCR text"
        
        result = _ocr_tesseract("test.png")
        assert isinstance(result, str)
        mock_tesseract.assert_called_once()


class TestDocumentLoading:
    """Test main document loading function."""
    
    @patch('src.reader._read_pdf_text')
    def test_load_document_text_pdf(self, mock_pdf_read, tmp_path):
        """Test loading a PDF document."""
        mock_pdf_read.return_value = "PDF text content"
        
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("dummy")
        
        doc_id, text = load_document_text(str(pdf_path))
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0
        assert isinstance(text, str)
        assert text == "PDF text content"
    
    @patch.dict(os.environ, {'DISABLE_EASYOCR': 'false'})
    @patch('src.reader._ocr_easyocr')
    @patch('src.reader._ocr_tesseract')
    def test_load_document_text_image_fallback(self, mock_tesseract, mock_easyocr):
        """Test image loading with OCR fallback."""
        # EasyOCR fails, falls back to Tesseract
        mock_easyocr.side_effect = Exception("EasyOCR failed")
        mock_tesseract.return_value = "Tesseract OCR text"
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(b'fake image data')
            tmp_path = tmp.name
        
        try:
            doc_id, text = load_document_text(tmp_path)
            assert isinstance(text, str)
            assert text == "Tesseract OCR text"
        finally:
            os.unlink(tmp_path)
    
    def test_load_document_text_returns_tuple(self):
        """Test that load_document_text returns (doc_id, text) tuple."""
        # Using a file that doesn't exist to test error handling
        doc_id, text = load_document_text("nonexistent.txt")
        assert isinstance(doc_id, str)
        assert isinstance(text, str)
    
    @pytest.mark.skipif(not Path("data/samples").exists(), reason="Sample data not available")
    def test_load_document_text_with_sample(self, sample_image_path):
        """Test with actual sample image if available."""
        if sample_image_path and os.path.exists(sample_image_path):
            doc_id, text = load_document_text(sample_image_path)
            assert isinstance(doc_id, str)
            assert len(doc_id) > 0
            assert isinstance(text, str)


import tempfile