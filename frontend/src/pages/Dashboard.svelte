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

<main style="max-width: 80rem; margin: 0 auto; padding: 2rem;">
  <div style="margin-bottom: 2rem;">
    <h1 style="font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem; color: black; font-family: 'IBM Plex Mono', monospace;">
      Dashboard
    </h1>
    <p style="font-size: 1.125rem; color: #222222; margin-bottom: 1.5rem;">
      Manage your study topics and knowledge graphs
    </p>
  </div>
  
  <!-- Topic Cards -->
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr)); gap: 1.5rem;">
    {#each $topicStore.topics as topic}
      <div style="background-color: white; border: 4px solid black; border-radius: 4px; padding: 1.5rem; position: relative;">
        <button 
          style="position: absolute; top: 1rem; right: 1rem; background-color: #FF2C2C; color: white; border: 2px solid black; border-radius: 4px; padding: 0.25rem 0.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.75rem; display: flex; align-items: center; gap: 0.25rem;"
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
          style="position: absolute; bottom: 1rem; right: 1rem; background-color: #FF2C2C; color: white; border: 2px solid black; border-radius: 4px; padding: 0.5rem; cursor: pointer; display: flex; align-items: center; justify-content: center;"
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
        <h3 style="font-size: 1.25rem; font-weight: bold; margin-bottom: 1rem; color: black; font-family: 'IBM Plex Mono', monospace; padding-right: 5rem;">
          {topic.title}
        </h3>
        <p style="color: #222222; margin-bottom: 1rem;">
          {topic.description}
        </p>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
          <span 
            style="background-color: {topic.status === 'completed' ? '#10B981' : '#F59E0B'}; color: white; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem; font-family: 'IBM Plex Mono', monospace;"
          >
            {topic.status}
          </span>
          <span style="font-size: 0.875rem; color: #222222;">{topic.createdAt}</span>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button 
            style="background-color: #0050FF; color: white; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;"
            on:click={() => handleStudyClick(topic)}
          >
            Study
          </button>
          <button 
            style="background-color: #EC4899; color: white; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;"
            on:click={() => handleAddRemoveSourcesClick(topic)}
          >
            Add/Remove Sources
          </button>
        </div>
      </div>
    {/each}
    
    {#if $topicStore.topics.length === 0}
      <div style="grid-column: 1 / -1;">
        <div style="background-color: white; border: 4px solid black; border-radius: 4px; padding: 3rem; text-align: center;">
          <h3 style="font-size: 1.25rem; font-weight: bold; margin-bottom: 1rem; color: black; font-family: 'IBM Plex Mono', monospace;">No topics yet</h3>
          <p style="color: #222222; margin-bottom: 1.5rem;">Create your first study topic to get started</p>
          <button 
            style="background-color: #0050FF; color: white; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer;"
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