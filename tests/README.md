# Test Suite

This directory contains comprehensive tests for the Intelligent Form Agent.

## Test Structure

- `conftest.py` - Shared pytest fixtures and test utilities
- `test_reader.py` - Tests for OCR and document loading
- `test_extractor.py` - Tests for field extraction
- `test_summarizer.py` - Tests for document summarization
- `test_rag_indexer.py` - Tests for vector indexing and retrieval
- `test_qa_agent.py` - Tests for question answering
- `test_end_to_end.py` - Integration tests for complete workflows

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test file:
```bash
pytest tests/test_extractor.py
```

### Run with verbose output:
```bash
pytest -v
```

### Run only fast tests (skip slow ones):
```bash
pytest -m "not slow"
```

### Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

## Test Markers

Tests can be marked with:
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_openai` - Tests needing OpenAI API key
- `@pytest.mark.requires_sample_data` - Tests needing sample data files

## Mocking

Most tests use mocks to avoid:
- Making actual API calls (OpenAI)
- Loading large models (Donut)
- Requiring external services (Ollama, Google Vision)

## Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock
```

## Notes

- Tests that require actual OpenAI API calls should set the `OPENAI_API_KEY` environment variable
- Sample data tests will be skipped if sample files are not available
- Most tests are unit tests with mocks for fast execution
