<script lang="ts">
  import Navbar from './components/Navbar.svelte'
  import Dashboard from './pages/Dashboard.svelte'
  import WalletModal from './components/WalletModal.svelte'
  import { uiStore, uiActions } from './stores/uiStore'
  
  function handleWalletModalClose() {
    uiActions.closeWalletModal()
  }
  
  function handleWalletConnect(event: CustomEvent) {
    const { type } = event.detail
    console.log(`Wallet connection initiated with ${type}`)
    // TODO: Implement actual wallet connection logic
    uiActions.closeWalletModal()
  }
</script>

<div class="min-h-screen bg-brand-yellow font-inter">
  <Navbar />
  <Dashboard />
</div>

<!-- Wallet Modal -->
<WalletModal 
  isOpen={$uiStore.isWalletModalOpen}
  on:close={handleWalletModalClose}
  on:connect={handleWalletConnect}
/>