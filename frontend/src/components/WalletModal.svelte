<!--
  WalletModal.svelte - Wallet connection modal component
  
  This modal provides options for users to connect their wallets to the application:
  - WalletConnect integration for mobile wallet connections
  - Social Connect for email/social login options
  - Clean, accessible interface following neobrutalism design
  
  Features:
  - Two connection methods with distinct visual styling
  - Keyboard shortcuts (Escape to close)
  - Backdrop click to close
  - Proper ARIA attributes for accessibility
  - Event dispatching for parent component integration
  
  TODO: Implement actual wallet connection logic
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  
  // Props
  export let isOpen = false    // Controls modal visibility from parent component
  
  // Event dispatcher for communicating with parent component
  const dispatch = createEventDispatcher()
  
  /**
   * Closes the wallet modal and resets form state
   * Dispatches 'close' event to parent component
   */
  function handleClose() {
    dispatch('close')
  }
  
  /**
   * Handles WalletConnect wallet connection
   * TODO: Implement actual WalletConnect integration
   * Currently just logs and dispatches event for testing
   */
  function handleWalletConnect() {
    // TODO: Implement WalletConnect integration
    console.log('Connecting with WalletConnect...')
    dispatch('connect', { type: 'walletconnect' })
  }
  
  /**
   * Handles Social Connect authentication (Google, Twitter, email)
   * TODO: Implement actual Social Connect integration
   * Currently just logs and dispatches event for testing
   */
  function handleSocialConnect() {
    // TODO: Implement Social Connect integration
    console.log('Connecting with Social Connect...')
    dispatch('connect', { type: 'social' })
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
</script>

<!-- 
  ========================================
  WALLET MODAL TEMPLATE
  ========================================
  
  Two-option wallet connection interface:
  1. WalletConnect: For mobile wallet connections
  2. Social Connect: For email/social authentication
-->
{#if isOpen}
  <!-- 
    Modal Backdrop
    - Full screen overlay with semi-transparent background
    - Handles outside clicks and keyboard shortcuts
    - Accessible modal with proper ARIA attributes
  -->
  <div 
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    on:click={handleBackdropClick}
    on:keydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    aria-labelledby="wallet-modal-title"
    tabindex="-1"
  >
    <!-- 
      Modal Container
      - Compact modal for wallet connection options
      - Neobrutalism styling with thick black border and rounded corners
      - Responsive width with reasonable maximum
    -->
    <div class="bg-white border-4 border-black rounded-lg w-11/12 max-w-md relative">
      
      <!-- 
        Modal Header
        - Contains wallet icon, title, and close button
        - Separated from body with bottom border
      -->
      <div class="p-6 border-b-2 border-black">
        <div class="flex items-center justify-between">
          <!-- Title section with wallet icon -->
          <div class="flex items-center gap-2">
            <!-- Wallet/document icon -->
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" class="text-black">
              <path d="M21 18v1a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v13z"/>
              <path d="M8 6h8v2H8V6zm0 4h8v2H8v-2zm0 4h5v2H8v-2z" fill="white"/>
            </svg>
            <!-- Modal title with proper ID for ARIA labeling -->
            <h2 id="wallet-modal-title" class="text-lg font-bold text-black font-mono m-0">
              CONNECT WALLET
            </h2>
          </div>
          
          <!-- Close button -->
          <button 
            on:click={handleClose}
            class="bg-brand-pink text-white border-2 border-black rounded px-2 py-1 cursor-pointer font-mono text-xs font-bold"
          >
            ×
          </button>
        </div>
      </div>
      
      <!-- 
        Modal Body - Connection Options
        Contains the two main wallet connection methods
      -->
      <div class="p-6">
        
        <!-- 
          WalletConnect Option
          - Primary option for connecting mobile wallets
          - Blue icon with WiFi-like connectivity symbol
          - Hover effects for better user experience
        -->
        <button 
          on:click={handleWalletConnect}
          class="w-full flex items-center gap-4 p-4 bg-white border-3 border-black rounded-md mb-4 cursor-pointer transition-colors hover:bg-gray-50"
        >
          <!-- WalletConnect Icon Container -->
          <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
            <!-- Connectivity/WiFi-style icon -->
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
              <path d="M5.5 7.5c4.11-4.11 10.78-4.11 14.89 0l.49.5-2.12 2.12-.35-.35c-2.73-2.73-7.17-2.73-9.9 0l-.35.35L5.5 7.5z"/>
              <path d="M12 15.5c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5-1.5.67-1.5 1.5.67 1.5 1.5 1.5z"/>
              <path d="M8.5 11.5l.35-.35c1.36-1.36 3.58-1.36 4.95 0l.35.35-1.41 1.41-.35-.35c-.59-.59-1.54-.59-2.12 0l-.35.35L8.5 11.5z"/>
            </svg>
          </div>
          
          <!-- WalletConnect Text Content -->
          <div class="text-left">
            <div class="font-mono font-bold text-black text-base">
              Wallet Connect
            </div>
            <div class="text-gray-600 text-sm mt-1">
              Connect with your mobile wallet
            </div>
          </div>
        </button>
        
        <!-- 
          Social Connect Option
          - Alternative authentication method
          - Darker blue icon with checkmark/social symbol
          - For users who prefer email/social login
        -->
        <button 
          on:click={handleSocialConnect}
          class="w-full flex items-center gap-4 p-4 bg-white border-3 border-black rounded-md cursor-pointer transition-colors hover:bg-gray-50"
        >
          <!-- Social Connect Icon Container -->
          <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <!-- Social/checkmark icon -->
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              <path d="M12 7c2.76 0 5 2.24 5 5s-2.24 5-5 5-5-2.24-5-5 2.24-5 5-5m0-2C8.13 5 5 8.13 5 12s3.13 7 7 7 7-3.13 7-7-3.13-7-7-7z"/>
            </svg>
          </div>
          
          <!-- Social Connect Text Content -->
          <div class="text-left">
            <div class="font-mono font-bold text-black text-base">
              Social Connect
            </div>
            <div class="text-gray-600 text-sm mt-1">
              Connect with Google, Twitter, or email
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- End of conditional modal rendering -->