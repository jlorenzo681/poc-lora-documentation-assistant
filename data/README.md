# Data Directory

This directory contains runtime data for the RAG Chatbot application.

## Structure

- **documents/**: Store your uploaded documents here (PDF, TXT, MD files)
- **vector_stores/**: Saved FAISS vector store indices are stored here

## Usage

These directories are automatically created by the application and are gitignored to prevent accidentally committing large data files or sensitive documents to version control.

## Notes

- The `documents/` directory is for temporary storage of uploaded files
- The `vector_stores/` directory contains serialized vector indices that can be loaded for faster startup
- Both directories can be safely deleted - they will be recreated as needed
