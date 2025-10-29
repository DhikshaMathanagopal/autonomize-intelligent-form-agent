"""
End-to-end integration tests for the complete pipeline.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.reader import load_document_text
from src.extractor import extract_fields
from src.summarizer import summarize_doc
from src.rag_indexer import build_index, retrieve_context
from src.qa_agent import answer_with_rag


class TestEndToEndPipeline:
    """Test complete pipeline workflows."""
    
    def setup_method(self):
        """Reset global state before each test."""
        import src.rag_indexer
        src.rag_indexer.GLOBAL_INDEX = None
    
    @patch('src.extractor.can_use_openai')
    @patch('src.extractor.OpenAI')
    @patch('src.summarizer.can_use_openai')
    @patch('src.summarizer.OpenAI')
    def test_extract_and_summarize_workflow(self, mock_summary_openai, mock_summary_can_use,
                                             mock_extract_openai, mock_extract_can_use):
        """Test field extraction followed by summarization."""
        # Mock extractor
        mock_extract_can_use.return_value = True
        mock_extract_client = MagicMock()
        mock_extract_openai.return_value = mock_extract_client
        
        extract_response = MagicMock()
        extract_response.choices = [MagicMock()]
        import json
        extract_response.choices[0].message.content = json.dumps({
            "form_type": "Prior Authorization",
            "fields": {"Patient Name": "John Doe", "Diagnosis": "Hypertension"}
        })
        mock_extract_client.chat.completions.create.return_value = extract_response
        
        # Mock summarizer
        mock_summary_can_use.return_value = True
        mock_summary_client = MagicMock()
        mock_summary_openai.return_value = mock_summary_client
        
        summary_response = MagicMock()
        summary_response.choices = [MagicMock()]
        summary_response.choices[0].message.content = "- Form: Prior Authorization\n- Patient: John Doe"
        mock_summary_client.chat.completions.create.return_value = summary_response
        
        # Test workflow
        form_text = "Form Type: Prior Authorization\nPatient Name: John Doe\nDiagnosis: Hypertension"
        fields = extract_fields(form_text)
        
        assert "fields" in fields
        assert "Patient Name" in fields["fields"]
        
        summary = summarize_doc(fields, form_text)
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    @patch('src.rag_indexer.OpenAIEmbeddings')
    @patch('src.rag_indexer.Chroma')
    @patch('src.qa_agent.OpenAI')
    def test_rag_qa_workflow(self, mock_qa_openai, mock_chroma, mock_embeddings):
        """Test RAG indexing and QA workflow."""
        # Setup mocks
        mock_emb = MagicMock()
        mock_embeddings.return_value = mock_emb
        
        mock_index = MagicMock()
        mock_index.similarity_search.return_value = [
            MagicMock(page_content="Patient Name: John Doe\nDiagnosis: Hypertension")
        ]
        mock_chroma.from_texts.return_value = mock_index
        
        mock_qa_client = MagicMock()
        mock_qa_openai.return_value = mock_qa_client
        
        qa_response = MagicMock()
        qa_response.choices = [MagicMock()]
        qa_response.choices[0].message.content = "John Doe"
        mock_qa_client.chat.completions.create.return_value = qa_response
        
        # Test workflow
        docs = [{"doc_id": "doc1", "text": "Patient Name: John Doe\nDiagnosis: Hypertension"}]
        index = build_index(docs)
        
        ctx = retrieve_context("Who is the patient?")
        assert len(ctx) > 0
        
        answer = answer_with_rag("Who is the patient?", ctx)
        assert isinstance(answer, str)
        assert len(answer) > 0
    
    @patch('src.reader._read_pdf_text')
    @patch('src.extractor.can_use_openai')
    @patch('src.extractor.OpenAI')
    def test_pdf_extraction_workflow(self, mock_openai, mock_can_use, mock_pdf_read):
        """Test PDF loading and field extraction workflow."""
        mock_pdf_read.return_value = "Form Type: Prior Authorization\nPatient Name: John Doe"
        
        mock_can_use.return_value = True
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        import json
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = json.dumps({
            "form_type": "Prior Authorization",
            "fields": {"Patient Name": "John Doe"}
        })
        mock_client.chat.completions.create.return_value = response
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'fake pdf')
            pdf_path = tmp.name
        
        try:
            doc_id, text = load_document_text(pdf_path)
            assert len(text) > 0
            
            fields = extract_fields(text)
            assert "fields" in fields
        finally:
            os.unlink(pdf_path)