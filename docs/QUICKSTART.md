# Quick Start Guide

Get the LoRA RAG Chatbot running in minutes on your Mac!

## 🚀 Fast Track (Local)

### 1. Start LM Studio
1.  Open **LM Studio**.
2.  Load a model (e.g., `Llama-3` or `Mistral`).
3.  Start the **Local Server** on port `1234`.

### 2. Setup & Run
```bash
# Clone
git clone <your-repo-url>
cd poc-lora-documentation-assistant

# Install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
streamlit run app.py
```

Visit **http://localhost:8501** in your browser.

## 📝 Usage

1.  **Select Provider**: In the sidebar, verify "LLM Provider" is set to "mlx" (default for Apple Silicon) or "lmstudio" for LM Studio.
2.  **Upload Document**: Drag & drop a PDF, Markdown, or Text file.
3.  **Process**: Click "Process Document" to create the knowledge base.
4.  **Visualize**: Switch to the **Graph View** tab to see document entity relationships.
5.  **Chat**: Ask questions about your document!
6.  **Observe**: Check your traces at **http://localhost:3000** (Langfuse).

## 💡 Configuration Tips
-   **Model Selection**: The chatbot uses whatever model is loaded in LM Studio.
-   **Direct Inference**: If you choose "MLX" provider in the UI, the app will load the model directly into RAM using apple silicon optimization (no LM Studio needed), but this requires downloading the MLX-format weights to `data/models` or specifying a HuggingFace repo ID.
