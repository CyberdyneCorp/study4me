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
    class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
    on:click={handleOutsideClick}
    on:keydown={(e) => e.key === 'Escape' && handleCancel()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="confirm-modal-title"
    tabindex="-1"
  >
    <!-- Modal Container -->
    <div 
      class="bg-white border-4 border-black w-full max-w-md flex flex-col"
    >
      <!-- Modal Header -->
      <div class="px-6 py-6 pb-4">
        <h2 id="confirm-modal-title" class="text-lg font-bold font-mono text-black mb-4">
          {title}
        </h2>
        <p class="text-sm text-gray-600 leading-relaxed">
          {message}
        </p>
      </div>
      
      <!-- Modal Footer -->
      <div class="px-6 py-4 pt-4 flex justify-end gap-3">
        <button 
          class="bg-gray-100 text-black border-2 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer text-sm"
          on:click={handleCancel}
        >
          {cancelText}
        </button>
        <button 
          class="{isDangerous ? 'bg-brand-red' : 'bg-brand-blue'} text-white border-2 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer text-sm"
          on:click={handleConfirm}
        >
          {confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}