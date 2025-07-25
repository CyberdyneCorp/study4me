<!--
  TopicCreationModal.svelte - Modal dialog for creating new study topics
  
  This modal provides a form interface for users to create new topics by entering:
  - Topic name/title (required)
  - Topic description (required)
  
  Features:
  - Form validation (both fields required)
  - Loading state during creation
  - Keyboard shortcuts (Escape to close)
  - Backdrop click to close
  - Accessible design with proper ARIA attributes
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  import { apiService, type CreateStudyTopicRequest, type CreateStudyTopicResponse } from '../services/api'
  
  // Props
  export let isOpen = false  // Controls modal visibility from parent component
  
  // Event dispatcher for communicating with parent component
  const dispatch = createEventDispatcher()
  
  // Form state variables
  let topicName = ''         // User input for topic name
  let topicDescription = ''  // User input for topic description
  let useKnowledgeGraph = true  // Knowledge graph option (default enabled)
  let isCreating = false     // Loading state during topic creation
  let errorMessage = ''      // Error message for failed creation
  
  /**
   * Closes the modal and resets form state
   * Dispatches 'close' event to parent component
   */
  function handleClose() {
    resetForm()
    dispatch('close')
  }
  
  /**
   * Resets all form fields and states to initial values
   * Called when modal closes or after successful creation
   */
  function resetForm() {
    topicName = ''
    topicDescription = ''
    useKnowledgeGraph = true
    isCreating = false
    errorMessage = ''
  }
  
  /**
   * Handles topic creation form submission
   * Validates inputs and calls the backend API to create the topic
   */
  async function handleCreate() {
    // Validate required fields
    if (!topicName.trim()) {
      errorMessage = 'Topic name is required'
      return
    }
    
    // Clear any previous error
    errorMessage = ''
    
    // Set loading state
    isCreating = true
    
    try {
      // Call the backend API to create the study topic
      const request: CreateStudyTopicRequest = {
        name: topicName.trim(),
        description: topicDescription.trim() || undefined,
        use_knowledge_graph: useKnowledgeGraph
      }
      
      const response: CreateStudyTopicResponse = await apiService.createStudyTopic(request)
      
      // Dispatch success event with the created topic data
      dispatch('create', {
        topic_id: response.topic_id,
        name: response.name,
        description: response.description,
        use_knowledge_graph: response.use_knowledge_graph
      })
      
      // Reset form and close modal
      resetForm()
      dispatch('close')
      
    } catch (error) {
      console.error('Failed to create study topic:', error)
      errorMessage = error instanceof Error ? error.message : 'Failed to create topic. Please try again.'
      isCreating = false
    }
  }
  
  /**
   * Handles backdrop click to close modal
   * Only closes if user clicks the backdrop itself, not the modal content
   * @param event - Mouse click event to check target
   */
  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose()
    }
  }
  
  /**
   * Handles keyboard shortcuts for modal interaction
   * Currently supports Escape key to close modal
   * @param event - Keyboard event to check which key was pressed
   */
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      handleClose()
    }
  }
  
  /**
   * Reactive statement that validates form completeness
   * Updates automatically when user types in the input field
   * Used to enable/disable the Create button
   */
  $: isFormValid = topicName.trim() // Only topic name is required
</script>

<!-- 
  ========================================
  TOPIC CREATION MODAL TEMPLATE
  ========================================
  
  Conditional rendering: Only displays when isOpen prop is true
  Uses Svelte's {#if} block for conditional visibility
-->
{#if isOpen}
  <!-- 
    Modal Backdrop Overlay
    - Full screen overlay with semi-transparent background 
    - Centers modal content using flexbox
    - Handles click-outside-to-close functionality
    - Supports keyboard navigation with proper ARIA attributes
  -->
  <div 
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    on:click={handleBackdropClick}
    on:keydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    aria-labelledby="topic-creation-modal-title"
    tabindex="-1"
  >
    <!-- 
      Modal Content Container
      - White background with neobrutalism styling (thick black border)
      - Responsive width: 11/12 on mobile, max 28rem on larger screens
      - Positioned relative for absolute positioning of child elements
    -->
    <div class="bg-white border-4 border-black rounded-lg w-11/12 max-w-md relative">
      
      <!-- 
        Modal Header Section
        - Contains title and close button
        - Separated from body with bottom border
        - Uses flexbox for space-between layout
      -->
      <div class="p-6 border-b-2 border-black">
        <div class="flex items-center justify-between">
          <!-- Title section with icon -->
          <div class="flex items-center gap-2">
            <!-- Star icon for visual appeal -->
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" class="text-black">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            <!-- Modal title with proper ID for ARIA labeling -->
            <h2 id="topic-creation-modal-title" class="text-lg font-bold text-black font-mono m-0">
              CREATE NEW TOPIC
            </h2>
          </div>
          
          <!-- Close button with hover effect -->
          <button 
            on:click={handleClose}
            class="bg-brand-pink text-white border-2 border-black rounded px-2 py-1 cursor-pointer font-mono text-xs font-bold hover:bg-opacity-90"
          >
            ×
          </button>
        </div>
      </div>
      
      <!-- 
        Modal Body - Form Content
        Contains all form inputs and action buttons
      -->
      <div class="p-6">
        
        <!-- Topic Name Input Field -->
        <div class="mb-4">
          <!-- Label with proper association to input via for/id -->
          <label for="topic-name" class="block font-bold font-mono mb-2 text-sm text-black">
            Topic Name
          </label>
          <!-- Text input with two-way binding and validation -->
          <input
            id="topic-name"
            type="text"
            bind:value={topicName}
            placeholder="e.g., Machine Learning Fundamentals"
            class="w-full p-3 border-2 border-black rounded font-inter text-sm"
            disabled={isCreating}
          />
        </div>
        
        <!-- Topic Description Textarea Field -->
        <div class="mb-4">
          <!-- Label with proper association to textarea -->
          <label for="topic-description" class="block font-bold font-mono mb-2 text-sm text-black">
            Description <span class="text-gray-500 font-normal">(optional)</span>
          </label>
          <!-- Textarea with resize disabled and proper binding -->
          <textarea
            id="topic-description"
            bind:value={topicDescription}
            placeholder="Brief description of what this topic covers..."
            rows="3"
            class="w-full p-3 border-2 border-black rounded font-inter text-sm resize-none"
            disabled={isCreating}
          ></textarea>
        </div>
        
        <!-- Knowledge Graph Toggle -->
        <div class="mb-6">
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              bind:checked={useKnowledgeGraph}
              disabled={isCreating}
              class="w-4 h-4 border-2 border-black rounded"
            />
            <span class="font-bold font-mono text-sm text-black">
              Use Knowledge Graph
            </span>
          </label>
          <p class="text-xs text-gray-600 mt-1 ml-7">
            Enable AI-powered knowledge graph generation for this topic
          </p>
        </div>
        
        <!-- Error Message -->
        {#if errorMessage}
          <div class="mb-4 p-3 bg-red-100 border-2 border-red-500 rounded">
            <p class="text-red-700 text-sm font-mono">{errorMessage}</p>
          </div>
        {/if}
        
        <!-- 
          Action Buttons Section
          - Cancel and Create buttons aligned to the right
          - Create button shows loading state and is disabled when form invalid
          - Uses conditional classes for styling based on state
        -->
        <div class="flex gap-3 justify-end">
          <!-- Cancel Button -->
          <button 
            on:click={handleClose}
            class="bg-gray-100 text-black border-2 border-black rounded px-6 py-2 font-mono font-bold cursor-pointer text-sm hover:bg-gray-200"
            disabled={isCreating}
          >
            Cancel
          </button>
          
          <!-- Create Button with conditional styling and text -->
          <button 
            on:click={handleCreate}
            class="bg-brand-blue text-white border-2 border-black rounded px-6 py-2 font-mono font-bold cursor-pointer text-sm {!isFormValid || isCreating ? 'opacity-50 cursor-not-allowed' : 'hover:bg-opacity-90'}"
            disabled={!isFormValid || isCreating}
          >
            <!-- Dynamic button text based on loading state -->
            {isCreating ? 'Creating...' : 'Create Topic'}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}