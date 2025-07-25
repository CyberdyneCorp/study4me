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

### Debug & Health
- `GET /` - Basic health check and service status
- `GET /readyz` - Kubernetes readiness probe endpoint

### Knowledge Upload
- `POST /documents/upload` - Upload and process documents (PDF, DOCX, XLS, XLSX)
- `POST /webpage/process` - Process web page content with background processing
- `POST /youtube/process` - Process YouTube video transcripts and add to knowledge base
- `POST /image/interpret` - Analyze images with OpenAI Vision API

### Datasource Management
- `GET /datasources` - List all uploaded documents with metadata
- `GET /datasources/{filename}/info` - Get detailed document metadata
- `GET /datasources/{filename}/download` - Download specific document
- `DELETE /datasources/{filename}` - Delete document from storage

### YouTube Processing
- `GET /youtube/transcript` - Get transcript for single video with language support
- `POST /youtube/batch` - Process multiple YouTube videos in batch

### Knowledge Graph
- `GET /graph/json` - Get knowledge graph as JSON with nodes and edges
- `GET /graph/graphml` - Download GraphML file for external analysis
- `GET /graph/png` - Render and download knowledge graph as PNG image

### AI Querying
- `GET /query` - Synchronous queries with multiple modes (naive, local, global, hybrid)
- `POST /query-async` - Asynchronous queries with background processing and callback support

### Task Management
- `GET /task-status/{task_id}` - Check background task status and retrieve results

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

The application uses FastAPI's `BackgroundTasks` for processing with graceful shutdown:

1. **File Upload**: Documents are saved immediately, processed in background
2. **Task Tracking**: Each background task gets a unique ID for status tracking
3. **Status Updates**: Tasks update status in SQLite database
4. **Callbacks**: Optional webhook callbacks for task completion
5. **Graceful Shutdown**: Background tasks are properly cancelled on server shutdown
6. **Error Handling**: Comprehensive OpenAI API error handling with structured responses

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

1. **OpenAI API Key Error**: 
   - Server fails gracefully at startup with clear error messages
   - Ensure `OPENAI_API_KEY` is set in environment or .env file
   - Replace placeholder values with actual API key
2. **File Upload Errors**: Check file permissions and disk space
3. **YouTube Errors**: yt-dlp may need updates for new YouTube changes
4. **Memory Issues**: Large documents may require chunking strategies
5. **Shutdown Issues**: 
   - Server now handles Ctrl+C gracefully with 5-second timeout
   - Background tasks are properly cancelled on shutdown

### Debugging

The application includes comprehensive logging for debugging and performance monitoring:

1. **Startup/Shutdown Logging**: Clear messages for server lifecycle events
2. **Task Processing**: Detailed logs with unique IDs for each background task
3. **Performance Metrics**: Processing times for each phase of operations
4. **Error Details**: Structured error information with context
5. **OpenAI API Monitoring**: Request/response logging with rate limit handling

Enable debug logging:
```bash
uvicorn main:app --reload --log-level debug
```

Log patterns to watch for:
- `🚀` Server startup events
- `📺` YouTube processing
- `🧠` LightRAG operations
- `📡` Callback notifications
- `❌` Error conditions
- `✅` Successful completions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code formatting compliance
5. Submit a pull request