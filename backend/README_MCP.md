# Study4Me MCP Server

This directory contains an MCP (Model Context Protocol) server built with FastMCP v2 that provides access to the Study4Me backend functionality.

## Features

The MCP server exposes three main tools:

### 1. `get_content_from_study`
Get all content for a specific study topic.

**Parameters:**
- `study_topic_id` (string): The UUID of the study topic

**Returns:**
- Complete topic information including all content items
- Content statistics (token counts, content length)
- Individual content items with full text

### 2. `query_study` 
Query a specific study topic using either LightRAG (for knowledge graph enabled topics) or ChatGPT with context.

**Parameters:**
- `study_topic_id` (string): The UUID of the study topic to query
- `query` (string): The question to ask
- `mode` (string, optional): RAG mode for LightRAG queries (default: "hybrid")

**Returns:**
- Query results
- Processing method used (LightRAG or ChatGPT+Context)
- Topic metadata

### 3. `list_all_studies`
List all study topics with their metadata and optionally content counts and summaries.

**Parameters:**
- `include_content_count` (boolean, optional): Whether to include content item counts (default: true)
- `include_summary` (boolean, optional): Whether to include cached summaries (default: true)

**Returns:**
- Complete list of all study topics
- Content statistics for each topic
- Cached summaries if available

## Setup

1. **Install Dependencies:**
   ```bash
   pip install fastmcp
   ```

2. **Environment Configuration:**
   Ensure these environment variables are set in your `config.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   DB_PATH=./rag_tasks.db
   RAG_DIR=./rag_storage
   ```

3. **Run the Server:**
   
   **For Claude Desktop (STDIO transport):**
   ```bash
   python mcp_server.py --transport stdio
   # or simply
   python mcp_server.py
   ```
   
   **For HTTP transport (debugging/testing):**
   ```bash
   python mcp_server.py --transport http --port 8001
   ```
   
   **Command-line options:**
   - `--transport {stdio,http}`: Transport type (default: stdio)
   - `--port PORT`: Port for HTTP transport (default: 8001)
   - `--host HOST`: Host for HTTP transport (default: 127.0.0.1)

## Configuration for Claude Desktop

### Option 1: STDIO Transport (Recommended)

```json
{
  "mcpServers": {
    "study4me": {
      "command": "python",
      "args": ["/absolute/path/to/study4me/backend/mcp_server.py", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here"
      }
    }
  }
}
```

### Option 2: HTTP Transport (For Testing)

First start the server manually:
```bash
python mcp_server.py --transport http --port 8001
```

Then configure Claude Desktop:
```json
{
  "mcpServers": {
    "study4me": {
      "url": "http://127.0.0.1:8001/mcp/"
    }
  }
}
```

**Note:** For HTTP transport, ensure your environment variables are set where you run the MCP server.

## Usage Examples

Once connected through an MCP client (like Claude Desktop), you can:

1. **List all available studies:**
   ```
   Please use the list_all_studies tool to show me all available study topics.
   ```

2. **Get content from a specific study:**
   ```
   Use get_content_from_study with topic ID "409159f9-11fa-4dd1-aaa0-56697278885c" to show me all content for that study.
   ```

3. **Query a study topic:**
   ```
   Use query_study to ask "What are the main concepts in machine learning?" for topic ID "409159f9-11fa-4dd1-aaa0-56697278885c".
   ```

## Technical Details

- **Framework:** FastMCP v2
- **Transport:** HTTP (127.0.0.1:8001/mcp/)
- **Database:** SQLite (async)
- **RAG Engine:** LightRAG for knowledge graph queries
- **Fallback:** ChatGPT with context for non-knowledge graph topics
- **Content Support:** Documents, webpages, YouTube transcripts, images

## File Structure

```
backend/
├── mcp_server.py          # Main MCP server implementation
├── mcp_config.json        # Example MCP configuration
├── test_mcp.py           # Testing script
├── utils/
│   ├── db_async.py       # Database functions
│   └── utils_async.py    # Utility functions
└── rag_storage/          # LightRAG knowledge graphs
    └── topic_{uuid}/     # Per-topic RAG instances
```

## Troubleshooting

1. **Database not found:** Ensure the `rag_tasks.db` file exists and is accessible
2. **OpenAI API errors:** Verify your API key is valid and has sufficient credits
3. **Import errors:** Run the server from the backend directory where utils/ is available
4. **Permission errors:** Ensure the server has read/write access to the database and RAG storage directories

## Integration with Main Backend

This MCP server integrates seamlessly with the main Study4Me FastAPI backend:
- Shares the same database (`rag_tasks.db`)
- Uses the same RAG storage directory structure
- Leverages existing utility functions and models
- Maintains consistency with the web API functionality