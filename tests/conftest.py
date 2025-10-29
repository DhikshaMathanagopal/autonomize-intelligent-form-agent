"""
Shared pytest fixtures for all tests.
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, MagicMock
from pathlib import Path


@pytest.fixture
def sample_form_text():
    """Sample form text for testing."""
    return """
    Form Type: Prior Authorization
    Patient Name: John Doe
    DOB: 02/14/1980
    Diagnosis: Hypertension
    Provider: Dr. Smith
    NPI #: 1234567890
    ICD10: I10
    Urgency: Urgent
    """


@pytest.fixture
def sample_extracted_fields():
    """Sample extracted fields structure."""
    return {
        "form_type": "Prior Authorization",
        "fields": {
            "Patient Name": "John Doe",
            "DOB": "02/14/1980",
            "Diagnosis": "Hypertension",
            "Provider": "Dr. Smith",
            "NPI #": "1234567890",
            "ICD10": "I10",
            "Urgency": "Urgent"
        }
    }


@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock OpenAI client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mocked response"
    mock_client.chat.completions.create.return_value = mock_response
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    return mock_client


@pytest.fixture
def sample_image_path():
    """Returns path to a sample image if available, otherwise None."""
    sample_path = Path("data/samples")
    if sample_path.exists():
        for img_file in sample_path.glob("*.png"):
            return str(img_file)
    return None


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    temp_file = tmp_path / "test_form.txt"
    temp_file.write_text("Sample form content for testing")
    return str(temp_file)


@pytest.fixture
def mock_donut():
    """Mock Donut model availability."""
    class MockDonut:
        HAS_DONUT = False
        
        @staticmethod
        def _donut_answer(path, question):
            return "Mocked Donut answer"
        
        @staticmethod
        def _donut_extract_form_data(path):
            return {"Form Type": "Test", "Urgency": "Urgent"}
    
    return MockDonut


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("USE_OPENAI_ONLY", "true")
    monkeypatch.setenv("FORCE_LOCAL_ONLY", "false")
