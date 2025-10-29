# Testing Guide

## Summary

✅ **Cleaned up unnecessary files:**
- Deleted `src/ontology.json` (was empty)
- Deleted `src/layout.py` (was empty)

✅ **Created comprehensive test suite:**
- `tests/conftest.py` - Shared fixtures and utilities
- `tests/test_reader.py` - OCR and document loading tests
- `tests/test_extractor.py` - Field extraction tests with mocks
- `tests/test_summarizer.py` - Summarization tests
- `tests/test_rag_indexer.py` - Vector indexing tests
- `tests/test_qa_agent.py` - QA agent tests
- `tests/test_end_to_end.py` - Integration tests
- `pytest.ini` - Pytest configuration

## Running Tests

### Prerequisites

Install dependencies:
```bash
pip install -r requirements.txt
```

Set up environment variables (for tests that need OpenAI):
```bash
export OPENAI_API_KEY="sk-your-key-here"  # Optional, most tests use mocks
```

### Run Tests

**Run all tests:**
```bash
pytest
```

**Run with verbose output:**
```bash
pytest -v
```

**Run specific test file:**
```bash
pytest tests/test_extractor.py
```

**Run with coverage:**
```bash
pytest --cov=src --cov-report=html
```

**Skip slow tests:**
```bash
pytest -m "not slow"
```

## Test Structure

### Unit Tests (with mocks)
Most tests mock external dependencies:
- ✅ OpenAI API calls - mocked to avoid costs/network
- ✅ OCR operations - mocked for fast execution
- ✅ Vector store operations - mocked for isolation

### Integration Tests
- End-to-end workflows
- Multiple components working together

### Fixtures
Located in `conftest.py`:
- `sample_form_text` - Sample form content
- `sample_extracted_fields` - Sample extracted structure
- `mock_openai_client` - Mocked OpenAI client
- `mock_env_vars` - Environment variable mocks

## What's Tested

### ✅ Reader Module (`test_reader.py`)
- PDF text extraction
- OCR functions (Tesseract)
- Document loading with fallbacks
- Error handling

### ✅ Extractor Module (`test_extractor.py`)
- Field extraction with OpenAI
- Fallback behavior when OpenAI unavailable
- JSON parsing and error handling
- Refinement logic for weak extractions

### ✅ Summarizer Module (`test_summarizer.py`)
- Document summarization
- OpenAI integration
- Fallback summaries when OpenAI unavailable
- Text clipping for long documents

### ✅ RAG Indexer (`test_rag_indexer.py`)
- Index building with tuples and dicts
- Context retrieval
- Global index management
- Error handling for missing index

### ✅ QA Agent (`test_qa_agent.py`)
- Question answering with context
- Automatic context retrieval
- Different context formats (list, string)
- Error handling

### ✅ End-to-End (`test_end_to_end.py`)
- Complete extraction → summarization workflow
- RAG indexing → QA workflow
- PDF processing workflow

## Notes

- **Most tests use mocks** to avoid external API calls and dependencies
- **Sample data tests** are skipped if data files aren't available
- **OpenAI tests** can work with real API or mocks (mocks preferred)
- Tests are designed to be **fast and isolated**

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest`
3. Add more tests as you add features
4. Use `pytest --cov` to check test coverage
