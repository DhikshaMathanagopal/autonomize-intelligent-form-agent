# System Architecture

## Overview

The Intelligent Form Agent is designed as a modular, multi-stage pipeline that processes healthcare forms through OCR, visual understanding, structured extraction, and intelligent querying.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Single   │  │ Summarize│  │ Multi    │            │
│  │ Form QA  │  │   Form   │  │ Form QA  │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Document Reader                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ PDF Text │  │  EasyOCR │  │Tesseract │            │
│  │Extraction│  │          │  │          │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│                         │                              │
│                         ▼                              │
│              ┌─────────────────┐                      │
│              │ Google Vision    │                      │
│              │ (Fallback)       │                      │
│              └─────────────────┘                      │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Donut Vision-Language Model                │
│  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Checkbox        │  │ Structured      │             │
│  │ Detection       │  │ Field Extraction │             │
│  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Enhanced Text        │
              │  (OCR + Visual Data)  │
              └──────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Field      │ │   Vector     │ │   Summary    │
│  Extraction  │ │   Indexing    │ │  Generation  │
│  (OpenAI)    │ │  (Chroma +    │ │  (OpenAI)    │
│              │ │  Embeddings)  │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
        │                │
        │                ▼
        │         ┌──────────────┐
        │         │ Context      │
        │         │ Retrieval    │
        │         └──────────────┘
        │                │
        └────────┬───────┘
                 ▼
        ┌──────────────┐
        │   RAG QA     │
        │   (OpenAI)   │
        └──────────────┘
```

## Component Details

### 1. Document Reader (`reader.py`)

**Purpose:** Extract text from various document formats

**Flow:**
1. PDF → Direct text extraction using `pypdf`
2. Images → Multi-engine OCR cascade:
   - Primary: EasyOCR (fast, good for printed text)
   - Secondary: Tesseract (robust, works offline)
   - Fallback: Google Vision (cloud-based, high accuracy)

**Key Functions:**
- `load_document_text(path)` - Main entry point
- `_read_pdf_text(path)` - PDF extraction
- `_ocr_easyocr(img_path)` - EasyOCR integration
- `_ocr_tesseract(img_path)` - Tesseract integration
- `_ocr_google_vision(img_path)` - Google Vision API

### 2. Vision Processing (`reader.py` - Donut)

**Purpose:** Visual understanding for checkboxes and handwritten fields

**Models:**
- Donut (`naver-clova-ix/donut-base-finetuned-docvqa`)
  - Visual QA for specific questions
  - Structured field extraction from images

**Key Functions:**
- `_donut_answer(image_path, question)` - Answer questions about form visually
- `_donut_extract_form_data(image_path)` - Extract structured checkbox/data

### 3. Field Extractor (`extractor.py`)

**Purpose:** Extract structured key-value pairs from form text

**Process:**
1. Parse form text with adaptive prompts
2. Use OpenAI GPT-4o-mini for extraction
3. Refine results if extraction is weak (< 3 fields)
4. Normalize output structure

**Output Format:**
```json
{
  "form_type": "Prior Authorization",
  "fields": {
    "Patient Name": "John Doe",
    "DOB": "02/14/1980",
    "Diagnosis": "Hypertension"
  }
}
```

### 4. RAG Indexer (`rag_indexer.py`)

**Purpose:** Create searchable vector index for semantic search

**Components:**
- **Embeddings:** OpenAI text-embedding models
- **Vector Store:** Chroma (in-memory)
- **Indexing:** Document normalization and metadata tracking

**Features:**
- Global index management
- Similarity search (top-k retrieval)
- Metadata filtering support

### 5. QA Agent (`qa_agent.py`)

**Purpose:** Answer questions using retrieved context

**RAG Pipeline:**
1. Retrieve relevant context chunks from vector index
2. Combine context with user question
3. Generate answer using OpenAI GPT
4. Return natural language response

### 6. Summarizer (`summarizer.py`)

**Purpose:** Generate concise summaries of form content

**Input:**
- Extracted fields
- Original form text (clipped for performance)

**Output:**
- Bullet-point summary
- Field-based quick summary (fallback)

## Data Flow

### Single Form QA Flow

```
1. User uploads form
   ↓
2. OCR extraction → Text
   ↓
3. Donut visual extraction → Checkbox data
   ↓
4. Merge: Text + Visual data → Enhanced text
   ↓
5. Vector index creation
   ↓
6. User asks question
   ↓
7. Context retrieval (semantic search)
   ↓
8. Donut visual QA (if applicable)
   ↓
9. RAG answer generation
   ↓
10. Combine/prioritize responses
```

### Summarization Flow

```
1. User uploads form
   ↓
2. OCR extraction → Text
   ↓
3. Field extraction (OpenAI) → Structured fields
   ↓
4. Summary generation (OpenAI) → Bullet points
```

## Design Decisions

### 1. Multi-Engine OCR
**Rationale:** Different OCR engines excel at different tasks:
- EasyOCR: Fast, good for printed text
- Tesseract: Robust, works offline
- Google Vision: High accuracy, handles complex layouts

### 2. Donut Integration
**Rationale:** OCR misses visual elements like checkboxes. Donut provides:
- Visual reasoning capabilities
- Checkbox detection
- Handwritten text recognition

### 3. RAG Architecture
**Rationale:** Combines retrieval (accurate context) with generation (natural answers):
- More accurate than pure generation
- Grounded in source documents
- Supports multi-document queries

### 4. OpenAI Dependencies
**Rationale:** For reliable, production-quality results:
- High-quality field extraction
- Accurate summarization
- Natural language QA

### 5. Chroma Vector Store
**Rationale:** Lightweight, easy to integrate:
- In-memory performance
- LangChain compatibility
- Simple API

## Performance Optimizations

1. **Lazy Loading:** Heavy models (Donut, EasyOCR) load on-demand
2. **Text Clipping:** Long documents clipped to 1500 chars for summarization
3. **Caching:** Vector index persists during session
4. **Fallback Chains:** Multiple OCR engines ensure reliability
5. **Timeout Handling:** Fast failures prevent hanging

## Error Handling

- **OCR Failures:** Automatic fallback to next engine
- **API Failures:** Graceful degradation with fallback summaries
- **Model Loading:** Optional models fail silently if unavailable
- **Missing Data:** Structured output guarantees for consistency

## Scalability Considerations

- **Current:** Single-user, in-memory processing
- **Potential Improvements:**
  - Persistent vector database (Pinecone, Weaviate)
  - Batch processing capabilities
  - Model caching and optimization
  - Async processing for multiple documents
