<!--
  NotificationDisplay.svelte - Debug WebSocket Notification Display
  
  This component provides a temporary debug interface to show WebSocket
  notifications and real-time messages from the backend.
  
  Features:
  - Real-time notification display
  - Collapsible interface
  - Notification type indicators
  - Clear notifications functionality
  - WebSocket connection status
-->

<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import { notificationService } from '../services/notifications'
  import { webSocketService } from '../services/websocket'
  import type { DebugNotification } from '../services/notifications'
  
  // Component state
  let notifications: DebugNotification[] = []
  let isExpanded = false
  let unsubscribe: (() => void) | null = null
  
  // WebSocket connection status
  $: isConnected = webSocketService.isConnected
  
  onMount(() => {
    // Get existing notifications
    notifications = notificationService.getNotifications()
    
    // Subscribe to new notifications
    unsubscribe = notificationService.subscribe((notification) => {
      notifications = notificationService.getNotifications()
      
      // Auto-expand when new notifications arrive
      if (notification.type !== 'info' || notification.message !== 'Notifications cleared') {
        isExpanded = true
      }
    })
  })
  
  onDestroy(() => {
    if (unsubscribe) {
      unsubscribe()
    }
  })
  
  function clearNotifications() {
    notificationService.clearNotifications()
  }
  
  function toggleExpanded() {
    isExpanded = !isExpanded
  }
  
  function formatTimestamp(timestamp: number): string {
    return new Date(timestamp).toLocaleTimeString()
  }
  
  function getNotificationColor(type: string): string {
    switch (type) {
      case 'error': return 'bg-red-100 border-red-500 text-red-800'
      case 'warning': return 'bg-yellow-100 border-yellow-500 text-yellow-800'
      case 'task_update': return 'bg-blue-100 border-blue-500 text-blue-800'
      case 'welcome': return 'bg-green-100 border-green-500 text-green-800'
      case 'debug': return 'bg-purple-100 border-purple-500 text-purple-800'
      default: return 'bg-gray-100 border-gray-500 text-gray-800'
    }
  }
  
  function getStatusIcon(type: string): string {
    switch (type) {
      case 'error': return '❌'
      case 'warning': return '⚠️'
      case 'task_update': return '📋'
      case 'welcome': return '👋'
      case 'echo': return '🔄'
      case 'debug': return '🐛'
      default: return '📢'
    }
  }
</script>

<!-- Debug Notification Display -->
<div class="fixed bottom-4 right-4 z-50 max-w-md">
  
  <!-- Header Bar -->
  <div 
    class="bg-black text-white p-3 border-2 border-black cursor-pointer flex justify-between items-center"
    on:click={toggleExpanded}
    on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && toggleExpanded()}
    role="button"
    tabindex="0"
    aria-label="Toggle WebSocket notifications"
  >
    <div class="flex items-center gap-2">
      <span class="font-mono font-bold text-sm">WS Debug</span>
      <div class="flex items-center gap-1">
        <div class="w-2 h-2 rounded-full {isConnected ? 'bg-green-400' : 'bg-red-400'}"></div>
        <span class="text-xs">{isConnected ? 'Connected' : 'Disconnected'}</span>
      </div>
      {#if notifications.length > 0}
        <span class="bg-brand-pink text-white px-2 py-1 rounded text-xs font-bold">
          {notifications.length}
        </span>
      {/if}
    </div>
    
    <div class="flex items-center gap-2">
      {#if notifications.length > 0 && isExpanded}
        <button 
          class="bg-brand-red text-white px-2 py-1 rounded text-xs font-bold hover:bg-opacity-90"
          on:click|stopPropagation={clearNotifications}
          title="Clear notifications"
        >
          Clear
        </button>
      {/if}
      <span class="text-lg">
        {isExpanded ? '▼' : '▲'}
      </span>
    </div>
  </div>
  
  <!-- Notifications Panel -->
  {#if isExpanded}
    <div class="bg-white border-2 border-black border-t-0 max-h-96 overflow-y-auto">
      {#if notifications.length === 0}
        <div class="p-4 text-center text-gray-600 text-sm">
          No notifications yet
        </div>
      {:else}
        <div class="flex flex-col">
          {#each notifications as notification}
            <div class="p-3 border-b border-gray-200 {getNotificationColor(notification.type)} text-xs">
              <!-- Notification header -->
              <div class="flex justify-between items-start mb-1">
                <div class="flex items-center gap-1">
                  <span>{getStatusIcon(notification.type)}</span>
                  <span class="font-bold uppercase">{notification.type}</span>
                  {#if notification.from}
                    <span class="text-gray-600">({notification.from})</span>
                  {/if}
                </div>
                <span class="text-gray-600">{formatTimestamp(notification.timestamp)}</span>
              </div>
              
              <!-- Message -->
              <div class="font-mono mb-1">{notification.message}</div>
              
              <!-- Task details if available -->
              {#if notification.task_id}
                <div class="text-gray-700">
                  <div>Task: {notification.task_id.slice(0, 8)}...</div>
                  {#if notification.status}
                    <div>Status: {notification.status}</div>
                  {/if}
                </div>
              {/if}
              
              <!-- Error details if available -->
              {#if notification.error}
                <div class="text-red-700 mt-1 font-mono text-xs">
                  Error: {notification.error}
                </div>
              {/if}
              
              <!-- Result preview if available -->
              {#if notification.result}
                <div class="text-gray-700 mt-1">
                  <details>
                    <summary class="cursor-pointer">View Result</summary>
                    <pre class="mt-1 p-2 bg-gray-50 rounded text-xs overflow-auto">{JSON.stringify(notification.result, null, 2)}</pre>
                  </details>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  /* Custom scrollbar for notifications */
  .overflow-y-auto::-webkit-scrollbar {
    width: 4px;
  }
  
  .overflow-y-auto::-webkit-scrollbar-track {
    background: #f1f1f1;
  }
  
  .overflow-y-auto::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 2px;
  }
  
  .overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: #555;
  }
</style>