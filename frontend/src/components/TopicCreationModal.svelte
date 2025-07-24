<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  
  export let isOpen = false
  
  const dispatch = createEventDispatcher()
  
  let topicName = ''
  let topicDescription = ''
  let isCreating = false
  
  function handleClose() {
    resetForm()
    dispatch('close')
  }
  
  function resetForm() {
    topicName = ''
    topicDescription = ''
    isCreating = false
  }
  
  function handleCreate() {
    if (!topicName.trim() || !topicDescription.trim()) {
      return
    }
    
    isCreating = true
    
    // Simulate API call delay
    setTimeout(() => {
      dispatch('create', {
        name: topicName.trim(),
        description: topicDescription.trim()
      })
      resetForm()
    }, 500)
  }
  
  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose()
    }
  }
  
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      handleClose()
    }
  }
  
  $: isFormValid = topicName.trim() && topicDescription.trim()
</script>

{#if isOpen}
  <!-- Modal backdrop -->
  <div 
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    on:click={handleBackdropClick}
    on:keydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    aria-labelledby="topic-creation-modal-title"
    tabindex="-1"
  >
    <!-- Modal content -->
    <div class="bg-white border-4 border-black rounded-lg w-11/12 max-w-md relative">
      <!-- Modal header -->
      <div class="p-6 border-b-2 border-black">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" class="text-black">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            <h2 id="topic-creation-modal-title" class="text-lg font-bold text-black font-mono m-0">
              CREATE NEW TOPIC
            </h2>
          </div>
          <button 
            on:click={handleClose}
            class="bg-brand-pink text-white border-2 border-black rounded px-2 py-1 cursor-pointer font-mono text-xs font-bold hover:bg-opacity-90"
          >
            ×
          </button>
        </div>
      </div>
      
      <!-- Modal body -->
      <div class="p-6">
        <!-- Topic Name Input -->
        <div class="mb-4">
          <label for="topic-name" class="block font-bold font-mono mb-2 text-sm text-black">
            Topic Name
          </label>
          <input
            id="topic-name"
            type="text"
            bind:value={topicName}
            placeholder="e.g., Machine Learning Fundamentals"
            class="w-full p-3 border-2 border-black rounded font-inter text-sm"
            disabled={isCreating}
          />
        </div>
        
        <!-- Topic Description Input -->
        <div class="mb-6">
          <label for="topic-description" class="block font-bold font-mono mb-2 text-sm text-black">
            Description
          </label>
          <textarea
            id="topic-description"
            bind:value={topicDescription}
            placeholder="Brief description of what this topic covers..."
            rows="3"
            class="w-full p-3 border-2 border-black rounded font-inter text-sm resize-none"
            disabled={isCreating}
          ></textarea>
        </div>
        
        <!-- Action Buttons -->
        <div class="flex gap-3 justify-end">
          <button 
            on:click={handleClose}
            class="bg-gray-100 text-black border-2 border-black rounded px-6 py-2 font-mono font-bold cursor-pointer text-sm hover:bg-gray-200"
            disabled={isCreating}
          >
            Cancel
          </button>
          <button 
            on:click={handleCreate}
            class="bg-brand-blue text-white border-2 border-black rounded px-6 py-2 font-mono font-bold cursor-pointer text-sm {!isFormValid || isCreating ? 'opacity-50 cursor-not-allowed' : 'hover:bg-opacity-90'}"
            disabled={!isFormValid || isCreating}
          >
            {isCreating ? 'Creating...' : 'Create Topic'}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}