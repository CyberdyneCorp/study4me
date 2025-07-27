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
  import { onMount } from 'svelte'
  
  // Store imports for UI state management
  import { uiStore, uiActions } from '../stores/uiStore'
  
  // MCP service import
  import { mcpService } from '../services/mcp'
  import type { McpStatusResponse } from '../services/api'
  
  // Local component state
  let mcpStatus: McpStatusResponse | null = null
  let mcpEnabled = false
  let mcpStatusMessage = 'Checking...'
  let isChecking = false
  
  /**
   * Check MCP status from backend
   */
  async function checkMcpStatus() {
    if (isChecking) return
    
    isChecking = true
    try {
      mcpStatus = await mcpService.getStatus()
      mcpEnabled = mcpStatus.status === 'running'
      mcpStatusMessage = await mcpService.getStatusMessage()
    } catch (error) {
      console.error('Failed to check MCP status:', error)
      mcpEnabled = false
      mcpStatusMessage = 'Failed to check status'
    } finally {
      isChecking = false
    }
  }
  
  /**
   * Get the appropriate CSS class for the MCP status button
   */
  function getMcpStatusClass(): string {
    if (isChecking) return 'bg-yellow-500'
    
    if (!mcpStatus) return 'bg-gray-500'
    
    switch (mcpStatus.status) {
      case 'running':
        return 'bg-green-500'
      case 'installed_not_running':
        return 'bg-orange-500'
      case 'not_configured':
        return 'bg-red-500'
      case 'not_installed':
        return 'bg-gray-500'
      case 'error':
        return 'bg-red-600'
      default:
        return 'bg-gray-500'
    }
  }
  
  /**
   * Get the appropriate text for the MCP status button
   */
  function getMcpStatusText(): string {
    if (isChecking) return 'Checking...'
    
    if (!mcpStatus) return 'Unknown'
    
    switch (mcpStatus.status) {
      case 'running':
        return 'Running'
      case 'installed_not_running':
        return 'Not Running'
      case 'not_configured':
        return 'Not Configured'
      case 'not_installed':
        return 'Not Installed'
      case 'error':
        return 'Error'
      default:
        return 'Unknown'
    }
  }
  
  /**
   * Refresh MCP status (clears cache and checks again)
   */
  async function refreshMcpStatus() {
    mcpService.clearCache()
    await checkMcpStatus()
  }
  
  /**
   * Opens the wallet connection modal
   * Triggered when user clicks the "Connect Wallet" button
   */
  function handleConnectWallet() {
    uiActions.openWalletModal()
  }
  
  // Check MCP status on component mount
  onMount(() => {
    checkMcpStatus()
    
    // Check status every 30 seconds
    const interval = setInterval(checkMcpStatus, 30000)
    
    return () => clearInterval(interval)
  })
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
          MCP Status Button
          - Dynamic styling based on actual server status
          - Color coding: Green (running), Orange (not running), Red (not configured/error), Gray (not installed)
          - Small size with monospace font for technical appearance
          - Click to refresh status
        -->
        <button 
          on:click={refreshMcpStatus}
          disabled={isChecking}
          class="{getMcpStatusClass()} text-white border-2 border-black rounded px-2 py-0.5 font-mono font-bold cursor-pointer text-xs disabled:cursor-not-allowed hover:opacity-80 transition-opacity"
          title="{mcpStatusMessage}"
        >
          {getMcpStatusText()}
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