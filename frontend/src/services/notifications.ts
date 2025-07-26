/**
 * Notification Service for Debug WebSocket Messages
 * 
 * This service provides a temporary notification system to display
 * WebSocket debug messages and other real-time notifications.
 */

export interface DebugNotification {
  id: string
  type: 'debug' | 'task_update' | 'welcome' | 'echo' | 'info' | 'warning' | 'error'
  message: string
  timestamp: number
  from?: string
  task_id?: string
  status?: string
  result?: any
  error?: string
  target_client?: string
}

type NotificationCallback = (notification: DebugNotification) => void

class NotificationService {
  private callbacks: Set<NotificationCallback> = new Set()
  private notifications: DebugNotification[] = []
  private maxNotifications = 50 // Keep only last 50 notifications

  /**
   * Subscribe to notifications
   */
  subscribe(callback: NotificationCallback): () => void {
    this.callbacks.add(callback)
    
    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback)
    }
  }

  /**
   * Add a new notification
   */
  addNotification(notification: Omit<DebugNotification, 'id'>): void {
    const fullNotification: DebugNotification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9)
    }

    // Add to notifications list
    this.notifications.unshift(fullNotification)
    
    // Keep only the most recent notifications
    if (this.notifications.length > this.maxNotifications) {
      this.notifications = this.notifications.slice(0, this.maxNotifications)
    }

    // Notify all subscribers
    this.callbacks.forEach(callback => {
      try {
        callback(fullNotification)
      } catch (error) {
        console.error('Error in notification callback:', error)
      }
    })
  }

  /**
   * Get all notifications
   */
  getNotifications(): DebugNotification[] {
    return [...this.notifications]
  }

  /**
   * Clear all notifications
   */
  clearNotifications(): void {
    this.notifications = []
    // Notify subscribers of cleared state
    this.callbacks.forEach(callback => {
      try {
        callback({
          id: 'clear',
          type: 'info',
          message: 'Notifications cleared',
          timestamp: Date.now(),
          from: 'notification_service'
        })
      } catch (error) {
        console.error('Error in notification callback:', error)
      }
    })
  }

  /**
   * Handle WebSocket message and convert to notification
   */
  handleWebSocketMessage(data: any): void {
    try {
      const parsed = typeof data === 'string' ? JSON.parse(data) : data
      
      // Determine notification type based on message structure
      let type: DebugNotification['type'] = 'debug'
      if (parsed.type) {
        type = parsed.type
      } else if (parsed.task_id) {
        type = 'task_update'
      }

      this.addNotification({
        type,
        message: parsed.message || 'WebSocket message received',
        timestamp: parsed.timestamp || Date.now(),
        from: parsed.from || 'websocket',
        task_id: parsed.task_id,
        status: parsed.status,
        result: parsed.result,
        error: parsed.error,
        target_client: parsed.target_client
      })
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
      this.addNotification({
        type: 'error',
        message: `Failed to parse WebSocket message: ${error}`,
        timestamp: Date.now(),
        from: 'notification_service'
      })
    }
  }
}

// Create and export singleton instance
export const notificationService = new NotificationService()
export default notificationService