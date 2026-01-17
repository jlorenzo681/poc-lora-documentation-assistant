# Setup Guide

This guide will help you set up and run the RAG Chatbot application.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Groq API key ([Get one here](https://console.groq.com/keys))
- Optional: OpenAI API key (only for OpenAI embeddings)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd poc-rag-chatbot-wiki
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Add your keys to `.env`:
```
GROQ_API_KEY=your-groq-api-key-here
OPENAI_API_KEY=your-openai-api-key-here  # Optional
```

### 5. Verify Installation

Run the example script to verify everything is working:

```bash
python example_usage.py
```

## Running the Application

### Web Interface (Streamlit)

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Command Line Interface

See [example_usage.py](example_usage.py) for programmatic usage examples.

## Project Structure Overview

```
poc-rag-chatbot-wiki/
├── src/chatbot/          # Main application package
│   ├── core/            # Core modules (processing, vector store, RAG)
│   └── utils/           # Utility functions
├── config/              # Configuration and settings
├── data/               # Runtime data (documents, vector stores)
├── logs/               # Application logs
├── tests/              # Test files
├── app.py             # Streamlit web interface
└── example_usage.py   # CLI examples
```

## Configuration

Main configuration settings are in [config/settings.py](config/settings.py).

### Key Settings:

- **Chunk Size**: Default 1000 characters
- **Chunk Overlap**: Default 200 characters
- **Retrieval K**: Default 4 documents
- **Temperature**: Default 0.3
- **LLM Model**: Default "llama-3.1-8b-instant"

## Usage Examples

### 1. Upload and Query a Document

1. Start the web interface: `streamlit run app.py`
2. Enter your Groq API key in the sidebar
3. Upload a PDF, TXT, or MD file
4. Click "Process Document"
5. Start asking questions!

### 2. Save and Reuse Vector Stores

```python
from src.chatbot import DocumentProcessor, VectorStoreManager

# Create and save
processor = DocumentProcessor()
chunks = processor.process_document("my_doc.pdf")

manager = VectorStoreManager(embedding_type="huggingface")
manager.create_vector_store(chunks)
manager.save_vector_store("data/vector_stores/my_index")

# Load later
new_manager = VectorStoreManager(embedding_type="huggingface")
new_manager.load_vector_store("data/vector_stores/my_index")
```

### 3. Programmatic Usage

See [example_usage.py](example_usage.py) for complete examples including:
- Basic Q&A
- Saving/loading vector stores
- Using OpenAI embeddings
- Multi-turn conversations

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the project root:
```bash
cd /path/to/poc-rag-chatbot-wiki
python app.py  # or streamlit run app.py
```

### API Key Issues

- Verify your Groq API key is valid
- Check that `.env` file exists and contains your key
- Ensure no extra spaces in the API key

### Memory Issues

- Reduce chunk size in `config/settings.py`
- Use HuggingFace embeddings instead of OpenAI
- Process smaller documents

### Slow Performance

- Use faster models like `llama3-8b-8192`
- Reduce retrieval K value
- Use HuggingFace embeddings for local processing

## Development

### Adding New Features

1. Core modules go in `src/chatbot/core/`
2. Utility functions go in `src/chatbot/utils/`
3. Update `__init__.py` files to export new functionality

### Running Tests

```bash
# Tests directory is ready for pytest
pytest tests/
```

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Review [example_usage.py](example_usage.py) for code examples
- Open an issue on GitHub for bugs or questions

## Next Steps

1. Try the example usage script: `python example_usage.py`
2. Start the web interface: `streamlit run app.py`
3. Upload your first document and start asking questions!
4. Explore different models and settings for optimal performance

## Resources

- [LangChain Documentation](https://python.langchain.com/)
- [Groq Documentation](https://console.groq.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)
