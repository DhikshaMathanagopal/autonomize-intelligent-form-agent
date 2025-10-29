# Intelligent Form Agent - Machine Learning Project

An intelligent document processing system that extracts structured information from healthcare forms using OCR, computer vision, and retrieval-augmented generation (RAG).

## Project Overview

This project implements an end-to-end pipeline for intelligent form processing that:

1. **Extracts text** from PDFs and images using multiple OCR engines (EasyOCR, Tesseract, Google Vision)
2. **Identifies visual elements** like checkboxes and handwritten fields using Donut vision-language model
3. **Extracts structured fields** using OpenAI GPT models
4. **Indexes documents** in a vector database (Chroma) for semantic search
5. **Answers questions** using RAG (Retrieval-Augmented Generation)
6. **Generates summaries** of form content

## Project Structure

```
autonomize-intelligent-form-agent/
├── src/                    # Source code
│   ├── app.py             # Streamlit web application
│   ├── reader.py          # OCR and document loading
│   ├── extractor.py      # Field extraction
│   ├── summarizer.py     # Document summarization
│   ├── rag_indexer.py    # Vector indexing and retrieval
│   ├── qa_agent.py       # Question answering agent
│   └── config.py         # Configuration management
├── tests/                 # Test suite
│   ├── conftest.py       # Shared fixtures
│   ├── test_reader.py    # OCR tests
│   ├── test_extractor.py # Extraction tests
│   ├── test_summarizer.py # Summarization tests
│   ├── test_rag_indexer.py # RAG tests
│   ├── test_qa_agent.py  # QA tests
│   └── test_end_to_end.py # Integration tests
├── data/                  # Sample data
│   └── samples/          # Sample form images
├── requirements.txt      # Python dependencies
├── pytest.ini           # Test configuration
├── README.md            # This file
└── TESTING.md           # Testing documentation
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Tesseract OCR installed on your system:
  ```bash
  # macOS
  brew install tesseract
  
  # Linux
  sudo apt-get install tesseract-ocr
  ```

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd autonomize-intelligent-form-agent
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   USE_OPENAI_ONLY=true
   FORCE_LOCAL_ONLY=false
   
   # Optional: Google Vision OCR
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account.json
   
   # Optional: Disable heavy models for faster startup
   DISABLE_DONUT=false
   DISABLE_EASYOCR=false
   ```

## Usage

### Running the Application

Start the Streamlit web interface:
```bash
streamlit run src/app.py
```

The application will open in your browser at `http://localhost:8501`

### Features

The application provides three main tabs:

1. **Single Form QA**: Upload a form and ask questions about it
   - Automatically extracts checkbox/visual data using Donut
   - Indexes content for semantic search
   - Answers questions using RAG

2. **Summarize Form**: Extract structured fields and generate summaries
   - Field extraction from form text
   - Automated summarization

3. **Multi-Form Insights**: Analyze multiple forms together
   - Indexes multiple documents
   - Cross-document question answering

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_extractor.py -v
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## System Architecture

### Pipeline Flow

```
Input Document (PDF/Image)
    ↓
OCR Processing (EasyOCR → Tesseract → Google Vision)
    ↓
Donut Visual Extraction (Checkboxes, handwritten fields)
    ↓
Enhanced Text (OCR + Visual Data)
    ↓
Vector Indexing (Chroma + OpenAI Embeddings)
    ↓
┌─────────────────┬──────────────────┐
│   Field Extract │  Question Answer │
│   (OpenAI GPT)  │   (RAG + OpenAI) │
└─────────────────┴──────────────────┘
```

### Key Components

1. **Reader Module** (`reader.py`)
   - Multi-engine OCR (EasyOCR, Tesseract, Google Vision)
   - PDF text extraction
   - Donut vision-language model integration
   - Fallback mechanisms

2. **Extractor Module** (`extractor.py`)
   - Structured field extraction using OpenAI
   - JSON output normalization
   - Error handling and refinement

3. **RAG Indexer** (`rag_indexer.py`)
   - Document vectorization using OpenAI embeddings
   - Chroma vector store
   - Semantic similarity search

4. **QA Agent** (`qa_agent.py`)
   - Context retrieval from vector store
   - OpenAI-powered question answering
   - RAG (Retrieval-Augmented Generation) implementation

5. **Summarizer** (`summarizer.py`)
   - Document summarization
   - Field-based summaries
   - Fast fallback summaries

## Dependencies

### Core Libraries
- `streamlit` - Web interface
- `openai` - GPT models for extraction and QA
- `langchain` - RAG framework
- `chromadb` - Vector database

### OCR & Vision
- `easyocr` - OCR engine
- `pytesseract` - Tesseract OCR wrapper
- `google-cloud-vision` - Google Vision API
- `transformers` - Hugging Face models (Donut)

### Testing
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities

See `requirements.txt` for complete list.

## Configuration

Configuration is managed through environment variables and `src/config.py`:

- `OPENAI_API_KEY` - Required for field extraction and QA
- `OPENAI_MODEL` - Default: `gpt-4o-mini`
- `USE_OPENAI_ONLY` - Use only OpenAI (no Ollama fallback)
- `DISABLE_DONUT` - Skip Donut model loading
- `DISABLE_EASYOCR` - Skip EasyOCR initialization

## Performance Considerations

- **Fast Startup**: Disable heavy models (`DISABLE_DONUT=true`, `DISABLE_EASYOCR=true`) for faster initial load
- **Model Loading**: Donut model loads on-demand for visual reasoning
- **OCR Fallback**: Multiple OCR engines provide reliability
- **Caching**: Vector index persists in memory during session

## Limitations

- OpenAI API required for core functionality
- Donut model requires significant memory
- OCR accuracy depends on image quality
- Vector index is in-memory (not persistent across restarts)

## Future Improvements

- [ ] Persistent vector database
- [ ] Local LLM support (Llama, Mistral)
- [ ] Batch processing capabilities
- [ ] Enhanced error handling
- [ ] Model fine-tuning options
- [ ] Multi-language support

## License

This project is created for educational purposes as part of a Machine Learning assignment.

## Author

Autonomize AI - Machine Learning Assignment Project

## Acknowledgments

- Hugging Face for Donut model
- OpenAI for GPT models
- LangChain community
- Streamlit framework
