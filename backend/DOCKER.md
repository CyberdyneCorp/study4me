# Study4Me Backend - Docker Deployment Guide

This guide explains how to deploy the Study4Me backend using Docker with external volume mounting for persistent knowledge graph storage.

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- OpenAI API key
- At least 2GB of available RAM

### 2. Basic Setup

```bash
# Clone the repository
git clone <repository-url>
cd study4me/backend

# Create external data directory
mkdir -p ./data/rag_storage ./data/uploaded_docs ./logs

# Set up environment variables
cp .env.docker.example .env.docker
# Edit .env.docker with your OpenAI API key

# Build and run
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f study4me-backend

# Test API
curl http://localhost:8000/readyz
```

## Docker Configuration

### Dockerfile Features

- **Multi-stage build** for optimized image size
- **Non-root user** for security
- **Health checks** for container orchestration
- **Volume mounts** for persistent data
- **Production-ready** uvicorn configuration

### Volume Mounting

The Docker setup supports external folder mounting for persistent storage:

```yaml
volumes:
  # External knowledge graphs and documents
  - ./data:/app/data
  # External logs
  - ./logs:/app/logs
```

This ensures your knowledge graphs persist between container restarts and updates.

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Basic deployment
docker-compose up -d

# With custom environment file
COMPOSE_FILE=docker-compose.yml docker-compose --env-file .env.docker up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Docker Run

```bash
# Build image
docker build -t study4me-backend .

# Run with volume mounts
docker run -d \
  --name study4me-backend \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_api_key_here \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  study4me-backend
```

### Option 3: Production with External Data

For production deployments with external storage:

```bash
# Create dedicated data directory
sudo mkdir -p /opt/study4me/data
sudo mkdir -p /opt/study4me/logs
sudo chown $USER:$USER /opt/study4me -R

# Update docker-compose.yml volumes
volumes:
  - /opt/study4me/data:/app/data
  - /opt/study4me/logs:/app/logs
```

## Environment Configuration

### Required Environment Variables

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Optional Environment Variables

```bash
# Storage paths (container internal)
RAG_DIR=/app/data/rag_storage
UPLOAD_DIR=/app/data/uploaded_docs
DB_PATH=/app/data/rag_tasks.db

# Performance tuning
MAX_WORKERS=4
YOUTUBE_TIMEOUT=30
WEB_SCRAPING_TIMEOUT=30

# Security
CORS_ORIGINS=https://yourdomain.com
```

## Data Persistence

### Directory Structure

```
./data/                    # Mounted to /app/data in container
├── rag_storage/          # LightRAG knowledge graphs
│   ├── graph_chunk_entity_relation.graphml
│   ├── vdb_entities.json
│   ├── vdb_relationships.json
│   └── ...
├── uploaded_docs/        # User uploaded documents
└── rag_tasks.db         # Task status database

./logs/                   # Application logs (optional)
```

### Backup Strategy

```bash
# Backup knowledge graphs and data
tar -czf study4me-backup-$(date +%Y%m%d).tar.gz ./data

# Restore from backup
tar -xzf study4me-backup-20240125.tar.gz
```

## Monitoring and Maintenance

### Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker inspect study4me-backend | grep -A 5 "Health"

# Manual health check
curl http://localhost:8000/readyz
```

### Log Management

```bash
# View real-time logs
docker-compose logs -f study4me-backend

# View specific number of log lines
docker-compose logs --tail=100 study4me-backend

# Log rotation is configured automatically (10MB max, 3 files)
```

### Resource Monitoring

```bash
# Monitor resource usage
docker stats study4me-backend

# View detailed container info
docker inspect study4me-backend
```

## Scaling and Performance

### Resource Limits

Adjust in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      memory: 4G      # Increase for large knowledge graphs
      cpus: '2.0'     # More CPU for faster processing
    reservations:
      memory: 1G
      cpus: '0.5'
```

### Multiple Workers

For high-traffic deployments:

```bash
# Update CMD in Dockerfile
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4"]
```

## Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker-compose logs study4me-backend
   
   # Verify environment variables
   docker-compose config
   ```

2. **Permission errors**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER ./data ./logs
   ```

3. **OpenAI API key errors**
   ```bash
   # Verify environment variable
   docker exec study4me-backend printenv OPENAI_API_KEY
   ```

4. **Memory issues**
   ```bash
   # Increase memory limits in docker-compose.yml
   # Monitor usage: docker stats
   ```

### Debug Mode

```bash
# Run in debug mode
docker run -it --rm \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  study4me-backend \
  uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug
```

## Security Considerations

### Production Security

1. **Use specific CORS origins**
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
   ```

2. **Run behind reverse proxy**
   ```yaml
   # nginx-proxy service in docker-compose.yml
   ```

3. **Use secrets management**
   ```bash
   # Use Docker secrets instead of environment variables
   echo "your_api_key" | docker secret create openai_api_key -
   ```

4. **Regular updates**
   ```bash
   # Rebuild with latest security patches
   docker-compose pull
   docker-compose up -d --build
   ```

## Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/study4me"
mkdir -p $BACKUP_DIR

# Stop container
docker-compose stop study4me-backend

# Create backup
tar -czf "$BACKUP_DIR/study4me_$DATE.tar.gz" ./data

# Start container
docker-compose start study4me-backend

echo "Backup completed: $BACKUP_DIR/study4me_$DATE.tar.gz"
```

### Recovery Process

```bash
# Stop services
docker-compose down

# Restore data
tar -xzf /backups/study4me/study4me_20240125_143000.tar.gz

# Start services
docker-compose up -d
```