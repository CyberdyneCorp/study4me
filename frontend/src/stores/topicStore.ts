/**
 * topicStore.ts - Svelte store for managing study topics
 * 
 * This store handles all topic-related state and operations including:
 * - CRUD operations (Create, Read, Update, Delete) for topics
 * - Topic selection and filtering
 * - Loading states and error handling
 * - Source management for each topic
 * 
 * Uses Svelte's writable store for reactive state management
 * across the entire application.
 */

import { writable } from 'svelte/store'
import { apiService, type StudyTopic, type CreateStudyTopicRequest } from '../services/api'

/**
 * Interface defining the structure of a study topic
 * Represents a single topic that users can study and manage
 */
export interface Topic {
  id: string                  // Unique identifier for the topic (maps to topic_id from backend)
  title: string              // Display name of the topic (maps to name from backend)
  description: string | null // Brief description of what the topic covers
  status: 'pending' | 'processing' | 'completed' | 'error'  // Current processing status (frontend only)
  createdAt: string         // ISO date string when topic was created
  updatedAt: string         // ISO date string when topic was last modified
  use_knowledge_graph?: boolean // Whether knowledge graph is enabled for this topic
  sources?: Array<{         // Optional array of learning sources
    id: string,             // Unique identifier for the source
    title: string,          // Display name of the source
    type: string            // Type of source (PDF, Video, Article, etc.)
  }>
  graphData?: any           // Optional knowledge graph data (structure TBD)
  audioSummary?: string     // Optional audio summary URL or data
}

/**
 * Interface defining the overall state shape for the topic store
 * Contains all topic-related state and UI flags
 */
export interface TopicState {
  topics: Topic[]           // Array of all user's topics
  selectedTopic: Topic | null  // Currently selected topic for detailed view
  isLoading: boolean        // Flag indicating if any async operation is in progress
  error: string | null      // Error message if any operation fails
}

/**
 * Initial state when the application starts
 * All arrays are empty and flags are set to default values
 */
const initialState: TopicState = {
  topics: [],
  selectedTopic: null,
  isLoading: false,
  error: null
}

/**
 * Main Svelte store for topic state
 * Components subscribe to this store to get reactive updates
 * when topic data changes
 */
export const topicStore = writable<TopicState>(initialState)

/**
 * Helper function to convert backend StudyTopic to frontend Topic format
 * @param studyTopic - Backend StudyTopic object
 * @returns Frontend Topic object
 */
function convertStudyTopicToTopic(studyTopic: StudyTopic): Topic {
  return {
    id: studyTopic.topic_id,
    title: studyTopic.name,
    description: studyTopic.description,
    status: 'completed', // Default status for topics from backend
    createdAt: studyTopic.created_at,
    updatedAt: studyTopic.updated_at,
    use_knowledge_graph: studyTopic.use_knowledge_graph,
    sources: [] // Initialize empty sources array
  }
}

/**
 * Topic Actions - Collection of functions to modify topic state
 * 
 * These functions provide a clean API for components to interact with
 * the topic store without directly calling store.update() everywhere.
 * Each function handles a specific aspect of topic management.
 */
export const topicActions = {
  
  /**
   * Sets the loading state for async operations
   * @param loading - True when an operation is in progress, false when complete
   */
  setLoading: (loading: boolean) => {
    topicStore.update(state => ({ ...state, isLoading: loading }))
  },
  
  /**
   * Sets an error message in the store
   * @param error - Error message string or null to clear the error
   */
  setError: (error: string | null) => {
    topicStore.update(state => ({ ...state, error }))
  },
  
  /**
   * Replaces the entire topics array with a new set of topics
   * Useful for initial data loading or complete refresh
   * @param topics - Array of topics to set as the complete list
   */
  setTopics: (topics: Topic[]) => {
    topicStore.update(state => ({ ...state, topics }))
  },
  
  /**
   * Adds a new topic to the beginning of the topics array
   * New topics appear first in the list
   * @param topic - Complete topic object to add
   */
  addTopic: (topic: Topic) => {
    topicStore.update(state => ({
      ...state,
      topics: [topic, ...state.topics]  // Prepend to array for newest-first order
    }))
  },
  
  /**
   * Updates an existing topic with partial data
   * Also updates selectedTopic if it matches the updated topic
   * @param id - Unique identifier of the topic to update
   * @param updates - Partial topic object with fields to update
   */
  updateTopic: (id: string, updates: Partial<Topic>) => {
    topicStore.update(state => ({
      ...state,
      // Update the topic in the main array
      topics: state.topics.map(topic =>
        topic.id === id ? { ...topic, ...updates } : topic
      ),
      // Also update selectedTopic if it's the same topic
      selectedTopic: state.selectedTopic?.id === id
        ? { ...state.selectedTopic, ...updates }
        : state.selectedTopic
    }))
  },
  
  /**
   * Sets a topic as the currently selected topic
   * Used for detailed views or editing
   * @param topic - Topic object to select
   */
  selectTopic: (topic: Topic) => {
    topicStore.update(state => ({ ...state, selectedTopic: topic }))
  },
  
  /**
   * Clears the currently selected topic
   * Returns to unselected state
   */
  clearSelectedTopic: () => {
    topicStore.update(state => ({ ...state, selectedTopic: null }))
  },
  
  /**
   * Removes a topic from the store permanently
   * Also clears selectedTopic if the deleted topic was selected
   * @param id - Unique identifier of the topic to delete
   */
  deleteTopic: (id: string) => {
    topicStore.update(state => ({
      ...state,
      // Remove topic from the main array
      topics: state.topics.filter(topic => topic.id !== id),
      // Clear selectedTopic if it was the deleted topic
      selectedTopic: state.selectedTopic?.id === id ? null : state.selectedTopic
    }))
  },
  
  /**
   * Creates a new topic via backend API and adds it to the store
   * @param name - The title/name of the new topic
   * @param description - Brief description of what the topic covers
   * @param useKnowledgeGraph - Whether to enable knowledge graph for this topic
   * @returns Promise that resolves to the newly created topic object
   */
  createTopic: async (name: string, description: string, useKnowledgeGraph = true) => {
    try {
      // Set loading state
      topicActions.setLoading(true)
      topicActions.setError(null)
      
      // Create topic via backend API
      const request: CreateStudyTopicRequest = {
        name,
        description: description || undefined,
        use_knowledge_graph: useKnowledgeGraph
      }
      
      const response = await apiService.createStudyTopic(request)
      
      // Create frontend topic object from backend response
      const newTopic: Topic = {
        id: response.topic_id,
        title: response.name,
        description: response.description,
        status: 'completed', // Topics created successfully are marked as completed
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        use_knowledge_graph: response.use_knowledge_graph,
        sources: []
      }
      
      // Add the new topic to the store (at the beginning of the array)
      topicStore.update(state => ({
        ...state,
        topics: [newTopic, ...state.topics],
        isLoading: false
      }))
      
      return newTopic
      
    } catch (error) {
      console.error('Failed to create topic:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create topic'
      topicActions.setError(errorMessage)
      topicActions.setLoading(false)
      throw error
    }
  },

  /**
   * Loads topics from the backend API
   * @param limit - Maximum number of topics to fetch
   * @param offset - Number of topics to skip
   */
  loadTopics: async (limit = 100, offset = 0) => {
    try {
      topicActions.setLoading(true)
      topicActions.setError(null)
      
      const response = await apiService.getStudyTopics(limit, offset)
      const topics = response.topics.map(convertStudyTopicToTopic)
      
      topicStore.update(state => ({
        ...state,
        topics,
        isLoading: false
      }))
      
      return topics
      
    } catch (error) {
      console.error('Failed to load topics:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to load topics'
      topicActions.setError(errorMessage)
      topicActions.setLoading(false)
      throw error
    }
  }
}