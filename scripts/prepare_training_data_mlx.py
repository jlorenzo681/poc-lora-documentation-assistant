
import os
import glob
import json
import argparse
from pathlib import Path
from typing import List, Dict

# Try to import langchain components, fall back if not available (though they should be based on pyproject.toml)
try:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    print("LangChain dependencies not found. Please install them.")
    exit(1)

def load_documents(data_dir: str) -> List[str]:
    """Load documents from the data directory."""
    documents = []
    
    # PDF files
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    for pdf_file in pdf_files:
        print(f"Loading {pdf_file}...")
        try:
            loader = PyPDFLoader(pdf_file)
            docs = loader.load()
            for doc in docs:
                documents.append(doc.page_content)
        except Exception as e:
            print(f"Error loading {pdf_file}: {e}")

    # specific markdown and text files mentioned in list_dir
    # We can use a glob for these too
    text_extensions = ["*.txt", "*.md"]
    for ext in text_extensions:
        files = glob.glob(os.path.join(data_dir, ext))
        for file_path in files:
            print(f"Loading {file_path}...")
            try:
                if file_path.endswith(".md"):
                     # Simple read for now to avoid 'unstructured' dep if not present, or use TextLoader
                     with open(file_path, 'r', encoding='utf-8') as f:
                         documents.append(f.read())
                else:
                    loader = TextLoader(file_path)
                    docs = loader.load()
                    for doc in docs:
                        documents.append(doc.page_content)
            except Exception as e:
                 print(f"Error loading {file_path}: {e}")
                 
    return documents

def prepare_data(data_dir: str, output_dir: str, chunk_size: int = 1024, chunk_overlap: int = 100):
    """
    Load documents, chunk them, and save as JSONL for MLX training.
    Format: {"text": "<content>"}
    """
    raw_texts = load_documents(data_dir)
    print(f"Loaded {len(raw_texts)} document source(s).")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    all_chunks = []
    for text in raw_texts:
        chunks = text_splitter.split_text(text)
        all_chunks.extend(chunks)
    
    print(f"Generated {len(all_chunks)} chunks.")

    # Split into train and valid (90/10)
    split_idx = int(len(all_chunks) * 0.9)
    train_chunks = all_chunks[:split_idx]
    valid_chunks = all_chunks[split_idx:]

    os.makedirs(output_dir, exist_ok=True)
    
    train_file = os.path.join(output_dir, "train.jsonl")
    valid_file = os.path.join(output_dir, "valid.jsonl")

    with open(train_file, "w", encoding='utf-8') as f:
        for chunk in train_chunks:
            # Clean up newlines slightly to make it continuous text, or keep as is.
            # For simplicity, we keep as is but format as json.
            entry = {"text": chunk}
            f.write(json.dumps(entry) + "\n")
            
    with open(valid_file, "w", encoding='utf-8') as f:
        for chunk in valid_chunks:
            entry = {"text": chunk}
            f.write(json.dumps(entry) + "\n")

    print(f"Saved {len(train_chunks)} training examples to {train_file}")
    print(f"Saved {len(valid_chunks)} validation examples to {valid_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare data for MLX training")
    parser.add_argument("--data_dir", type=str, default="data/documents", help="Directory containing source documents")
    parser.add_argument("--output_dir", type=str, default="data/mlx_data", help="Output directory for JSONL files")
    parser.add_argument("--chunk_size", type=int, default=2048, help="Token/char chunk size")
    args = parser.parse_args()

    # Ensure paths are relative to project root or absolute
    base_path = Path(__file__).resolve().parent.parent
    data_dir = base_path / args.data_dir
    output_dir = base_path / args.output_dir

    prepare_data(str(data_dir), str(output_dir), chunk_size=args.chunk_size)
