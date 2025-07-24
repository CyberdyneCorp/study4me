<script lang="ts">
  let mcpEnabled = true;
  
  function toggleMCP() {
    mcpEnabled = !mcpEnabled;
  }
</script>

<nav style="background-color: white; border-bottom: 4px solid black; padding: 1rem;">
  <div style="max-width: 80rem; margin: 0 auto; display: flex; align-items: center; justify-content: space-between;">
    <div style="display: flex; flex-direction: column; align-items: flex-start;">
      <h1 style="font-size: 1.5rem; font-weight: bold; color: black; font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.25rem;">
        Study4Me
      </h1>
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="font-family: 'IBM Plex Mono', monospace; font-weight: bold; color: black; font-size: 0.65rem;">
          MCP:
        </span>
        <button 
          on:click={toggleMCP} 
          style="background-color: {mcpEnabled ? '#10B981' : '#EF4444'}; color: white; border: 2px solid black; border-radius: 3px; padding: 0.125rem 0.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.65rem;"
        >
          {mcpEnabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>
    </div>
    <div style="display: flex; align-items: center; gap: 1rem;">
      <span style="color: black; font-family: 'IBM Plex Mono', monospace; font-weight: bold;">Dashboard</span>
      <button style="background-color: #0050FF; color: white; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer;">
        Connect Wallet
      </button>
    </div>
  </div>
</nav>