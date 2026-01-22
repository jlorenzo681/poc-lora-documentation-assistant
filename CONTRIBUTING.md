# Contributing to LoRA RAG Chatbot

Thank you for your interest in contributing! This document provides guidelines for setting up your development environment and submitting contributions.

## Development Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd poc-lora-documentation-assistant
    ```

2.  **Install dependencies:**
    We recommend using a virtual environment (venv) or `uv`:
    ```bash
    # Using pip
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -e ".[dev]" # Install dev dependencies
    ```

3.  **Set up Pre-commit (Optional but recommended):**
    Ensure `ruff` is installed for linting.

## Project Structure

- `src/`: Source code
    - `backend/`: FastAPI application
    - `chatbot/`: Core RAG logic
    - `schemas/`: Pydantic models
- `tests/`: Unit and integration tests
- `config/`: Configuration settings
- `data/`: Local data storage (documents, vector stores)

## Coding Standards

- **Linting**: We use `ruff` for linting and formatting.
    ```bash
    ruff check .
    ruff format .
    ```
- **Testing**: All new features must include unit tests.
    ```bash
    pytest tests/
    ```
- **Type Hinting**: Use Python type hints for all function signatures.

## Pull Request Process

1.  Create a new branch for your feature or fix: `git checkout -b feature/my-feature`
2.  Make your changes and ensure tests pass.
3.  Commit your changes with descriptive messages.
4.  Push to your fork and submit a Pull Request.
5.  Wait for CI checks to pass.

## Architecture

See the README for high-level architecture details.
