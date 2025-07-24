<script lang="ts">
  import { uiStore, uiActions } from '../stores/uiStore'
  
  let mcpEnabled = true;
  
  function toggleMCP() {
    mcpEnabled = !mcpEnabled;
  }
  
  function handleConnectWallet() {
    uiActions.openWalletModal()
  }
</script>

<nav class="bg-white border-b-4 border-black p-4">
  <div class="max-w-7xl mx-auto flex items-center justify-between">
    <div class="flex flex-col items-start">
      <h1 class="text-2xl font-bold text-black font-mono mb-1">
        Study4Me
      </h1>
      <div class="flex items-center gap-2">
        <span class="font-mono font-bold text-black text-xs">
          MCP:
        </span>
        <button 
          on:click={toggleMCP} 
          class="{mcpEnabled ? 'bg-green-500' : 'bg-red-500'} text-white border-2 border-black rounded px-2 py-0.5 font-mono font-bold cursor-pointer text-xs"
        >
          {mcpEnabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>
    </div>
    <div class="flex items-center gap-4">
      <span class="text-black font-mono font-bold">Dashboard</span>
      <button 
        on:click={handleConnectWallet}
        class="bg-brand-blue text-white border-4 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer"
      >
        Connect Wallet
      </button>
    </div>
  </div>
</nav>