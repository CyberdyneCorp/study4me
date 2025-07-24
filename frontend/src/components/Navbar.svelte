<!--
  Navbar.svelte - Top navigation bar component
  
  This component provides the main navigation interface for the Study4Me application:
  - Application branding and title
  - MCP (Model Context Protocol) status toggle
  - Current page indicator
  - Wallet connection button
  
  Features:
  - Responsive layout with proper spacing
  - Neobrutalism design with thick borders
  - Interactive MCP toggle with visual feedback
  - Wallet modal integration
  - Clean typography hierarchy
-->

<script lang="ts">
  // Store imports for UI state management
  import { uiStore, uiActions } from '../stores/uiStore'
  
  // Local component state
  let mcpEnabled = true;    // MCP (Model Context Protocol) toggle state
  
  /**
   * Toggles the MCP (Model Context Protocol) enabled state
   * Updates the visual indicator and potentially affects backend connections
   * TODO: Implement actual MCP connection logic
   */
  function toggleMCP() {
    mcpEnabled = !mcpEnabled;
    // TODO: Add actual MCP connection/disconnection logic here
  }
  
  /**
   * Opens the wallet connection modal
   * Triggered when user clicks the "Connect Wallet" button
   */
  function handleConnectWallet() {
    uiActions.openWalletModal()
  }
</script>

<!-- 
  ========================================
  NAVIGATION BAR TEMPLATE
  ========================================
  
  Fixed top navigation with three main sections:
  1. Left: Brand name and MCP status
  2. Center: (Currently empty, reserved for navigation items)
  3. Right: Current page indicator and wallet connection
-->

<!-- 
  Main Navigation Container
  - White background with thick bottom border for neobrutalism design
  - Full width with consistent padding
  - Fixed at top of application layout
-->
<nav class="bg-white border-b-4 border-black p-4">
  <!-- 
    Navigation Content Container
    - Centered with max width for large screens
    - Flexbox layout for space-between alignment
  -->
  <div class="max-w-7xl mx-auto flex items-center justify-between">
    
    <!-- 
      Left Section - Branding and System Status
      - Application title and MCP status indicator
      - Vertical stack layout for better organization
    -->
    <div class="flex flex-col items-start">
      <!-- Main application title -->
      <h1 class="text-2xl font-bold text-black font-mono mb-1">
        Study4Me
      </h1>
      
      <!-- 
        MCP Status Section
        - Shows Model Context Protocol connection status
        - Interactive toggle for enabling/disabling MCP
        - Color-coded visual feedback (green=enabled, red=disabled)
      -->
      <div class="flex items-center gap-2">
        <!-- MCP label -->
        <span class="font-mono font-bold text-black text-xs">
          MCP:
        </span>
        
        <!-- 
          MCP Toggle Button
          - Dynamic styling based on enabled state
          - Green background when enabled, red when disabled
          - Small size with monospace font for technical appearance
        -->
        <button 
          on:click={toggleMCP} 
          class="{mcpEnabled ? 'bg-green-500' : 'bg-red-500'} text-white border-2 border-black rounded px-2 py-0.5 font-mono font-bold cursor-pointer text-xs"
        >
          {mcpEnabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>
    </div>
    
    <!-- 
      Right Section - Navigation and Actions
      - Current page indicator
      - Primary action buttons (wallet connection)
    -->
    <div class="flex items-center gap-4">
      <!-- Current page indicator -->
      <span class="text-black font-mono font-bold">Dashboard</span>
      
      <!-- 
        Connect Wallet Button
        - Primary action button with brand blue styling
        - Thick border for neobrutalism aesthetic
        - Opens wallet connection modal when clicked
      -->
      <button 
        on:click={handleConnectWallet}
        class="bg-brand-blue text-white border-4 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer"
      >
        Connect Wallet
      </button>
    </div>
  </div>
</nav>

<!-- End of navigation bar -->