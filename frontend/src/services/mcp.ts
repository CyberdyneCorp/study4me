/**
 * MCP Service - Handles Model Context Protocol status and management
 * 
 * This service provides functionality to:
 * - Check MCP server status from the backend
 * - Monitor MCP connection health
 * - Provide real-time status updates for UI components
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface McpStatusResponse {
  status: 'running' | 'installed_not_running' | 'not_configured' | 'not_installed' | 'unknown' | 'error'
  server_file_exists: boolean
  config_file_exists: boolean
  server_running: boolean
  server_url: string
  server_url_source: string
  server_error?: string
  environment: {
    openai_api_key_set: boolean
    db_path_set: boolean
    rag_dir_set: boolean
  }
  config?: any
  error?: string
  timestamp: number
}

class McpService {
  private statusCache: McpStatusResponse | null = null
  private lastCheck: number = 0
  private readonly CACHE_DURATION = 30000 // 30 seconds

  /**
   * Get MCP server status from backend
   * Includes caching to avoid excessive API calls
   */
  async getStatus(): Promise<McpStatusResponse> {
    const now = Date.now()
    
    // Return cached result if still valid
    if (this.statusCache && (now - this.lastCheck) < this.CACHE_DURATION) {
      return this.statusCache
    }

    try {
      const response = await fetch(`${API_BASE_URL}/mcp/status`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data: McpStatusResponse = await response.json()
      
      // Update cache
      this.statusCache = data
      this.lastCheck = now
      
      return data
    } catch (error) {
      console.error('Failed to fetch MCP status:', error)
      
      // Return error status
      const errorResponse: McpStatusResponse = {
        status: 'error',
        server_file_exists: false,
        config_file_exists: false,
        environment: {
          openai_api_key_set: false,
          db_path_set: false,
          rag_dir_set: false
        },
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: now
      }
      
      this.statusCache = errorResponse
      this.lastCheck = now
      
      return errorResponse
    }
  }

  /**
   * Check if MCP is enabled based on current status
   */
  async isEnabled(): Promise<boolean> {
    const status = await this.getStatus()
    return status.status === 'running'
  }

  /**
   * Clear the status cache to force refresh on next check
   */
  clearCache(): void {
    this.statusCache = null
    this.lastCheck = 0
  }

  /**
   * Get a human-readable status message
   */
  async getStatusMessage(): Promise<string> {
    const status = await this.getStatus()
    
    switch (status.status) {
      case 'running':
        return `MCP server is running at ${status.server_url} (${status.server_url_source})`
      case 'installed_not_running':
        const urlInfo = status.server_url_source ? ` at ${status.server_url} (${status.server_url_source})` : ''
        const errorMsg = status.server_error ? status.server_error : 'MCP server is installed but not running'
        return errorMsg + urlInfo
      case 'not_configured':
        return 'MCP server is installed but OpenAI API key not set'
      case 'not_installed':
        return 'MCP server file not found'
      case 'unknown':
        return 'MCP server status unknown'
      case 'error':
        return status.error || 'Error checking MCP status'
      default:
        return 'Unknown MCP status'
    }
  }

  /**
   * Get detailed configuration info for debugging
   */
  async getDetailedStatus(): Promise<{
    status: McpStatusResponse
    summary: string
    recommendations: string[]
  }> {
    const status = await this.getStatus()
    const summary = await this.getStatusMessage()
    const recommendations: string[] = []

    if (status.status !== 'running') {
      if (!status.server_file_exists) {
        recommendations.push('Ensure mcp_server.py exists in the backend directory')
      }
      if (!status.environment.openai_api_key_set) {
        recommendations.push('Set OPENAI_API_KEY environment variable')
      }
      if (!status.environment.db_path_set) {
        recommendations.push('Set DB_PATH environment variable')
      }
      if (!status.environment.rag_dir_set) {
        recommendations.push('Set RAG_DIR environment variable')
      }
      if (!status.config_file_exists) {
        recommendations.push('Consider creating mcp_config.json for Claude Desktop integration')
      }
      if (status.status === 'installed_not_running') {
        recommendations.push(`Start the MCP server with: python mcp_server.py --transport http --port 8001`)
        recommendations.push(`Or check if server is accessible at: ${status.server_url}`)
      }
    }

    return {
      status,
      summary,
      recommendations
    }
  }
}

// Export singleton instance
export const mcpService = new McpService()
export default mcpService

// Export types
export type { McpStatusResponse }