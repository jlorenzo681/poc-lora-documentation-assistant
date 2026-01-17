# Quick Start Guide

Get the RAG Chatbot running in minutes!

## 🚀 Fastest Way to Deploy

### Using Podman (Recommended for Production)

```bash
# 1. Clone and navigate
git clone <your-repo-url>
cd poc-rag-chatbot-wiki

# 2. Set up API key
cp .env.example .env
echo "GROQ_API_KEY=your-key-here" > .env

# 3. Deploy!
make deploy

# Visit: http://localhost:8501
```

### Using Python (Local Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export GROQ_API_KEY='your-key-here'

# 3. Run!
streamlit run app.py

# Visit: http://localhost:8501
```

## 📋 Common Commands

### Podman Deployment

```bash
make deploy          # Deploy application
make logs            # View logs
make stop            # Stop application
make restart         # Restart application
make shell           # Open container shell
make clean           # Remove containers
```

### Local Development

```bash
streamlit run app.py              # Start web interface
python example_usage.py           # Run CLI examples
make test                         # Run tests
```

## 🔑 Getting Your API Key

1. Visit [Groq Console](https://console.groq.com/keys)
2. Sign up or log in
3. Create a new API key
4. Copy the key to your `.env` file

## 📝 First Steps After Deployment

1. **Open the app**: Navigate to `http://localhost:8501`
2. **Enter API key**: Paste your Groq API key in the sidebar
3. **Upload a document**: Choose a PDF, TXT, or MD file
4. **Process document**: Click the "Process Document" button
5. **Ask questions**: Start chatting!

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Find what's using port 8501
sudo ss -tulpn | grep 8501

# Kill the process or change port
podman run -p 8080:8501 ...
```

### API Key Not Working
```bash
# Verify your .env file
cat .env | grep GROQ_API_KEY

# Make sure no extra spaces or quotes
```

### Container Won't Start
```bash
# Check logs
podman logs rag-chatbot

# Rebuild image
make clean
make build
make deploy
```

## 📚 Learn More

- **Full Documentation**: See [README.md](README.md)
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Setup Instructions**: See [SETUP.md](SETUP.md)
- **Architecture Details**: See [STRUCTURE.md](STRUCTURE.md)

## 🎯 What's Next?

- Try different LLM models (llama-3.1-8b-instant, compound)
- Experiment with temperature settings
- Upload larger documents
- Save and reuse vector stores
- Deploy with systemd for auto-start

## 💡 Tips

- Use HuggingFace embeddings for free, local processing
- Lower temperature (0.1-0.3) for factual answers
- Higher temperature (0.5-0.7) for creative responses
- Retrieval K=4 is usually optimal
- Check out [example_usage.py](example_usage.py) for programmatic usage
