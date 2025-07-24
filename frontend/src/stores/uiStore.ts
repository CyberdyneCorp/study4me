/**
 * uiStore.ts - Svelte store for managing UI state and modal interactions
 * 
 * This store handles all user interface state that needs to be shared
 * across components, including:
 * - Modal visibility states (chat, sources, confirmation, wallet, etc.)
 * - Selected topics for different contexts
 * - Notifications and user feedback
 * - Theme preferences
 * 
 * Separating UI state from business logic (topics) keeps the application
 * architecture clean and maintainable.
 */

import { writable } from 'svelte/store'

/**
 * Interface defining the complete UI state structure
 * Contains flags for all modals and UI-related data
 */
export interface UIState {
  // Generic modal system (legacy - may be removed)
  isModalOpen: boolean
  modalContent: string | null
  
  // Chat modal for studying topics
  isChatModalOpen: boolean
  selectedTopicForChat: string | null        // Topic ID currently being studied
  
  // Sources management modal
  isSourcesModalOpen: boolean
  selectedTopicForSources: string | null     // Topic ID for source management
  
  // Confirmation modal for destructive actions
  isConfirmModalOpen: boolean
  confirmModalData: ConfirmModalData | null  // Configuration for the confirmation dialog
  
  // Wallet connection modal
  isWalletModalOpen: boolean
  
  // Topic creation modal
  isTopicCreationModalOpen: boolean
  
  // User notifications system
  notifications: Notification[]              // Array of active notifications
  
  // Theme preference
  theme: 'light' | 'dark'                   // Current theme setting
}

/**
 * Configuration object for confirmation modals
 * Allows customization of title, message, buttons, and styling
 */
export interface ConfirmModalData {
  title: string           // Modal title (e.g., "Delete Topic")
  message: string         // Confirmation message to display
  confirmText: string     // Text for confirm button (e.g., "Delete", "OK")
  cancelText: string      // Text for cancel button (e.g., "Cancel")
  isDangerous?: boolean   // If true, applies red styling to confirm button
  onConfirm: () => void   // Function to call when user confirms
}

/**
 * Structure for user notifications/alerts
 * Used for showing success messages, errors, warnings, etc.
 */
export interface Notification {
  id: string                                      // Unique identifier for the notification
  type: 'success' | 'error' | 'warning' | 'info' // Determines icon and color scheme
  message: string                                 // Text content to display
  timestamp: number
}

const initialState: UIState = {
  isModalOpen: false,
  modalContent: null,
  isChatModalOpen: false,
  selectedTopicForChat: null,
  isSourcesModalOpen: false,
  selectedTopicForSources: null,
  isConfirmModalOpen: false,
  confirmModalData: null,
  isWalletModalOpen: false,
  isTopicCreationModalOpen: false,
  notifications: [],
  theme: 'light'
}

export const uiStore = writable<UIState>(initialState)

export const uiActions = {
  openModal: (content: string) => {
    uiStore.update(state => ({
      ...state,
      isModalOpen: true,
      modalContent: content
    }))
  },
  
  closeModal: () => {
    uiStore.update(state => ({
      ...state,
      isModalOpen: false,
      modalContent: null
    }))
  },
  
  openChatModal: (topicId: string) => {
    uiStore.update(state => ({
      ...state,
      isChatModalOpen: true,
      selectedTopicForChat: topicId
    }))
  },
  
  closeChatModal: () => {
    uiStore.update(state => ({
      ...state,
      isChatModalOpen: false,
      selectedTopicForChat: null
    }))
  },
  
  openSourcesModal: (topicId: string) => {
    uiStore.update(state => ({
      ...state,
      isSourcesModalOpen: true,
      selectedTopicForSources: topicId
    }))
  },
  
  closeSourcesModal: () => {
    uiStore.update(state => ({
      ...state,
      isSourcesModalOpen: false,
      selectedTopicForSources: null
    }))
  },
  
  openConfirmModal: (data: ConfirmModalData) => {
    uiStore.update(state => ({
      ...state,
      isConfirmModalOpen: true,
      confirmModalData: data
    }))
  },
  
  closeConfirmModal: () => {
    uiStore.update(state => ({
      ...state,
      isConfirmModalOpen: false,
      confirmModalData: null
    }))
  },
  
  openWalletModal: () => {
    uiStore.update(state => ({
      ...state,
      isWalletModalOpen: true
    }))
  },
  
  closeWalletModal: () => {
    uiStore.update(state => ({
      ...state,
      isWalletModalOpen: false
    }))
  },
  
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: Date.now()
    }
    
    uiStore.update(state => ({
      ...state,
      notifications: [...state.notifications, newNotification]
    }))
    
    setTimeout(() => {
      uiActions.removeNotification(newNotification.id)
    }, 5000)
  },
  
  removeNotification: (id: string) => {
    uiStore.update(state => ({
      ...state,
      notifications: state.notifications.filter(n => n.id !== id)
    }))
  },
  
  setTheme: (theme: 'light' | 'dark') => {
    uiStore.update(state => ({ ...state, theme }))
  },
  
  openTopicCreationModal: () => {
    uiStore.update(state => ({
      ...state,
      isTopicCreationModalOpen: true
    }))
  },
  
  closeTopicCreationModal: () => {
    uiStore.update(state => ({
      ...state,
      isTopicCreationModalOpen: false
    }))
  }
}