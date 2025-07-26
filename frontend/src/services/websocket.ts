/**
 * WebSocket Service for Real-time Backend Communication
 * 
 * This service provides WebSocket functionality to receive real-time updates
 * from the backend for async operations like document processing, webpage scraping,
 * and YouTube video processing.
 */

import { notificationService } from './notifications'

interface TaskUpdate {
  task_id: string
  status: 'processing' | 'done' | 'failed'
  message?: string
  progress?: number
  result?: any
  error?: string
}

type TaskUpdateCallback = (update: TaskUpdate) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private taskCallbacks = new Map<string, TaskUpdateCallback[]>()
  private isConnecting = false

  constructor(private baseUrl: string = 'ws://localhost:8000') {}

  /**
   * Connect to the WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      if (this.isConnecting) {
        // If already connecting, wait for that connection
        const checkConnection = () => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            resolve()
          } else if (!this.isConnecting) {
            reject(new Error('Connection failed'))
          } else {
            setTimeout(checkConnection, 100)
          }
        }
        checkConnection()
        return
      }

      this.isConnecting = true
      
      try {
        this.ws = new WebSocket(`${this.baseUrl}/ws`)
        
        this.ws.onopen = () => {
          console.log('✅ WebSocket connected')
          this.reconnectAttempts = 0
          this.isConnecting = false
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            
            // Send to notification service for debug display
            notificationService.handleWebSocketMessage(data)
            
            // Handle as task update if it has task_id
            if (data.task_id) {
              this.handleTaskUpdate(data as TaskUpdate)
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
            notificationService.addNotification({
              type: 'error',
              message: `Failed to parse WebSocket message: ${error}`,
              timestamp: Date.now(),
              from: 'websocket_service'
            })
          }
        }
        
        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason)
          this.isConnecting = false
          this.ws = null
          
          // Don't attempt to reconnect automatically since backend doesn't support WebSocket yet
          // if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          //   this.attemptReconnect()
          // }
        }
        
        this.ws.onerror = (error) => {
          console.warn('⚠️ WebSocket connection failed (this is expected if backend doesn\'t support WebSocket yet):', error)
          this.isConnecting = false
          // Don't reject - allow the app to continue without WebSocket
          resolve()
        }
        
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    this.taskCallbacks.clear()
  }

  /**
   * Subscribe to task updates for a specific task ID
   */
  subscribeToTask(taskId: string, callback: TaskUpdateCallback): () => void {
    if (!this.taskCallbacks.has(taskId)) {
      this.taskCallbacks.set(taskId, [])
    }
    
    this.taskCallbacks.get(taskId)!.push(callback)
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.taskCallbacks.get(taskId)
      if (callbacks) {
        const index = callbacks.indexOf(callback)
        if (index > -1) {
          callbacks.splice(index, 1)
        }
        if (callbacks.length === 0) {
          this.taskCallbacks.delete(taskId)
        }
      }
    }
  }

  /**
   * Send a message to the WebSocket server
   */
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }

  /**
   * Get the current connection status
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * Handle incoming task updates
   */
  private handleTaskUpdate(update: TaskUpdate): void {
    const callbacks = this.taskCallbacks.get(update.task_id)
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(update)
        } catch (error) {
          console.error('Error in task update callback:', error)
        }
      })
    }
  }

  /**
   * Attempt to reconnect to the WebSocket server
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`🔄 Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error)
      })
    }, delay)
  }
}

// Create and export a singleton instance
export const webSocketService = new WebSocketService()

// Auto-connect when the service is imported
webSocketService.connect().catch((error) => {
  console.warn('Initial WebSocket connection failed:', error)
})

export default webSocketService
export type { TaskUpdate, TaskUpdateCallback }