# Study4Me Backend

FastAPI backend server for the Study4Me application, providing APIs for document processing, knowledge graph generation, and AI-powered querying.

## Features

- **Document Processing**: Upload and process PDFs, Word documents, and Excel files using Docling
- **YouTube Integration**: Extract transcripts from YouTube videos using yt-dlp
- **Web Scraping**: Process web pages and articles using Trafilatura
- **Image Analysis**: Analyze images using OpenAI Vision API
- **Knowledge Graph**: Generate interactive knowledge graphs using LightRAG
- **AI Querying**: Natural language queries with multiple modes (naive, local, global, hybrid)
- **Background Processing**: Asynchronous task processing with status tracking
- **RESTful API**: Comprehensive REST API with automatic OpenAPI documentation

## Tech Stack

- **Framework**: FastAPI with async/await support
- **Document Processing**: Docling for PDFs, Word, Excel
- **AI/LLM**: OpenAI GPT-4 and embeddings via LightRAG
- **Knowledge Graph**: LightRAG with NetworkX visualization
- **YouTube**: yt-dlp for transcript extraction
- **Database**: SQLite with aiosqlite for async operations
- **HTTP Client**: httpx for external API calls
- **Environment**: python-dotenv for configuration

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `config.env` and update with your API keys:

```bash
cp config.env .env
# Edit .env with your OpenAI API key
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key for LLM and embeddings

### 3. Run the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000

# With custom log level
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
```

### 4. API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## API Endpoints

### Document Processing
- `POST /documents/upload` - Upload and process documents
- `GET /datasources` - List all uploaded documents
- `GET /datasources/{filename}/info` - Get document metadata
- `GET /datasources/{filename}/download` - Download document
- `DELETE /datasources/{filename}` - Delete document

### YouTube Processing
- `GET /youtube/transcript` - Get transcript for single video
- `POST /youtube/batch` - Process multiple videos

### Web Content
- `POST /webpage/process` - Process web page content

### Image Analysis
- `POST /image/interpret` - Analyze images with AI

### Knowledge Graph
- `GET /graph/json` - Get graph as JSON
- `GET /graph/graphml` - Download GraphML file
- `GET /graph/png` - Render graph as PNG

### Querying
- `GET /query` - Synchronous queries
- `POST /query-async` - Asynchronous queries with callback support

### Task Management
- `GET /task-status/{task_id}` - Check background task status

## Architecture

### Directory Structure
```
backend/
├── main.py              # FastAPI application and routes
├── youtube_service.py   # YouTube transcript processing
├── requirements.txt    # Python dependencies
├── config.env         # Environment configuration template
├── utils/
│   ├── __init__.py
│   ├── db_async.py     # Database operations
│   ├── utils_async.py  # Background processing utilities
│   └── utils_ws.py     # Webhook/callback utilities
└── README.md          # This file
```

### Background Processing

The application uses FastAPI's `BackgroundTasks` for processing:

1. **File Upload**: Documents are saved immediately, processed in background
2. **Task Tracking**: Each background task gets a unique ID for status tracking
3. **Status Updates**: Tasks update status in SQLite database
4. **Callbacks**: Optional webhook callbacks for task completion

### LightRAG Integration

- **Initialization**: LightRAG instance created at startup with OpenAI integration
- **Document Ingestion**: Documents converted to markdown, then inserted into RAG
- **Knowledge Graph**: Entities and relationships extracted automatically
- **Query Modes**: 
  - `naive`: Simple text search
  - `local`: Local context search
  - `global`: Global knowledge search
  - `hybrid`: Combined approach (default)

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
flake8 .
```

### Adding New Endpoints

1. Add route to `main.py`
2. Implement business logic in appropriate service module
3. Add background processing function to `utils/utils_async.py` if needed
4. Update this README

## Production Deployment

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

Set these in production:
- `OPENAI_API_KEY`: Your OpenAI API key
- Configure uvicorn directly via command line arguments for host, port, and log level

### Scaling Considerations

- Use a proper ASGI server like Gunicorn with Uvicorn workers
- Consider Redis for task queue instead of in-memory storage
- Use a proper database like PostgreSQL for production
- Implement rate limiting and authentication as needed

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Ensure `OPENAI_API_KEY` is set in environment
2. **File Upload Errors**: Check file permissions and disk space
3. **YouTube Errors**: yt-dlp may need updates for new YouTube changes
4. **Memory Issues**: Large documents may require chunking strategies

### Debugging

Enable debug logging by setting `LOG_LEVEL=debug` in your environment.

Check logs for detailed processing information:
```bash
uvicorn main:app --reload --log-level debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code formatting compliance
5. Submit a pull request