<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  
  export let isOpen = false
  export let title = 'Confirm Action'
  export let message = 'Are you sure you want to proceed?'
  export let confirmText = 'OK'
  export let cancelText = 'Cancel'
  export let isDangerous = false
  
  const dispatch = createEventDispatcher()
  
  function handleConfirm() {
    dispatch('confirm')
  }
  
  function handleCancel() {
    dispatch('cancel')
  }
  
  function handleOutsideClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleCancel()
    }
  }
</script>

{#if isOpen}
  <!-- Modal Backdrop -->
  <div 
    style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; padding: 1rem; z-index: 2000;"
    on:click={handleOutsideClick}
    on:keydown={(e) => e.key === 'Escape' && handleCancel()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="confirm-modal-title"
  >
    <!-- Modal Container -->
    <div 
      style="background-color: white; border: 4px solid black; width: 100%; max-width: 28rem; display: flex; flex-direction: column;"
    >
      <!-- Modal Header -->
      <div style="padding: 1.5rem 1.5rem 1rem 1.5rem;">
        <h2 id="confirm-modal-title" style="font-size: 1.125rem; font-weight: bold; font-family: 'IBM Plex Mono', monospace; color: black; margin-bottom: 1rem;">
          {title}
        </h2>
        <p style="font-size: 0.875rem; color: #666; line-height: 1.5;">
          {message}
        </p>
      </div>
      
      <!-- Modal Footer -->
      <div style="padding: 1rem 1.5rem 1.5rem 1.5rem; display: flex; justify-content: flex-end; gap: 0.75rem;">
        <button 
          style="background-color: #f9f9f9; color: black; border: 2px solid black; border-radius: 4px; padding: 0.75rem 1.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;"
          on:click={handleCancel}
        >
          {cancelText}
        </button>
        <button 
          style="background-color: {isDangerous ? '#FF2C2C' : '#0050FF'}; color: white; border: 2px solid black; border-radius: 4px; padding: 0.75rem 1.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;"
          on:click={handleConfirm}
        >
          {confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}