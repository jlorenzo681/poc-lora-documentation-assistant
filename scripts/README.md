# Deployment Scripts

This directory contains scripts for managing the RAG Chatbot deployment with Podman.

## Available Scripts

### `deploy.sh`
Deploy the RAG Chatbot with both rag-chatbot and Ollama services using docker-compose.

```bash
# Basic deployment
./scripts/deploy.sh

# Deploy and pull all Ollama models
./scripts/deploy.sh --pull-models

# Deploy and pull a specific model
./scripts/deploy.sh --pull-model llama3.2:3b
```

**Options:**
- `--pull-models` - Pull all available Ollama models after deployment
- `--pull-model MODEL` - Pull a specific Ollama model (e.g., llama3.2:3b)

### `dev.sh`
Start development mode with hot reload for code changes while using compose for Ollama.

```bash
# Basic dev mode
./scripts/dev.sh

# Dev mode with model pulling
./scripts/dev.sh --pull-models

# Dev mode with specific model
./scripts/dev.sh --pull-model llama3.2:3b
```

**Features:**
- Hot reload for `app.py`, `src/`, `config/`, and `.streamlit/`
- Uses docker-compose for Ollama service
- Development container connected to compose network

**Options:**
- `--pull-models` - Pull all available Ollama models after starting
- `--pull-model MODEL` - Pull a specific Ollama model

### `pull-ollama-models.sh`
Pull Ollama models that are available in the app's model selector.

```bash
# Pull all models
./scripts/pull-ollama-models.sh --all

# Pull specific models
./scripts/pull-ollama-models.sh llama3.2:3b mistral:latest

# Pull single model
./scripts/pull-ollama-models.sh llama3.2:3b
```

**Available Models:**
- `deepseek-r1:8b` (~5.2 GB)
- `llama3.2:3b` (~2.0 GB)

**Note:** The Ollama container must be running before pulling models.

### `build.sh`
Build the RAG Chatbot container image.

```bash
./scripts/build.sh
```

### `stop.sh`
Stop all services (rag-chatbot and Ollama).

```bash
./scripts/stop.sh
```

### `logs.sh`
View container logs.

```bash
# View rag-chatbot logs (default)
./scripts/logs.sh

# View Ollama logs
./scripts/logs.sh ollama

# View all logs (requires podman-compose)
./scripts/logs.sh all
```

### `clean.sh`
Clean up containers, images, volumes, and networks.

```bash
# Remove containers only
./scripts/clean.sh

# Remove containers and images
./scripts/clean.sh --images

# Remove containers and volumes (Ollama models)
./scripts/clean.sh --volumes

# Remove everything
./scripts/clean.sh --all
```

**Options:**
- `--images` - Also remove container images
- `--volumes` - Also remove volumes (this will delete Ollama models!)
- `--all` - Remove everything (images + volumes)

## Quick Start

1. **First time setup:**
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY

   # Deploy and pull default model
   ./scripts/deploy.sh --pull-model llama3.2:3b
   ```

2. **Development:**
   ```bash
   # Start dev mode with hot reload
   ./scripts/dev.sh --pull-model llama3.2:3b
   ```

3. **View logs:**
   ```bash
   # Watch application logs
   ./scripts/logs.sh

   # Watch Ollama logs
   ./scripts/logs.sh ollama
   ```

4. **Stop services:**
   ```bash
   ./scripts/stop.sh
   ```

## Architecture

All scripts now use `docker-compose.yml` to manage both services:
- **rag-chatbot**: Streamlit web application
- **ollama**: Local LLM inference server

Both containers are on the same network (`poc-rag-chatbot-wiki_rag-network`) and can communicate via hostname resolution.

## Troubleshooting

**Ollama connection refused:**
- Ensure both containers are running: `docker ps`
- Check they're on the same network: `docker network inspect poc-rag-chatbot-wiki_rag-network`
- Restart with compose: `./scripts/stop.sh && ./scripts/deploy.sh`

**Models not found:**
- Pull models: `./scripts/pull-ollama-models.sh llama3.2:3b`
- List models: `docker exec ollama ollama list`

**Network issues:**
- Always use `./scripts/deploy.sh` or `docker-compose up -d` to start services
- Never start containers individually with `docker run`
