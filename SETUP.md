# Setup Instructions

## Quick Start

### 1. Install System Dependencies

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Windows:**
Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional but recommended
OPENAI_MODEL=gpt-4o-mini
USE_OPENAI_ONLY=true
FORCE_LOCAL_ONLY=false

# Performance tuning (optional)
DISABLE_DONUT=false    # Set to true for faster startup
DISABLE_EASYOCR=false  # Set to true for faster startup
```

### 4. Verify Installation

```bash
# Run tests
pytest tests/test_extractor.py -v

# Start application
streamlit run src/app.py
```

## Troubleshooting

### Common Issues

1. **Tesseract not found:**
   - Ensure Tesseract is installed and in PATH
   - Check: `tesseract --version`

2. **OpenAI API errors:**
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API key validity and quota

3. **Import errors:**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

4. **Slow startup:**
   - Set `DISABLE_DONUT=true` and `DISABLE_EASYOCR=true` in `.env`
   - Models will load on-demand when needed
