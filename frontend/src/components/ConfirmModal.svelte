<!--
  ConfirmModal.svelte - Reusable confirmation dialog component
  
  This modal provides a standardized confirmation interface for destructive
  or important actions throughout the application:
  - User-friendly confirmation dialogs
  - Customizable title, message, and button text
  - Support for dangerous actions (red styling)
  - Keyboard shortcuts (Escape to cancel)
  - Backdrop click to cancel
  - Accessible design with proper ARIA attributes
  
  Used for actions like:
  - Deleting topics
  - Removing sources
  - Clearing data
  - Other irreversible operations
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  
  // Props for customizing the confirmation modal
  export let isOpen = false                              // Controls modal visibility
  export let title = 'Confirm Action'                    // Modal title text
  export let message = 'Are you sure you want to proceed?' // Confirmation message
  export let confirmText = 'OK'                          // Confirm button text
  export let cancelText = 'Cancel'                       // Cancel button text
  export let isDangerous = false                         // If true, uses red styling for confirm button
  
  // Event dispatcher for parent communication
  const dispatch = createEventDispatcher()
  
  /**
   * Handles confirm button click
   * Dispatches 'confirm' event to parent component
   */
  function handleConfirm() {
    dispatch('confirm')
  }
  
  /**
   * Handles cancel button click or modal dismissal
   * Dispatches 'cancel' event to parent component
   */
  function handleCancel() {
    dispatch('cancel')
  }
  
  /**
   * Handles clicks outside the modal content to cancel the action
   * Only cancels if user clicks the backdrop, not the modal content itself
   * @param event - Mouse click event to check target
   */
  function handleOutsideClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleCancel()
    }
  }
</script>

<!-- 
  ========================================
  CONFIRMATION MODAL TEMPLATE
  ========================================
  
  Simple two-section modal:
  1. Header: Title and confirmation message
  2. Footer: Cancel and confirm action buttons
-->
{#if isOpen}
  <!-- 
    Modal Backdrop
    - Full screen overlay with semi-transparent background
    - Handles outside clicks and keyboard shortcuts
    - Accessible modal with proper ARIA attributes
  -->
  <div 
    class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
    on:click={handleOutsideClick}
    on:keydown={(e) => e.key === 'Escape' && handleCancel()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="confirm-modal-title"
    tabindex="-1"
  >
    <!-- 
      Modal Container
      - Compact modal for confirmation dialogs
      - Neobrutalism styling with thick black border
      - Flexible width with reasonable maximum
    -->
    <div 
      class="bg-white border-4 border-black w-full max-w-md flex flex-col"
    >
      <!-- 
        Modal Header/Content Section
        - Contains the confirmation title and message
        - Generous padding for readability
      -->
      <div class="px-6 py-6 pb-4">
        <!-- Modal title with proper ARIA labeling -->
        <h2 id="confirm-modal-title" class="text-lg font-bold font-mono text-black mb-4">
          {title}
        </h2>
        <!-- Confirmation message with readable formatting -->
        <p class="text-sm text-gray-600 leading-relaxed">
          {message}
        </p>
      </div>
      
      <!-- 
        Modal Footer/Actions Section
        - Contains cancel and confirm buttons
        - Buttons aligned to the right for standard UX
        - Different styling based on action type (dangerous vs normal)
      -->
      <div class="px-6 py-4 pt-4 flex justify-end gap-3">
        <!-- Cancel button (always gray, safe action) -->
        <button 
          class="bg-gray-100 text-black border-2 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer text-sm"
          on:click={handleCancel}
        >
          {cancelText}
        </button>
        
        <!-- 
          Confirm button with conditional styling
          - Red background for dangerous actions (delete, remove, etc.)
          - Blue background for normal confirmations
        -->
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

<!-- End of conditional modal rendering -->