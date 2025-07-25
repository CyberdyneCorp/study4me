<!--
  Dashboard.svelte - Main dashboard page for Study4Me application
  
  This component serves as the primary interface where users can:
  - View all their study topics in a responsive grid layout
  - Create new topics using the "Create New Topic" card or empty state button
  - Interact with existing topics (Study, Add/Remove Sources, View Graph, Delete)
  - Access various modals for different functionalities
  
  The dashboard handles two main states:
  1. Empty State: Shows "No topics yet" message with create button
  2. Populated State: Shows grid of topic cards with "Create New Topic" card as first item
-->

<script lang="ts">
  // Svelte lifecycle import for component initialization
  import { onMount } from 'svelte'
  
  // Store imports for state management
  import { topicStore, topicActions } from '../stores/topicStore'  // Topic data management
  import { uiStore, uiActions } from '../stores/uiStore'          // UI state (modals, etc.)
  import type { ConfirmModalData } from '../stores/uiStore'       // TypeScript type for confirmation modal
  
  // Component imports - reusable UI components
  import Card from '../components/Card.svelte'                    // Generic card component
  import Button from '../components/Button.svelte'               // Reusable button component
  import ChatModal from '../components/ChatModal.svelte'         // Study session chat interface
  import SourcesModal from '../components/SourcesModal.svelte'   // File upload and source management
  import ConfirmModal from '../components/ConfirmModal.svelte'   // Confirmation dialog for destructive actions
  import TopicCreationModal from '../components/TopicCreationModal.svelte' // New topic creation form
  
  onMount(() => {
    // Sample topics for demonstration
    topicActions.setTopics([
      {
        id: '1',
        title: 'Machine Learning Fundamentals',
        description: 'Basic concepts of ML algorithms and applications',
        status: 'completed',
        createdAt: '2024-01-15',
        updatedAt: '2024-01-16',
        sources: [
          { id: '1', title: 'Introduction to ML', type: 'PDF' },
          { id: '2', title: 'Neural Networks Basics', type: 'Video' },
          { id: '3', title: 'Supervised Learning Guide', type: 'Article' }
        ]
      },
      {
        id: '2',
        title: 'Quantum Computing Basics',
        description: 'Introduction to quantum mechanics and quantum algorithms',
        status: 'processing',
        createdAt: '2024-01-16',
        updatedAt: '2024-01-16',
        sources: [
          { id: '4', title: 'Quantum Mechanics Primer', type: 'PDF' },
          { id: '5', title: 'Qubits and Quantum Gates', type: 'Video' }
        ]
      },
      {
        id: '3',
        title: 'Web Development Essentials',
        description: 'Modern web technologies including React, Node.js, and database design',
        status: 'completed',
        createdAt: '2024-01-12',
        updatedAt: '2024-01-14',
        sources: [
          { id: '6', title: 'React Fundamentals', type: 'PDF' },
          { id: '7', title: 'Node.js Backend Tutorial', type: 'Video' },
          { id: '8', title: 'Database Design Patterns', type: 'Article' },
          { id: '9', title: 'CSS Grid and Flexbox', type: 'PDF' }
        ]
      },
      {
        id: '4',
        title: 'Data Structures & Algorithms',
        description: 'Core computer science concepts for technical interviews and problem solving',
        status: 'processing',
        createdAt: '2024-01-18',
        updatedAt: '2024-01-18',
        sources: [
          { id: '10', title: 'Big O Notation Guide', type: 'PDF' },
          { id: '11', title: 'Binary Trees Explained', type: 'Video' },
          { id: '12', title: 'Dynamic Programming Patterns', type: 'Article' }
        ]
      }
    ])
  })
  
  // ========================================
  // EVENT HANDLERS
  // ========================================
  
  /**
   * Opens the chat modal for studying a specific topic
   * This launches the interactive AI chat interface where users can ask questions about their topic
   * @param topic - The topic object containing id, title, description, etc.
   */
  function handleStudyClick(topic: any) {
    uiActions.openChatModal(topic.id)
  }
  
  /**
   * Closes the chat modal when user exits the study session
   */
  function handleCloseChatModal() {
    uiActions.closeChatModal()
  }
  
  /**
   * Opens the sources modal for managing topic sources (files, URLs, videos)
   * @param topic - The topic object to manage sources for
   */
  function handleAddRemoveSourcesClick(topic: any) {
    uiActions.openSourcesModal(topic.id)
  }
  
  /**
   * Closes the sources management modal
   */
  function handleCloseSourcesModal() {
    uiActions.closeSourcesModal()
  }
  
  /**
   * Handles topic deletion with confirmation dialog
   * Creates a confirmation modal to prevent accidental deletions
   * @param topicId - Unique identifier of the topic to delete
   * @param topicTitle - Display name of the topic (shown in confirmation message)
   */
  function handleDeleteTopic(topicId: string, topicTitle: string) {
    // Configure the confirmation modal with destructive action styling
    const confirmData: ConfirmModalData = {
      title: 'Delete Topic',
      message: `Are you sure you want to delete "${topicTitle}"? This action cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      isDangerous: true, // Applies red styling to confirm button
      onConfirm: () => {
        // Actually delete the topic and close the modal
        topicActions.deleteTopic(topicId)
        uiActions.closeConfirmModal()
      }
    }
    uiActions.openConfirmModal(confirmData)
  }
  
  /**
   * Cancels the confirmation modal without taking action
   */
  function handleConfirmModalCancel() {
    uiActions.closeConfirmModal()
  }
  
  /**
   * Opens the topic creation modal
   * Used by both the "Create New Topic" card and empty state button
   */
  function handleCreateTopicClick() {
    uiActions.openTopicCreationModal()
  }
  
  /**
   * Closes the topic creation modal without creating a topic
   */
  function handleTopicCreationModalClose() {
    uiActions.closeTopicCreationModal()
  }
  
  /**
   * Creates a new topic from the modal form data
   * @param event - Custom event containing form data (topic_id, name, description, use_knowledge_graph)
   */
  async function handleTopicCreate(event: CustomEvent) {
    const { topic_id, name, description, use_knowledge_graph } = event.detail
    
    try {
      // The modal has already created the topic via API, so we just need to add it to the store
      const newTopic = {
        id: topic_id,
        title: name,
        description: description,
        status: 'completed' as const,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        use_knowledge_graph: use_knowledge_graph,
        sources: []
      }
      
      // Add the topic to the store
      topicActions.addTopic(newTopic)
      
    } catch (error) {
      console.error('Failed to handle topic creation:', error)
      // Error is already handled in the modal
    }
  }
  
  // ========================================
  // REACTIVE STATEMENTS
  // ========================================
  
  /**
   * Reactive statement that finds the currently selected topic for chat modal
   * Updates automatically when either the selectedTopicForChat ID or topics array changes
   */
  $: selectedTopic = $uiStore.selectedTopicForChat 
    ? $topicStore.topics.find(t => t.id === $uiStore.selectedTopicForChat)
    : null
    
  /**
   * Reactive statement that finds the currently selected topic for sources modal
   * Updates automatically when either the selectedTopicForSources ID or topics array changes
   */
  $: selectedTopicForSources = $uiStore.selectedTopicForSources 
    ? $topicStore.topics.find(t => t.id === $uiStore.selectedTopicForSources)
    : null
  
  // ========================================
  // UTILITY FUNCTIONS
  // ========================================
  
  /**
   * Returns appropriate Tailwind CSS classes for topic status badges
   * @param status - The current status of the topic ('completed', 'processing', 'error', etc.)
   * @returns CSS classes for background and text color
   */
  function getStatusColor(status: string) {
    switch (status) {
      case 'completed': return 'bg-green-200 text-green-900'
      case 'processing': return 'bg-yellow-200 text-yellow-900'
      case 'error': return 'bg-red-200 text-red-900'
      default: return 'bg-gray-200 text-gray-900'
    }
  }
</script>

<!-- 
  ========================================
  MAIN DASHBOARD TEMPLATE
  ========================================
  
  This template renders the main dashboard interface using Tailwind CSS classes.
  The layout is responsive and uses CSS Grid for topic cards.
-->

<main class="max-w-7xl mx-auto p-8">
  <!-- Dashboard Header Section -->
  <div class="mb-8">
    <h1 class="text-4xl font-bold mb-4 text-black font-mono">
      Dashboard
    </h1>
    <p class="text-lg text-secondary-text mb-6">
      Manage your study topics and knowledge graphs
    </p>
  </div>
  
  <!-- 
    Topic Cards Grid Container
    - Responsive grid: 1 column on mobile, 2 on tablet (md), 3 on desktop (xl)
    - Uses CSS Grid with gap for consistent spacing
  -->
  <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
    
    <!-- 
      Create New Topic Card (Conditional)
      Only displays when topics exist to avoid duplication with empty state
      Uses Svelte's reactive if block to show/hide based on topics array length
    -->
    {#if $topicStore.topics.length > 0}
      <button 
        on:click={handleCreateTopicClick}
        class="bg-white border-4 border-dashed border-gray-400 rounded p-6 relative hover:border-brand-blue hover:bg-blue-50 transition-colors duration-200 cursor-pointer group"
      >
        <!-- Centered content with flexbox layout -->
        <div class="flex flex-col items-center justify-center h-full min-h-48">
          <!-- Plus icon with hover effect -->
          <div class="w-16 h-16 bg-brand-blue rounded-full flex items-center justify-center mb-4 group-hover:bg-opacity-90 transition-colors">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
              <path d="M12 2v20M2 12h20" stroke="white" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <!-- Card title with hover color change -->
          <h3 class="text-xl font-bold mb-2 text-gray-600 group-hover:text-brand-blue font-mono transition-colors">
            Create New Topic
          </h3>
          <!-- Description text -->
          <p class="text-sm text-gray-500 text-center group-hover:text-gray-700 transition-colors">
            Add a new study topic to get started
          </p>
        </div>
      </button>
    {/if}
    
    {#each $topicStore.topics as topic}
      <div class="bg-white border-4 border-black rounded p-6 relative flex flex-col min-h-80">
        <button 
          class="absolute top-4 right-4 bg-brand-red text-white border-2 border-black rounded px-2 py-1 font-mono font-bold cursor-pointer text-xs flex items-center gap-1"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="5" cy="5" r="3"/>
            <circle cx="19" cy="5" r="3"/>
            <circle cx="12" cy="19" r="3"/>
            <line x1="5" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2"/>
            <line x1="19" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2"/>
          </svg>
          Graph
        </button>
        
        <!-- Delete button in bottom-right corner -->
        <button 
          class="absolute bottom-4 right-4 bg-brand-red text-white border-2 border-black rounded p-2 cursor-pointer flex items-center justify-center"
          on:click={() => handleDeleteTopic(topic.id, topic.title)}
          aria-label="Delete topic"
          title="Delete topic"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 6h18l-1.5 14H4.5L3 6zm5-4h8v2H8V2zm2 6v8h2V8h-2zm4 0v8h2V8h-2z"/>
            <rect x="10" y="2" width="4" height="2"/>
            <rect x="9" y="11" width="2" height="6"/>
            <rect x="13" y="11" width="2" height="6"/>
          </svg>
        </button>
        
        <!-- Card Content -->
        <div class="flex-1 flex flex-col">
          <h3 class="text-xl font-bold mb-4 text-black font-mono pr-20">
            {topic.title}
          </h3>
          <p class="text-secondary-text mb-4 flex-1">
            {topic.description}
          </p>
          
          <!-- Status and Date Row -->
          <div class="flex items-center justify-between mb-4">
            <span 
              class="{topic.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'} text-white px-3 py-1 rounded text-sm font-mono"
            >
              {topic.status}
            </span>
            <span class="text-sm text-secondary-text">{topic.createdAt}</span>
          </div>
          
          <!-- Action Buttons - Always at bottom -->
          <div class="flex gap-2 mt-auto">
            <button 
              class="bg-brand-blue text-white border-4 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer text-sm"
              on:click={() => handleStudyClick(topic)}
            >
              Study
            </button>
            <button 
              class="bg-brand-pink text-white border-4 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer text-sm"
              on:click={() => handleAddRemoveSourcesClick(topic)}
            >
              Add/Remove Sources
            </button>
          </div>
        </div>
      </div>
    {/each}
    
    {#if $topicStore.topics.length === 0}
      <div class="col-span-full">
        <div class="bg-white border-4 border-black rounded p-12 text-center">
          <h3 class="text-xl font-bold mb-4 text-black font-mono">No topics yet</h3>
          <p class="text-secondary-text mb-6">Create your first study topic to get started</p>
          <button 
            on:click={handleCreateTopicClick}
            class="bg-brand-blue text-white border-4 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer hover:bg-opacity-90"
          >
            Create Topic
          </button>
        </div>
      </div>
    {/if}
  </div>
</main>

<!-- Chat Modal -->
<ChatModal 
  isOpen={$uiStore.isChatModalOpen}
  topicTitle={selectedTopic?.title || ''}
  sources={selectedTopic?.sources || []}
  on:close={handleCloseChatModal}
/>

<!-- Sources Modal -->
<SourcesModal 
  isOpen={$uiStore.isSourcesModalOpen}
  topicTitle={selectedTopicForSources?.title || ''}
  on:close={handleCloseSourcesModal}
/>

<!-- Confirm Modal -->
<ConfirmModal 
  isOpen={$uiStore.isConfirmModalOpen}
  title={$uiStore.confirmModalData?.title || ''}
  message={$uiStore.confirmModalData?.message || ''}
  confirmText={$uiStore.confirmModalData?.confirmText || 'OK'}
  cancelText={$uiStore.confirmModalData?.cancelText || 'Cancel'}
  isDangerous={$uiStore.confirmModalData?.isDangerous || false}
  on:confirm={() => $uiStore.confirmModalData?.onConfirm()}
  on:cancel={handleConfirmModalCancel}
/>

<!-- Topic Creation Modal -->
<TopicCreationModal 
  isOpen={$uiStore.isTopicCreationModalOpen}
  on:close={handleTopicCreationModalClose}
  on:create={handleTopicCreate}
/>