<script lang="ts">
  // Simple app without routing for now
  let mcpEnabled = true;
  
  function toggleMCP() {
    mcpEnabled = !mcpEnabled;
    const button = document.getElementById('mcpToggle');
    if (mcpEnabled) {
      button.style.backgroundColor = '#10B981';
      button.textContent = 'Enabled';
    } else {
      button.style.backgroundColor = '#EF4444';
      button.textContent = 'Disabled';
    }
  }
</script>

<div style="min-height: 100vh; background-color: #FFF200; font-family: 'Inter', sans-serif;">
  <!-- Simple Navbar -->
  <nav style="background-color: white; border-bottom: 4px solid black; padding: 1rem;">
    <div style="max-width: 80rem; margin: 0 auto; display: flex; align-items: center; justify-content: space-between;">
      <h1 style="font-size: 1.5rem; font-weight: bold; color: black; font-family: 'IBM Plex Mono', monospace;">
        Study4Me
      </h1>
      <div style="display: flex; align-items: center; gap: 1rem;">
        <a href="#" style="color: black; text-decoration: none; font-family: 'IBM Plex Mono', monospace;">Dashboard</a>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <span style="font-family: 'IBM Plex Mono', monospace; font-weight: bold; color: black; font-size: 0.875rem;">
            MCP:
          </span>
          <button id="mcpToggle" on:click={toggleMCP} style="background-color: #10B981; color: white; border: 3px solid black; border-radius: 4px; padding: 0.25rem 0.75rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.75rem;">
            Enabled
          </button>
        </div>
        <button style="background-color: #0050FF; color: white; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer;">
          Connect Wallet
        </button>
      </div>
    </div>
  </nav>

  <!-- Main Content -->
  <main style="max-width: 80rem; margin: 0 auto; padding: 2rem;">
    <div style="margin-bottom: 2rem;">
      <h1 style="font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem; color: black; font-family: 'IBM Plex Mono', monospace;">
        Dashboard
      </h1>
      <p style="font-size: 1.125rem; color: #222222; margin-bottom: 1.5rem;">
        Manage your study topics and knowledge graphs
      </p>
    </div>
    
    <!-- Topic Cards -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr)); gap: 1.5rem;">
      <!-- Card 1 -->
      <div style="background-color: white; border: 4px solid black; border-radius: 4px; padding: 1.5rem; position: relative;">
        <button style="position: absolute; top: 1rem; right: 1rem; background-color: #FF2C2C; color: white; border: 2px solid black; border-radius: 4px; padding: 0.25rem 0.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.75rem; display: flex; align-items: center; gap: 0.25rem;">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="5" cy="5" r="3"/>
            <circle cx="19" cy="5" r="3"/>
            <circle cx="12" cy="19" r="3"/>
            <line x1="5" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2"/>
            <line x1="19" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2"/>
          </svg>
          Graph
        </button>
        <h3 style="font-size: 1.25rem; font-weight: bold; margin-bottom: 1rem; color: black; font-family: 'IBM Plex Mono', monospace; padding-right: 5rem;">
          Machine Learning Fundamentals
        </h3>
        <p style="color: #222222; margin-bottom: 1rem;">
          Basic concepts of ML algorithms and applications
        </p>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
          <span style="background-color: #10B981; color: white; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem; font-family: 'IBM Plex Mono', monospace;">
            completed
          </span>
          <span style="font-size: 0.875rem; color: #222222;">2024-01-15</span>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button style="background-color: #0050FF; color: white; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;">
            View
          </button>
          <button style="background-color: white; color: black; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;">
            Edit
          </button>
        </div>
      </div>

      <!-- Card 2 -->
      <div style="background-color: white; border: 4px solid black; border-radius: 4px; padding: 1.5rem; position: relative;">
        <button style="position: absolute; top: 1rem; right: 1rem; background-color: #FF2C2C; color: white; border: 2px solid black; border-radius: 4px; padding: 0.25rem 0.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.75rem; display: flex; align-items: center; gap: 0.25rem;">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="5" cy="5" r="3"/>
            <circle cx="19" cy="5" r="3"/>
            <circle cx="12" cy="19" r="3"/>
            <line x1="5" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2"/>
            <line x1="19" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2"/>
          </svg>
          Graph
        </button>
        <h3 style="font-size: 1.25rem; font-weight: bold; margin-bottom: 1rem; color: black; font-family: 'IBM Plex Mono', monospace; padding-right: 5rem;">
          Quantum Computing Basics
        </h3>
        <p style="color: #222222; margin-bottom: 1rem;">
          Introduction to quantum mechanics and quantum algorithms
        </p>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
          <span style="background-color: #F59E0B; color: white; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem; font-family: 'IBM Plex Mono', monospace;">
            processing
          </span>
          <span style="font-size: 0.875rem; color: #222222;">2024-01-16</span>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button style="background-color: #0050FF; color: white; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;">
            View
          </button>
          <button style="background-color: white; color: black; border: 4px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;">
            Edit
          </button>
        </div>
      </div>
    </div>
  </main>
</div>