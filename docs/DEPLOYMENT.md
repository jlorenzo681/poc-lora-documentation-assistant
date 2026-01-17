# Deployment Guide

This guide covers deploying the RAG Chatbot using Podman containerization.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Methods](#deployment-methods)
  - [Method 1: Using Scripts (Recommended)](#method-1-using-scripts-recommended)
  - [Method 2: Using Makefile](#method-2-using-makefile)
  - [Method 3: Manual Podman Commands](#method-3-manual-podman-commands)
  - [Method 4: Podman Compose](#method-4-podman-compose)
  - [Method 5: Systemd Service](#method-5-systemd-service)
- [Configuration](#configuration)
- [Production Considerations](#production-considerations)
- [Monitoring and Logs](#monitoring-and-logs)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- **Podman** 4.0 or higher ([Installation Guide](https://podman.io/getting-started/installation))
- **Python** 3.10+ (for local development)
- **Groq API Key** ([Get one here](https://console.groq.com/keys))

### Optional

- **podman-compose** (for compose-based deployment)
- **make** (for Makefile commands)

### Installation Check

```bash
# Verify Podman installation
podman --version

# Verify Python installation
python3 --version

# Check system requirements
make check
```

## Quick Start

The fastest way to deploy:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd poc-rag-chatbot-wiki

# 2. Set up environment variables
cp .env.example .env
nano .env  # Add your GROQ_API_KEY

# 3. Deploy with one command
make deploy
```

The application will be available at `http://localhost:8501`

## Deployment Methods

### Method 1: Using Scripts (Recommended)

The deployment scripts provide automated setup and error checking.

```bash
# Deploy the application
./scripts/deploy.sh

# View logs
./scripts/logs.sh

# Stop the application
./scripts/stop.sh

# Rebuild the image
./scripts/build.sh
```

**Features:**
- Automatic dependency checking
- Environment validation
- Health check verification
- Colored output for easy reading

### Method 2: Using Makefile

Simple commands for common operations:

```bash
# Build container image
make build

# Deploy application
make deploy

# View logs
make logs

# Stop application
make stop

# Restart application
make restart

# Open shell in container
make shell

# Clean up everything
make clean
```

### Method 3: Manual Podman Commands

For full control over deployment:

#### Build the Image

```bash
podman build -t rag-chatbot:latest -f Containerfile .
```

#### Run the Container

```bash
podman run -d \
  --name rag-chatbot \
  -p 8501:8501 \
  --env-file .env \
  -v ./data/documents:/app/data/documents:z \
  -v ./data/vector_stores:/app/data/vector_stores:z \
  -v ./logs:/app/logs:z \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  rag-chatbot:latest
```

#### Manage the Container

```bash
# View logs
podman logs -f rag-chatbot

# Stop container
podman stop rag-chatbot

# Remove container
podman rm rag-chatbot

# Container status
podman ps -a

# Resource usage
podman stats rag-chatbot
```

### Method 4: Podman Compose

Using `podman-compose.yml` for orchestration:

#### Install podman-compose

```bash
pip install podman-compose
```

#### Deploy

```bash
# Start services
podman-compose up -d

# View logs
podman-compose logs -f

# Stop services
podman-compose down

# Restart services
podman-compose restart
```

### Method 5: Systemd Service

Run as a system service that starts automatically on boot.

#### Setup

1. Edit the service file with your project path:
   ```bash
   nano deployment/systemd/rag-chatbot.service
   # Update /path/to/your/project
   ```

2. Install the service:
   ```bash
   # User service (recommended)
   mkdir -p ~/.config/systemd/user
   cp deployment/systemd/rag-chatbot.service ~/.config/systemd/user/
   systemctl --user daemon-reload

   # Enable and start
   systemctl --user enable rag-chatbot
   systemctl --user start rag-chatbot
   ```

3. Enable auto-start on boot:
   ```bash
   loginctl enable-linger $USER
   ```

#### Management

```bash
# Check status
systemctl --user status rag-chatbot

# View logs
journalctl --user -u rag-chatbot -f

# Restart
systemctl --user restart rag-chatbot

# Stop
systemctl --user stop rag-chatbot
```

See [deployment/systemd/README.md](deployment/systemd/README.md) for more details.

## Configuration

### Environment Variables

Create a `.env` file with your configuration:

```bash
# Required
GROQ_API_KEY=your-groq-api-key-here

# Optional
OPENAI_API_KEY=your-openai-api-key-here
```

### Port Configuration

Default port is `8501`. To change:

**In Containerfile:**
```dockerfile
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

**Update port mapping:**
```bash
podman run -p 8080:8080 ...
```

### Volume Mounts

The application uses three persistent volumes:

- `./data/documents` - Uploaded documents
- `./data/vector_stores` - FAISS indices
- `./logs` - Application logs

**Important:** The `:z` option is required for SELinux systems.

## Production Considerations

### Security

The container is configured with security best practices:

- Runs as non-root user (UID 1000)
- Minimal capabilities (`no-new-privileges`)
- Dropped all capabilities except `NET_BIND_SERVICE`
- No privileged mode
- Read-only root filesystem possible (with volume mounts)

### Resource Limits

Add resource constraints for production:

```bash
podman run \
  --memory=2g \
  --memory-swap=2g \
  --cpus=2 \
  ...
```

### Reverse Proxy

For production, use a reverse proxy (nginx, Traefik, Caddy):

**Nginx example:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### HTTPS/TLS

Use Caddy for automatic HTTPS:

```bash
podman run -d \
  --name caddy \
  -p 80:80 -p 443:443 \
  -v $PWD/Caddyfile:/etc/caddy/Caddyfile \
  -v caddy_data:/data \
  caddy:latest
```

**Caddyfile:**
```
your-domain.com {
    reverse_proxy localhost:8501
}
```

### Backup Strategy

```bash
# Backup vector stores
tar -czf backup-$(date +%Y%m%d).tar.gz data/vector_stores/

# Restore
tar -xzf backup-20250115.tar.gz
```

## Monitoring and Logs

### View Container Logs

```bash
# Real-time logs
podman logs -f rag-chatbot

# Last 100 lines
podman logs --tail 100 rag-chatbot

# With timestamps
podman logs -t rag-chatbot
```

### Health Check

The container includes a health check:

```bash
# Check health status
podman inspect rag-chatbot | grep -A 10 Health

# Manual health check
curl http://localhost:8501/_stcore/health
```

### Resource Monitoring

```bash
# Real-time stats
podman stats rag-chatbot

# Container info
podman inspect rag-chatbot
```

### Application Logs

Application logs are stored in `./logs/` directory:

```bash
# View application logs
tail -f logs/*.log
```

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
podman logs rag-chatbot
```

**Common issues:**
- Missing `.env` file
- Invalid API key
- Port already in use
- Permission issues with volumes

**Solutions:**
```bash
# Check if port is in use
ss -tulpn | grep 8501

# Fix volume permissions
chmod -R 755 data/
chown -R $(id -u):$(id -g) data/

# Verify .env file
cat .env | grep GROQ_API_KEY
```

### Image Build Fails

**Clear build cache:**
```bash
podman system prune -a
podman build --no-cache -t rag-chatbot:latest -f Containerfile .
```

### Permission Denied on Volumes

For SELinux systems, ensure `:z` flag on volumes:
```bash
-v ./data/documents:/app/data/documents:z
```

### Can't Access Application

**Check container is running:**
```bash
podman ps | grep rag-chatbot
```

**Check firewall:**
```bash
# Allow port through firewall
sudo firewall-cmd --add-port=8501/tcp --permanent
sudo firewall-cmd --reload
```

**Test locally:**
```bash
curl http://localhost:8501/_stcore/health
```

### High Memory Usage

**Set memory limits:**
```bash
podman run --memory=2g --memory-swap=2g ...
```

**Use HuggingFace embeddings instead of OpenAI** (uses less memory)

### Slow Performance

**Optimize:**
- Use faster models (llama3-8b-8192)
- Reduce chunk size
- Lower retrieval K value
- Allocate more CPU cores: `--cpus=4`

## Advanced Deployment

### Pod Deployment

Deploy as a Podman pod with multiple containers:

```bash
# Create pod
podman pod create --name rag-pod -p 8501:8501

# Run application in pod
podman run -d --pod rag-pod --name rag-app rag-chatbot:latest

# Add nginx reverse proxy to pod
podman run -d --pod rag-pod --name rag-nginx nginx:alpine
```

### Kubernetes/OpenShift

Generate Kubernetes YAML:

```bash
podman generate kube rag-chatbot > rag-chatbot-k8s.yaml
kubectl apply -f rag-chatbot-k8s.yaml
```

### Auto-update

Enable automatic image updates:

```bash
# Add label to container
podman run -d \
  --label "io.containers.autoupdate=registry" \
  --name rag-chatbot \
  rag-chatbot:latest

# Enable auto-update service
systemctl --user enable podman-auto-update.timer
```

## Performance Tuning

### Container Optimization

```bash
podman run \
  --cpus=4 \
  --memory=4g \
  --memory-swap=4g \
  --pids-limit=200 \
  --shm-size=1g \
  ...
```

### Application Tuning

Edit [config/settings.py](config/settings.py):
- Adjust chunk size/overlap
- Change retrieval K value
- Modify temperature settings

## Support

For issues or questions:

1. Check [README.md](README.md) for general documentation
2. Review [SETUP.md](SETUP.md) for installation help
3. Check logs: `podman logs rag-chatbot`
4. Open an issue on GitHub

## Next Steps

After deployment:

1. Access the application: `http://localhost:8501`
2. Configure API keys in the sidebar
3. Upload a test document
4. Start asking questions!

For production deployment:
1. Set up reverse proxy with HTTPS
2. Configure systemd service
3. Implement backup strategy
4. Set up monitoring and alerts
