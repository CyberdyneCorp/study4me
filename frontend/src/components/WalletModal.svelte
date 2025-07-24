<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  
  export let isOpen = false
  
  const dispatch = createEventDispatcher()
  
  function handleClose() {
    dispatch('close')
  }
  
  function handleWalletConnect() {
    // TODO: Implement WalletConnect integration
    console.log('Connecting with WalletConnect...')
    dispatch('connect', { type: 'walletconnect' })
  }
  
  function handleSocialConnect() {
    // TODO: Implement Social Connect integration
    console.log('Connecting with Social Connect...')
    dispatch('connect', { type: 'social' })
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
</script>

{#if isOpen}
  <!-- Modal backdrop -->
  <div 
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    on:click={handleBackdropClick}
    on:keydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    aria-labelledby="wallet-modal-title"
    tabindex="-1"
  >
    <!-- Modal content -->
    <div class="bg-white border-4 border-black rounded-lg w-11/12 max-w-md relative">
      <!-- Modal header -->
      <div class="p-6 border-b-2 border-black">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" class="text-black">
              <path d="M21 18v1a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v13z"/>
              <path d="M8 6h8v2H8V6zm0 4h8v2H8v-2zm0 4h5v2H8v-2z" fill="white"/>
            </svg>
            <h2 id="wallet-modal-title" class="text-lg font-bold text-black font-mono m-0">
              CONNECT WALLET
            </h2>
          </div>
          <button 
            on:click={handleClose}
            class="bg-brand-pink text-white border-2 border-black rounded px-2 py-1 cursor-pointer font-mono text-xs font-bold"
          >
            ×
          </button>
        </div>
      </div>
      
      <!-- Modal body -->
      <div class="p-6">
        <!-- Wallet Connect Option -->
        <button 
          on:click={handleWalletConnect}
          class="w-full flex items-center gap-4 p-4 bg-white border-3 border-black rounded-md mb-4 cursor-pointer transition-colors hover:bg-gray-50"
        >
          <!-- WalletConnect Icon -->
          <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
              <path d="M5.5 7.5c4.11-4.11 10.78-4.11 14.89 0l.49.5-2.12 2.12-.35-.35c-2.73-2.73-7.17-2.73-9.9 0l-.35.35L5.5 7.5z"/>
              <path d="M12 15.5c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5-1.5.67-1.5 1.5.67 1.5 1.5 1.5z"/>
              <path d="M8.5 11.5l.35-.35c1.36-1.36 3.58-1.36 4.95 0l.35.35-1.41 1.41-.35-.35c-.59-.59-1.54-.59-2.12 0l-.35.35L8.5 11.5z"/>
            </svg>
          </div>
          <div class="text-left">
            <div class="font-mono font-bold text-black text-base">
              Wallet Connect
            </div>
            <div class="text-gray-600 text-sm mt-1">
              Connect with your mobile wallet
            </div>
          </div>
        </button>
        
        <!-- Social Connect Option -->
        <button 
          on:click={handleSocialConnect}
          class="w-full flex items-center gap-4 p-4 bg-white border-3 border-black rounded-md cursor-pointer transition-colors hover:bg-gray-50"
        >
          <!-- Social Connect Icon -->
          <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              <path d="M12 7c2.76 0 5 2.24 5 5s-2.24 5-5 5-5-2.24-5-5 2.24-5 5-5m0-2C8.13 5 5 8.13 5 12s3.13 7 7 7 7-3.13 7-7-3.13-7-7-7z"/>
            </svg>
          </div>
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