import { writable } from 'svelte/store'

export interface Topic {
  id: string
  title: string
  description: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  createdAt: string
  updatedAt: string
  sources?: Array<{id: string, title: string, type: string}>
  graphData?: any
  audioSummary?: string
}

export interface TopicState {
  topics: Topic[]
  selectedTopic: Topic | null
  isLoading: boolean
  error: string | null
}

const initialState: TopicState = {
  topics: [],
  selectedTopic: null,
  isLoading: false,
  error: null
}

export const topicStore = writable<TopicState>(initialState)

export const topicActions = {
  setLoading: (loading: boolean) => {
    topicStore.update(state => ({ ...state, isLoading: loading }))
  },
  
  setError: (error: string | null) => {
    topicStore.update(state => ({ ...state, error }))
  },
  
  setTopics: (topics: Topic[]) => {
    topicStore.update(state => ({ ...state, topics }))
  },
  
  addTopic: (topic: Topic) => {
    topicStore.update(state => ({
      ...state,
      topics: [topic, ...state.topics]
    }))
  },
  
  updateTopic: (id: string, updates: Partial<Topic>) => {
    topicStore.update(state => ({
      ...state,
      topics: state.topics.map(topic =>
        topic.id === id ? { ...topic, ...updates } : topic
      ),
      selectedTopic: state.selectedTopic?.id === id
        ? { ...state.selectedTopic, ...updates }
        : state.selectedTopic
    }))
  },
  
  selectTopic: (topic: Topic) => {
    topicStore.update(state => ({ ...state, selectedTopic: topic }))
  },
  
  clearSelectedTopic: () => {
    topicStore.update(state => ({ ...state, selectedTopic: null }))
  }
}