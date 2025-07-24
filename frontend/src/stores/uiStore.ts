import { writable } from 'svelte/store'

export interface UIState {
  isModalOpen: boolean
  modalContent: string | null
  isChatModalOpen: boolean
  selectedTopicForChat: string | null
  isSourcesModalOpen: boolean
  selectedTopicForSources: string | null
  isConfirmModalOpen: boolean
  confirmModalData: ConfirmModalData | null
  notifications: Notification[]
  theme: 'light' | 'dark'
}

export interface ConfirmModalData {
  title: string
  message: string
  confirmText: string
  cancelText: string
  isDangerous?: boolean
  onConfirm: () => void
}

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
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
  }
}