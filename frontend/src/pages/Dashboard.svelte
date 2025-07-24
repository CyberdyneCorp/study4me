<script lang="ts">
  import { onMount } from 'svelte'
  import { topicStore, topicActions } from '../stores/topicStore'
  import { uiStore, uiActions } from '../stores/uiStore'
  import type { ConfirmModalData } from '../stores/uiStore'
  import Card from '../components/Card.svelte'
  import Button from '../components/Button.svelte'
  import ChatModal from '../components/ChatModal.svelte'
  import SourcesModal from '../components/SourcesModal.svelte'
  import ConfirmModal from '../components/ConfirmModal.svelte'
  import TopicCreationModal from '../components/TopicCreationModal.svelte'
  
  onMount(() => {
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
  
  function handleStudyClick(topic: any) {
    uiActions.openChatModal(topic.id)
  }
  
  function handleCloseChatModal() {
    uiActions.closeChatModal()
  }
  
  function handleAddRemoveSourcesClick(topic: any) {
    uiActions.openSourcesModal(topic.id)
  }
  
  function handleCloseSourcesModal() {
    uiActions.closeSourcesModal()
  }
  
  function handleDeleteTopic(topicId: string, topicTitle: string) {
    const confirmData: ConfirmModalData = {
      title: 'Delete Topic',
      message: `Are you sure you want to delete "${topicTitle}"? This action cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      isDangerous: true,
      onConfirm: () => {
        topicActions.deleteTopic(topicId)
        uiActions.closeConfirmModal()
      }
    }
    uiActions.openConfirmModal(confirmData)
  }
  
  function handleConfirmModalCancel() {
    uiActions.closeConfirmModal()
  }
  
  function handleCreateTopicClick() {
    uiActions.openTopicCreationModal()
  }
  
  function handleTopicCreationModalClose() {
    uiActions.closeTopicCreationModal()
  }
  
  function handleTopicCreate(event: CustomEvent) {
    const { name, description } = event.detail
    topicActions.createTopic(name, description)
    uiActions.closeTopicCreationModal()
  }
  
  $: selectedTopic = $uiStore.selectedTopicForChat 
    ? $topicStore.topics.find(t => t.id === $uiStore.selectedTopicForChat)
    : null
    
  $: selectedTopicForSources = $uiStore.selectedTopicForSources 
    ? $topicStore.topics.find(t => t.id === $uiStore.selectedTopicForSources)
    : null
  
  function getStatusColor(status: string) {
    switch (status) {
      case 'completed': return 'bg-green-200 text-green-900'
      case 'processing': return 'bg-yellow-200 text-yellow-900'
      case 'error': return 'bg-red-200 text-red-900'
      default: return 'bg-gray-200 text-gray-900'
    }
  }
</script>

<main class="max-w-7xl mx-auto p-8">
  <div class="mb-8">
    <h1 class="text-4xl font-bold mb-4 text-black font-mono">
      Dashboard
    </h1>
    <p class="text-lg text-secondary-text mb-6">
      Manage your study topics and knowledge graphs
    </p>
  </div>
  
  <!-- Topic Cards -->
  <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
    <!-- Create New Topic Card -->
    <button 
      on:click={handleCreateTopicClick}
      class="bg-white border-4 border-dashed border-gray-400 rounded p-6 relative hover:border-brand-blue hover:bg-blue-50 transition-colors duration-200 cursor-pointer group"
    >
      <div class="flex flex-col items-center justify-center h-full min-h-48">
        <div class="w-16 h-16 bg-brand-blue rounded-full flex items-center justify-center mb-4 group-hover:bg-opacity-90 transition-colors">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
            <path d="M12 2v20M2 12h20" stroke="white" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h3 class="text-xl font-bold mb-2 text-gray-600 group-hover:text-brand-blue font-mono transition-colors">
          Create New Topic
        </h3>
        <p class="text-sm text-gray-500 text-center group-hover:text-gray-700 transition-colors">
          Add a new study topic to get started
        </p>
      </div>
    </button>
    
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