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
  import { createEventDispatcher, onMount } from 'svelte'
  import { 
    web3AuthState, 
    isWeb3AuthLoading, 
    web3AuthError,
    isWeb3AuthConnected,
    web3AuthUser
  } from '../stores/web3AuthStore'
  import { 
    initializeWeb3Auth, 
    loginWithWeb3Auth, 
    type LoginProvider 
  } from '../lib/web3AuthService'
  
  // Props
  export let isOpen = false    // Controls modal visibility from parent component
  
  // Event dispatcher for communicating with parent component
  const dispatch = createEventDispatcher()
  
  // Initialize Web3Auth when component mounts
  onMount(async () => {
    if (!$web3AuthState.isInitialized) {
      await initializeWeb3Auth()
    }
  })
  
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
   * Handles Web3Auth social authentication
   * Provides multiple social login options through Web3Auth
   * @param provider - The social login provider to use
   */
  async function handleWeb3AuthConnect(provider: LoginProvider) {
    try {
      const result = await loginWithWeb3Auth(provider)
      
      if (result.success && result.user) {
        console.log(`Successfully connected with ${provider}:`, result.user)
        dispatch('connect', { 
          type: 'web3auth', 
          provider, 
          user: result.user,
          web3Provider: result.provider
        })
        handleClose()
      } else {
        console.error(`Failed to connect with ${provider}:`, result.error)
      }
    } catch (error) {
      console.error(`Error connecting with ${provider}:`, error)
    }
  }
  
  /**
   * Handles legacy Social Connect authentication
   * TODO: Remove this once Web3Auth integration is fully tested
   */
  function handleSocialConnect() {
    // Legacy implementation - can be removed once Web3Auth is fully integrated
    console.log('Connecting with legacy Social Connect...')
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
          Web3Auth Social Login Options
          - Multiple social authentication providers via Web3Auth
          - Individual buttons for each provider
          - Loading and error state handling
        -->
        
        <!-- Error Display -->
        {#if $web3AuthError}
          <div class="mb-4 p-3 bg-red-100 border-2 border-red-500 rounded-md">
            <p class="text-red-700 text-sm font-mono">{$web3AuthError}</p>
          </div>
        {/if}

        <!-- Google Login -->
        <button 
          on:click={() => handleWeb3AuthConnect('google')}
          disabled={$isWeb3AuthLoading}
          class="w-full flex items-center gap-4 p-4 bg-white border-3 border-black rounded-md mb-3 cursor-pointer transition-colors hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <!-- Google Icon Container -->
          <div class="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          </div>
          
          <div class="text-left flex-1">
            <div class="font-mono font-bold text-black text-base">
              {$isWeb3AuthLoading ? 'Connecting...' : 'Continue with Google'}
            </div>
            <div class="text-gray-600 text-sm mt-1">
              Secure authentication via Google
            </div>
          </div>
        </button>

      </div>
    </div>
  </div>
{/if}

<!-- End of conditional modal rendering -->