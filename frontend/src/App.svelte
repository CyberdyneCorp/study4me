<!--
  App.svelte - Main application root component
  
  This is the entry point for the Study4Me application. It orchestrates
  the main layout and global components:
  
  Architecture:
  - Fixed navigation bar at the top
  - Main dashboard content area
  - Global modals (wallet connection, etc.)
  - Brand yellow background for neobrutalism design
  
  Responsibilities:
  - Application-wide layout and styling
  - Global modal state management
  - Wallet connection event handling
  - Inter-component communication coordination
-->

<script lang="ts">
  // Component imports
  import Navbar from './components/Navbar.svelte'       // Top navigation bar
  import Dashboard from './pages/Dashboard.svelte'     // Main dashboard page
  import WalletModal from './components/WalletModal.svelte'  // Wallet connection modal
  
  // Store imports for global state management
  import { uiStore, uiActions } from './stores/uiStore'
  
  /**
   * Handles wallet modal close events
   * Called when user cancels wallet connection or closes modal
   */
  function handleWalletModalClose() {
    uiActions.closeWalletModal()
  }
  
  /**
   * Handles wallet connection events from the wallet modal
   * Processes different wallet connection types and initiates connection
   * TODO: Implement actual wallet connection logic
   * @param event - Custom event containing wallet connection details
   */
  function handleWalletConnect(event: CustomEvent) {
    const { type } = event.detail
    console.log(`Wallet connection initiated with ${type}`)
    // TODO: Implement actual wallet connection logic
    // This should handle WalletConnect, Social Connect, etc.
    uiActions.closeWalletModal()
  }
</script>

<!-- 
  ========================================
  MAIN APPLICATION LAYOUT
  ========================================
  
  Full-height container with brand styling and component hierarchy:
  1. Navigation bar (fixed at top)
  2. Main dashboard content
  3. Global modals (positioned absolutely)
-->

<!-- 
  Main Application Container
  - Full viewport height with brand yellow background
  - Uses Inter font family for clean typography
  - Neobrutalism design system base styling
-->
<div class="min-h-screen bg-brand-yellow font-inter">
  <!-- Top navigation bar -->
  <Navbar />
  
  <!-- Main dashboard content area -->
  <Dashboard />
</div>

<!-- 
  Global Modals Section
  - Modals are rendered outside the main layout container
  - Positioned absolutely over the entire application
  - Controlled by global UI store state
-->

<!-- 
  Wallet Connection Modal
  - Global modal for wallet authentication
  - Controlled by uiStore.isWalletModalOpen state
  - Handles both WalletConnect and Social Connect options
-->
<WalletModal 
  isOpen={$uiStore.isWalletModalOpen}
  on:close={handleWalletModalClose}
  on:connect={handleWalletConnect}
/>

<!-- End of main application template -->