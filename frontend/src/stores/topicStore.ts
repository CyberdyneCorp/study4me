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

/**
 * Interface defining the structure of a study topic
 * Represents a single topic that users can study and manage
 */
export interface Topic {
  id: string                  // Unique identifier for the topic
  title: string              // Display name of the topic
  description: string        // Brief description of what the topic covers
  status: 'pending' | 'processing' | 'completed' | 'error'  // Current processing status
  createdAt: string         // ISO date string when topic was created
  updatedAt: string         // ISO date string when topic was last modified
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
   * Creates a new topic with default values and adds it to the store
   * Generates a unique ID and sets initial status to 'pending'
   * @param name - The title/name of the new topic
   * @param description - Brief description of what the topic covers
   * @returns The newly created topic object
   */
  createTopic: (name: string, description: string) => {
    // Get current date in YYYY-MM-DD format
    const now = new Date().toISOString().split('T')[0]
    
    // Create new topic object with default values
    const newTopic: Topic = {
      id: Math.random().toString(36).substr(2, 9), // Generate random ID
      title: name,
      description: description,
      status: 'pending',      // New topics start as pending
      createdAt: now,
      updatedAt: now,
      sources: []             // Start with empty sources array
    }
    
    // Add the new topic to the store (at the beginning of the array)
    topicStore.update(state => ({
      ...state,
      topics: [newTopic, ...state.topics]
    }))
    
    // Return the created topic for further use if needed
    return newTopic
  }
}