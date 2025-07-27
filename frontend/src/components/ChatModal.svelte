<!--
  ChatModal.svelte - Interactive study chat interface with backend integration
  
  This modal provides an AI-powered chat interface where users can:
  - Ask questions about their study topic using the dual query system
  - View reference materials fetched from backend in a sidebar
  - Interact with Study4Me AI via LightRAG or ChatGPT+context
  - Access study session actions (podcast, mindmap, summarize)
  - Copy AI responses to clipboard
  
  Features:
  - Real-time chat interface with backend query API integration
  - Dual query system support (LightRAG knowledge graphs or ChatGPT with context)
  - Auto-clearing chat history when modal opens for fresh conversations
  - Rich text formatting for AI responses (headers, bold, lists, code blocks)
  - Dynamic references sidebar loaded from backend with detailed metadata
  - Session actions for enhanced learning
  - Processing method and time display for AI responses
  - Copy to clipboard functionality for AI responses
  - Keyboard shortcuts (Enter to send, Escape to close)
  - Comprehensive error handling and loading states
  - Accessible design with proper ARIA attributes
  
  Backend Integration:
  - Uses GET /query endpoint for synchronous responses
  - Uses GET /study-topics/{topic_id}/content endpoint for references
  - Supports study topic UUID-based queries
  - Handles both LightRAG and ChatGPT+context processing methods
  - Displays processing metadata (method, time) for transparency
-->

<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte'
  import Button from './Button.svelte'
  import { apiService } from '../services/api'
  import type { QueryResponse, ContentItem, StudyTopicSummaryResponse, StudyTopicMindmapResponse, DeleteContentResponse } from '../services/api'
  import mermaid from 'mermaid'
  
  // Props passed from parent component
  export let isOpen = false           // Controls modal visibility
  export let topicTitle = ''          // Title of the topic being studied
  export let studyTopicId = ''        // UUID of the study topic for backend queries
  
  // Event dispatcher for parent communication
  const dispatch = createEventDispatcher()
  
  // Chat state variables
  let chatMessages: Array<{id: string, content: string, type: 'user' | 'assistant', timestamp: Date, processingMethod?: string, processingTime?: number}> = []  // Message history
  let currentMessage = ''             // Current message being typed
  let isLoading = false              // Loading state during AI response
  let errorMessage = ''              // Error message for failed queries
  let copiedMessageId: string | null = null  // Track which message was just copied
  
  // References state
  let references: ContentItem[] = []
  let isLoadingReferences = false
  let referencesErrorMessage = ''

  // Summary modal state
  let isSummaryModalOpen = false
  let summaryData: StudyTopicSummaryResponse | null = null
  let isLoadingSummary = false
  let summaryErrorMessage = ''

  // Mindmap modal state
  let isMindmapModalOpen = false
  let mindmapData: StudyTopicMindmapResponse | null = null
  let isLoadingMindmap = false
  let mindmapErrorMessage = ''

  // Pan and zoom state for mindmap
  let mindmapScale = 1
  let mindmapTranslateX = 0
  let mindmapTranslateY = 0
  let isDragging = false
  let lastMouseX = 0
  let lastMouseY = 0

  // Reference content modal state
  let isReferenceModalOpen = false
  let selectedReference: ContentItem | null = null

  // Initialize Mermaid on component mount
  onMount(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'Arial, sans-serif'
    })
  })

  // Load references when modal opens and study topic changes
  $: if (isOpen && studyTopicId) {
    loadReferences()
    chatMessages = []
    errorMessage = ''
    copiedMessageId = null
  } else if (isOpen && !studyTopicId) {
    chatMessages = []
    errorMessage = ''
    copiedMessageId = null
    references = []
  }

  /**
   * Loads references (content items) for the current study topic
   */
  async function loadReferences() {
    if (!studyTopicId) return

    isLoadingReferences = true
    referencesErrorMessage = ''
    
    try {
      const response = await apiService.getStudyTopicContent(studyTopicId)
      references = response.content_items || []
    } catch (error) {
      console.error('Failed to load references:', error)
      referencesErrorMessage = error instanceof Error ? error.message : 'Failed to load references'
      references = []
    } finally {
      isLoadingReferences = false
    }
  }

  /**
   * Handles the summarize content button click
   * Calls backend to generate AI summary of all study topic content
   */
  async function handleSummarizeContent() {
    if (!studyTopicId) {
      summaryErrorMessage = 'No study topic selected'
      return
    }

    isLoadingSummary = true
    summaryErrorMessage = ''
    
    try {
      summaryData = await apiService.summarizeStudyTopicContent(studyTopicId)
      isSummaryModalOpen = true
    } catch (error) {
      console.error('Failed to summarize content:', error)
      summaryErrorMessage = error instanceof Error ? error.message : 'Failed to summarize content'
    } finally {
      isLoadingSummary = false
    }
  }

  /**
   * Closes the summary modal
   */
  function closeSummaryModal() {
    isSummaryModalOpen = false
    summaryData = null
    summaryErrorMessage = ''
  }

  /**
   * Handles the generate mindmap button click
   * Calls backend to generate Mermaid mindmap code of all study topic content
   */
  async function handleGenerateMindmap() {
    if (!studyTopicId) {
      mindmapErrorMessage = 'No study topic selected'
      return
    }

    isLoadingMindmap = true
    mindmapErrorMessage = ''
    
    try {
      mindmapData = await apiService.generateStudyTopicMindmap(studyTopicId)
      isMindmapModalOpen = true
      
      // Wait a bit for the modal to render, then render the mindmap
      setTimeout(() => {
        renderMindmap()
      }, 100)
    } catch (error) {
      console.error('Failed to generate mindmap:', error)
      mindmapErrorMessage = error instanceof Error ? error.message : 'Failed to generate mindmap'
    } finally {
      isLoadingMindmap = false
    }
  }

  /**
   * Renders the Mermaid mindmap in the designated container
   */
  async function renderMindmap() {
    if (!mindmapData?.mindmap) return
    
    const mindmapContainer = document.getElementById('mindmap-container')
    if (!mindmapContainer) return

    try {
      // Clear the container
      mindmapContainer.innerHTML = ''
      
      // Generate a unique ID for this mindmap
      const mindmapId = `mindmap-${Date.now()}`
      
      // Parse and render the mindmap
      const { svg } = await mermaid.render(mindmapId, mindmapData.mindmap)
      mindmapContainer.innerHTML = svg
    } catch (error) {
      console.error('Failed to render mindmap:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mindmapContainer.innerHTML = `<div class="text-red-600 p-4">Failed to render mindmap: ${errorMessage}</div>`
    }
  }

  /**
   * Closes the mindmap modal
   */
  function closeMindmapModal() {
    isMindmapModalOpen = false
    mindmapData = null
    mindmapErrorMessage = ''
    // Reset pan and zoom state
    mindmapScale = 1
    mindmapTranslateX = 0
    mindmapTranslateY = 0
    isDragging = false
  }

  /**
   * Handles mouse wheel zoom on mindmap
   */
  function handleMindmapWheel(event: WheelEvent) {
    event.preventDefault()
    
    const container = event.currentTarget as HTMLElement
    const rect = container.getBoundingClientRect()
    
    // Calculate mouse position relative to container
    const mouseX = event.clientX - rect.left
    const mouseY = event.clientY - rect.top
    
    // Calculate zoom
    const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1
    const newScale = Math.max(0.1, Math.min(5, mindmapScale * zoomFactor))
    
    // Calculate the point to zoom towards (mouse position relative to current transform)
    const zoomPointX = (mouseX - mindmapTranslateX) / mindmapScale
    const zoomPointY = (mouseY - mindmapTranslateY) / mindmapScale
    
    // Update scale
    mindmapScale = newScale
    
    // Adjust translation to keep the zoom point under the mouse
    mindmapTranslateX = mouseX - zoomPointX * newScale
    mindmapTranslateY = mouseY - zoomPointY * newScale
  }

  /**
   * Handles mouse down for panning
   */
  function handleMindmapMouseDown(event: MouseEvent) {
    isDragging = true
    lastMouseX = event.clientX
    lastMouseY = event.clientY
    
    // Prevent text selection during drag
    event.preventDefault()
  }

  /**
   * Handles mouse move for panning
   */
  function handleMindmapMouseMove(event: MouseEvent) {
    if (!isDragging) return
    
    const deltaX = event.clientX - lastMouseX
    const deltaY = event.clientY - lastMouseY
    
    mindmapTranslateX += deltaX
    mindmapTranslateY += deltaY
    
    lastMouseX = event.clientX
    lastMouseY = event.clientY
  }

  /**
   * Handles mouse up to stop panning
   */
  function handleMindmapMouseUp() {
    isDragging = false
  }

  /**
   * Resets mindmap zoom and pan to default
   */
  function resetMindmapView() {
    mindmapScale = 1
    mindmapTranslateX = 0
    mindmapTranslateY = 0
  }

  /**
   * Fits mindmap to container size
   */
  function fitMindmapToContainer() {
    const container = document.getElementById('mindmap-container')
    const svg = container?.querySelector('svg')
    
    if (!container || !svg) return
    
    const containerRect = container.getBoundingClientRect()
    const svgRect = svg.getBoundingClientRect()
    
    // Calculate scale to fit content
    const scaleX = (containerRect.width - 40) / svg.viewBox.baseVal.width
    const scaleY = (containerRect.height - 40) / svg.viewBox.baseVal.height
    const newScale = Math.min(scaleX, scaleY, 1) // Don't scale up beyond 100%
    
    // Center the mindmap
    mindmapScale = newScale
    mindmapTranslateX = (containerRect.width - svg.viewBox.baseVal.width * newScale) / 2
    mindmapTranslateY = (containerRect.height - svg.viewBox.baseVal.height * newScale) / 2
  }

  /**
   * Opens the reference content modal with the selected reference
   */
  function openReferenceModal(reference: ContentItem) {
    selectedReference = reference
    isReferenceModalOpen = true
  }

  /**
   * Closes the reference content modal
   */
  function closeReferenceModal() {
    isReferenceModalOpen = false
    selectedReference = null
  }

  /**
   * Downloads a file (for document references with download URLs)
   */
  function downloadReference(reference: ContentItem) {
    if (reference.file_path && studyTopicId) {
      // Create a download link using the backend file serve endpoint with study topic organization
      const fileName = reference.file_path.split('/').pop() || 'download'
      const downloadUrl = `http://localhost:8000/files/${studyTopicId}/${encodeURIComponent(fileName)}`
      
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    }
  }

  /**
   * Deletes a content item/reference
   */
  async function deleteReference(reference: ContentItem, event: MouseEvent) {
    // Prevent opening the reference modal when delete button is clicked
    event.stopPropagation()
    
    if (!confirm(`Are you sure you want to delete "${reference.title}"? This action cannot be undone.`)) {
      return
    }

    try {
      const response: DeleteContentResponse = await apiService.deleteContent(reference.content_id)
      
      // Remove the reference from the local array
      references = references.filter(ref => ref.content_id !== reference.content_id)
      
      // Show success message briefly
      referencesErrorMessage = `✅ Deleted "${response.title}" successfully`
      setTimeout(() => {
        if (referencesErrorMessage.includes('✅')) {
          referencesErrorMessage = ''
        }
      }, 3000)
      
      // Dispatch event to parent component to refresh data if needed
      dispatch('contentDeleted', { contentId: reference.content_id, title: reference.title })
      
    } catch (error) {
      console.error('Failed to delete reference:', error)
      referencesErrorMessage = `❌ Failed to delete "${reference.title}": ${error instanceof Error ? error.message : 'Unknown error'}`
    }
  }

  /**
   * Copies text to clipboard and provides user feedback
   * @param text - Text to copy to clipboard
   * @param messageId - ID of the message being copied for visual feedback
   */
  async function copyToClipboard(text: string, messageId: string) {
    try {
      await navigator.clipboard.writeText(text)
      copiedMessageId = messageId
      
      // Reset the copied state after 2 seconds
      setTimeout(() => {
        copiedMessageId = null
      }, 2000)
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        copiedMessageId = messageId
        setTimeout(() => {
          copiedMessageId = null
        }, 2000)
      } catch (fallbackError) {
        console.error('Fallback copy failed:', fallbackError)
      }
      document.body.removeChild(textArea)
    }
  }

  /**
   * Formats AI response text to handle markdown-like formatting
   * Converts markdown headers, bold text, lists, and preserves line breaks
   * @param text - Raw text from AI response
   * @returns Formatted HTML string
   */
  function formatResponseText(text: string): string {
    if (!text) return ''
    
    return text
      // Handle code blocks (``` or ``` language)
      .replace(/```[\w]*\n([\s\S]*?)\n```/g, '<pre class="bg-gray-100 border border-gray-300 rounded p-3 mt-2 mb-2 text-xs overflow-x-auto"><code>$1</code></pre>')
      // Convert ### headers to styled headers
      .replace(/^### (.+)$/gm, '<h3 class="text-base font-bold mt-4 mb-2 text-black">$1</h3>')
      // Convert ## headers to slightly larger headers
      .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold mt-4 mb-2 text-black">$1</h2>')
      // Convert ** bold text ** to bold
      .replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold">$1</strong>')
      // Convert inline code `code` to styled code
      .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded text-xs font-mono">$1</code>')
      // Convert - bullet points to styled list items (handle nested bullets)
      .replace(/^[\s]*- (.+)$/gm, (match, p1) => {
        const indentMatch = match.match(/^(\s*)/)
        const indent = indentMatch ? indentMatch[1].length : 0
        const marginLeft = Math.max(4, indent * 2 + 4)
        return `<div class="mb-1" style="margin-left: ${marginLeft}px">• ${p1}</div>`
      })
      // Convert numbered lists (1. 2. etc.)
      .replace(/^(\d+)\. (.+)$/gm, '<div class="ml-4 mb-1">$1. $2</div>')
      // Convert double line breaks to paragraph breaks
      .replace(/\n\n/g, '</p><p class="mb-3">')
      // Convert single line breaks to br tags
      .replace(/\n/g, '<br>')
      // Wrap the whole thing in a paragraph if it doesn't start with a header or pre
      .replace(/^(?!<[h2-3]|<pre)/, '<p class="mb-3">')
      // Add closing paragraph tag at the end if needed
      .replace(/([^>])$/, '$1</p>')
  }
  
  /**
   * Closes the chat modal and notifies parent component
   * Resets any temporary state when modal closes
   */
  function handleClose() {
    dispatch('close')
  }
  
  /**
   * Handles clicks outside the modal content to close the modal
   * Only closes if user clicks the backdrop, not the modal content itself
   * @param event - Mouse click event to check target
   */
  function handleOutsideClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose()
    }
  }
  
  /**
   * Handles sending a chat message to the AI assistant
   * Validates input, adds user message to chat, and calls backend query API
   * Integrates with Study4Me backend dual query system (LightRAG or ChatGPT+context)
   */
  async function handleSendMessage() {
    // Prevent sending empty messages or multiple simultaneous requests
    if (!currentMessage.trim() || isLoading) return
    
    // Validate that we have a study topic ID
    if (!studyTopicId) {
      errorMessage = 'No study topic selected. Please select a topic first.'
      return
    }
    
    // Create user message object
    const userMessage = {
      id: Date.now().toString(),          // Simple ID generation (timestamp-based)
      content: currentMessage.trim(),     // Clean user input
      type: 'user' as const,             // Message type for styling
      timestamp: new Date()              // When message was sent
    }
    
    // Add user message to chat history
    chatMessages = [...chatMessages, userMessage]
    const messageToSend = currentMessage  // Store message before clearing input
    currentMessage = ''                   // Clear input field immediately
    isLoading = true                     // Show loading state
    errorMessage = ''                    // Clear any previous errors
    
    try {
      // Call backend query API using the API service
      const data: QueryResponse = await apiService.queryStudyTopic(studyTopicId, messageToSend, 'hybrid')
      
      // Create assistant message with response data
      const assistantMessage = {
        id: (Date.now() + 1).toString(),   // Ensure unique ID
        content: data.result || 'No response received',
        type: 'assistant' as const,        // AI response type
        timestamp: new Date(),             // Response timestamp
        processingMethod: data.processing_method,
        processingTime: data.processing_time_seconds
      }
      
      chatMessages = [...chatMessages, assistantMessage]  // Add AI response to chat
      
    } catch (error) {
      console.error('Query failed:', error)
      const errorMsg = error instanceof Error ? error.message : 'Unknown error occurred'
      errorMessage = `Failed to get response: ${errorMsg}`
      
      // Add error message to chat
      const errorChatMessage = {
        id: (Date.now() + 1).toString(),
        content: `Sorry, I encountered an error: ${errorMsg}`,
        type: 'assistant' as const,
        timestamp: new Date()
      }
      chatMessages = [...chatMessages, errorChatMessage]
      
    } finally {
      isLoading = false                                   // Clear loading state
    }
  }
  
  /**
   * Handles keyboard shortcuts in the message input
   * - Enter: Send message (without Shift)
   * - Shift+Enter: New line in message
   * @param event - Keyboard event to check for shortcuts
   */
  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()  // Prevent default textarea behavior
      handleSendMessage()     // Send the message
    }
    // Shift+Enter allows multiline messages (default textarea behavior)
  }
</script>

<!-- 
  ========================================
  CHAT MODAL TEMPLATE
  ========================================
  
  Three-column layout for comprehensive study experience:
  1. Left: Source materials sidebar
  2. Center: Chat interface with messages and input
  3. Right: Study session actions (podcast, mindmap, etc.)
-->
{#if isOpen}
  <!-- 
    Modal Backdrop
    - Full screen overlay with semi-transparent background
    - Handles outside clicks and keyboard shortcuts
    - Accessible modal with proper ARIA attributes
  -->
  <div 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    on:click={handleOutsideClick}
    on:keydown={(e) => e.key === 'Escape' && handleClose()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
    tabindex="-1"
  >
    <!-- 
      Modal Container
      - Large modal taking up most of screen space (w-full max-w-6xl h-4/5)
      - Neobrutalism styling with thick black border
      - Flexbox column layout for header and body sections
    -->
    <div 
      class="bg-white border-4 border-black w-full max-w-6xl h-4/5 flex flex-col"
    >
      <!-- 
        Modal Header
        - Contains topic title and close button
        - Fixed height with bottom border separator
        - White background to stand out from body
      -->
      <div class="flex justify-between items-center p-4 border-b-4 border-black bg-white">
        <!-- Title section -->
        <div>
          <!-- Main modal title with topic name -->
          <h2 id="modal-title" class="text-xl font-bold font-mono text-black mb-1">
            Study: {topicTitle}
          </h2>
          <!-- Subtitle explaining modal purpose -->
          <p class="text-sm text-gray-600">Ask questions about your topic sources</p>
        </div>
        
        <!-- Close button with accessibility attributes -->
        <button 
          class="bg-brand-pink text-white border-2 border-black rounded px-3 py-2 font-mono font-bold cursor-pointer text-lg hover:bg-opacity-90"
          on:click={handleClose}
          aria-label="Close modal"
        >
          ×
        </button>
      </div>
      
      <!-- 
        Modal Body - Three Column Layout
        - Uses flexbox for responsive three-column layout
        - flex-1 to fill remaining space after header
        - overflow-hidden to prevent layout issues
      -->
      <div class="flex flex-1 overflow-hidden">
        
        <!-- 
          Left Sidebar - References List
          - 1/4 width with yellow background for visual distinction
          - Shows all available reference materials for the topic
          - Scrollable if many references are available
        -->
        <div class="w-1/4 border-r-4 border-black p-4 overflow-y-auto bg-brand-yellow">
          <h3 class="text-lg font-bold mb-4 font-mono text-black">
            References
          </h3>
          
          <!-- Loading state -->
          {#if isLoadingReferences}
            <div class="text-center p-4">
              <div class="text-sm text-gray-600">Loading references...</div>
            </div>
          <!-- Error/Success state -->
          {:else if referencesErrorMessage}
            <div class="p-3 {referencesErrorMessage.includes('✅') ? 'bg-green-100 border-green-500 text-green-700' : 'bg-red-100 border-red-500 text-red-700'} border-2 text-sm mb-4">
              {#if referencesErrorMessage.includes('✅')}
                {referencesErrorMessage}
              {:else}
                <strong>Error:</strong> {referencesErrorMessage}
              {/if}
            </div>
          <!-- Empty state -->
          {:else if references.length === 0}
            <p class="text-sm text-gray-600">No references available</p>
          {:else}
            <!-- List of available references -->
            <div class="flex flex-col gap-2">
              {#each references as reference}
                <!-- 
                  Individual reference card
                  - White background with hover effects
                  - Shows title, type, and metadata with color transitions
                  - Interactive hover state with blue background
                  - Clickable to open reference content modal
                  - Delete button in top-right corner
                -->
                <div 
                  class="p-3 border-2 border-black bg-white cursor-pointer transition-all duration-300 hover:bg-brand-blue group relative"
                  on:click={() => openReferenceModal(reference)}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && openReferenceModal(reference)}
                  role="button"
                  tabindex="0"
                  aria-label="View content for {reference.title}">
                  
                  <!-- Delete button in top-right corner -->
                  <button
                    class="absolute top-2 right-2 bg-red-500 text-white border border-black rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                    on:click={(e) => deleteReference(reference, e)}
                    title="Delete this source"
                    aria-label="Delete {reference.title}"
                  >
                    ×
                  </button>
                  
                  <!-- Reference title with hover color change -->
                  <div class="font-bold text-sm font-mono text-black group-hover:text-white transition-colors duration-300 mb-1 pr-6">
                    {reference.title}
                  </div>
                  <!-- Reference type indicator -->
                  <div class="text-xs text-gray-600 uppercase group-hover:text-white transition-colors duration-300 mb-1">
                    {reference.content_type}
                  </div>
                  <!-- Reference metadata -->
                  <div class="text-xs text-gray-500 group-hover:text-white transition-colors duration-300">
                    {reference.content_length} chars • {reference.number_tokens} tokens
                  </div>
                  <!-- Source URL or file path if available -->
                  {#if reference.source_url}
                    <div class="text-xs text-blue-600 group-hover:text-white transition-colors duration-300 mt-1 truncate" title={reference.source_url}>
                      🔗 {reference.source_url}
                    </div>
                  {:else if reference.file_path}
                    <div class="text-xs text-green-600 group-hover:text-white transition-colors duration-300 mt-1 truncate" title={reference.file_path}>
                      📄 {reference.file_path.split('/').pop()}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>
        
        <!-- 
          Center Column - Chat Messages Interface
          - Main chat area taking up most horizontal space
          - Two-part layout: messages area (top) and input area (bottom)
          - Scrollable message history with responsive message bubbles
        -->
        <div class="flex-1 flex flex-col">
          
          <!-- 
            Messages Container
            - Scrollable area for chat history
            - Light gray background to distinguish from input area
            - Shows empty state when no messages exist
          -->
          <div class="flex-1 p-4 overflow-y-auto bg-gray-50">
            <!-- Empty state - shown when chat is empty -->
            {#if chatMessages.length === 0}
              <div class="text-center text-gray-600 mt-8">
                <p class="text-lg font-bold mb-2 font-mono">
                  Start a conversation
                </p>
                <p class="text-sm">Ask questions about your topic to get insights from your sources.</p>
              </div>
            {:else}
              <!-- Message history when chat has messages -->
              <div class="flex flex-col gap-4">
                <!-- Loop through all chat messages -->
                {#each chatMessages as message}
                  <!-- 
                    Message container with dynamic alignment
                    - User messages aligned right
                    - AI messages aligned left
                  -->
                  <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'}">
                    <!-- 
                      Message bubble
                      - Responsive max-width for different screen sizes
                      - Different background colors for user vs AI
                      - Contains sender, content, and timestamp
                    -->
                    <div class="max-w-sm lg:max-w-md xl:max-w-lg p-3 border-2 border-black {message.type === 'user' ? 'bg-blue-100' : 'bg-white'}">
                      <!-- Message header with sender and copy button for AI messages -->
                      <div class="flex justify-between items-start mb-1">
                        <!-- Sender identification -->
                        <div class="font-bold text-xs uppercase font-mono">
                          {message.type === 'user' ? 'You' : 'Study4Me AI'}
                        </div>
                        
                        <!-- Copy button for AI messages -->
                        {#if message.type === 'assistant'}
                          <button 
                            class="text-xs bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded px-2 py-1 font-mono transition-colors duration-200"
                            on:click={() => copyToClipboard(message.content, message.id)}
                            title="Copy to clipboard"
                          >
                            {copiedMessageId === message.id ? 'Copied!' : 'Copy'}
                          </button>
                        {/if}
                      </div>
                      
                      <!-- Message content with formatting support -->
                      <div class="text-sm leading-6">
                        {#if message.type === 'assistant'}
                          {@html formatResponseText(message.content)}
                        {:else}
                          {message.content}
                        {/if}
                      </div>
                      
                      <!-- Message metadata (timestamp and processing info for AI messages) -->
                      <div class="text-xs text-gray-600 mt-2">
                        {message.timestamp.toLocaleTimeString()}
                        {#if message.type === 'assistant' && message.processingMethod}
                          <span class="ml-2 text-blue-600">
                            • {message.processingMethod}
                            {#if message.processingTime}
                              ({message.processingTime}s)
                            {/if}
                          </span>
                        {/if}
                      </div>
                    </div>
                  </div>
                {/each}
                
                <!-- Loading indicator when AI is responding -->
                {#if isLoading}
                  <div class="flex justify-start">
                    <div class="max-w-sm lg:max-w-md xl:max-w-lg p-3 border-2 border-black bg-white">
                      <div class="font-bold text-xs mb-1 uppercase font-mono">
                        Study4Me AI
                      </div>
                      <div class="text-sm">
                        <span>Thinking...</span>
                      </div>
                    </div>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
          
          <!-- 
            Message Input Area
            - Fixed at bottom of chat interface
            - Contains textarea and send button
            - White background with top border separator
            - Includes keyboard shortcut instructions
            - Shows error messages when queries fail
          -->
          <div class="p-4 border-t-4 border-black bg-white">
            <!-- Error message display -->
            {#if errorMessage}
              <div class="mb-3 p-3 bg-red-100 border-2 border-red-500 text-red-700 text-sm">
                <strong>Error:</strong> {errorMessage}
              </div>
            {/if}
            <!-- Input controls container -->
            <div class="flex gap-2">
              <!-- 
                Message textarea
                - Auto-growing height with min/max constraints
                - Disabled during loading to prevent multiple sends
                - Supports keyboard shortcuts (Enter/Shift+Enter)
              -->
              <textarea
                bind:value={currentMessage}
                on:keydown={handleKeyPress}
                placeholder="Ask a question about your topic..."
                class="flex-1 p-3 border-2 border-black resize-none font-inter min-h-15 max-h-30"
                rows="2"
                disabled={isLoading}
              ></textarea>
              
              <!-- 
                Send button
                - Disabled when no message or loading
                - Visual feedback with opacity changes
                - Consistent neobrutalism styling
              -->
              <button 
                class="bg-brand-blue text-white border-4 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer {!currentMessage.trim() || isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-opacity-90'}"
                on:click={handleSendMessage}
                disabled={!currentMessage.trim() || isLoading}
              >
                Send
              </button>
            </div>
            
            <!-- Help text for keyboard shortcuts -->
            <div class="text-xs text-gray-600 mt-2">
              Press Enter to send, Shift+Enter for new line
            </div>
          </div>
        </div>
        
        <!-- 
          Right Sidebar - Study Session Actions
          - Narrower sidebar (1/5 width) for action buttons
          - Yellow background for visual consistency with left sidebar
          - Contains study enhancement tools
        -->
        <div class="w-1/5 border-l-4 border-black p-4 bg-brand-yellow">
          <h3 class="text-lg font-bold mb-4 font-mono text-black">
            Session
          </h3>
          
          <!-- Action buttons container -->
          <div class="flex flex-col gap-3">
            
            <!-- Create Podcast Button -->
            <!-- TODO: Implement podcast generation functionality -->
            <button class="w-full h-12 p-3 border-2 border-black bg-brand-pink text-white cursor-pointer font-mono font-bold text-sm flex items-center justify-center gap-2 hover:bg-opacity-90">
              <!-- Play icon for podcast -->
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
              </svg>
              Create Podcast
            </button>
            
            <!-- Create Mindmap Button -->
            <button 
              class="w-full h-12 p-3 border-2 border-black bg-brand-pink text-white cursor-pointer font-mono font-bold text-sm flex items-center justify-center gap-2 hover:bg-opacity-90 {isLoadingMindmap ? 'opacity-50 cursor-not-allowed' : ''}"
              on:click={handleGenerateMindmap}
              disabled={isLoadingMindmap || !studyTopicId}
            >
              <!-- Network/mindmap icon or loading spinner -->
              {#if isLoadingMindmap}
                <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              {:else}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <circle cx="9" cy="9" r="2"/>
                  <circle cx="15" cy="15" r="2"/>
                  <circle cx="9" cy="15" r="2"/>
                  <circle cx="15" cy="9" r="2"/>
                  <path d="M9 7v4m0 0v4m0-4h6m-6 0H3m6-6h6m-6 6v4"/>
                  <line x1="7" y1="9" x2="17" y2="9"/>
                  <line x1="9" y1="7" x2="9" y2="17"/>
                  <line x1="15" y1="7" x2="15" y2="17"/>
                  <line x1="7" y1="15" x2="17" y2="15"/>
                </svg>
              {/if}
              {isLoadingMindmap ? 'Generating...' : 'Create Mindmap'}
            </button>
            
            <!-- Summarize Content Button -->
            <button 
              class="w-full h-12 p-3 border-2 border-black bg-brand-pink text-white cursor-pointer font-mono font-bold text-sm flex items-center justify-center gap-2 hover:bg-opacity-90 {isLoadingSummary ? 'opacity-50 cursor-not-allowed' : ''}"
              on:click={handleSummarizeContent}
              disabled={isLoadingSummary || !studyTopicId}
            >
              <!-- Document/summary icon or loading spinner -->
              {#if isLoadingSummary}
                <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              {:else}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 3h18v18H3V3zm2 2v14h14V5H5zm2 2h10v2H7V7zm0 4h10v2H7v-2zm0 4h7v2H7v-2z"/>
                </svg>
              {/if}
              {isLoadingSummary ? 'Summarizing...' : 'Summarize Content'}
            </button>

            <!-- Summary error message -->
            {#if summaryErrorMessage}
              <div class="p-2 bg-red-100 border-2 border-red-500 text-red-700 text-xs">
                <strong>Error:</strong> {summaryErrorMessage}
              </div>
            {/if}

            <!-- Mindmap error message -->
            {#if mindmapErrorMessage}
              <div class="p-2 bg-red-100 border-2 border-red-500 text-red-700 text-xs">
                <strong>Error:</strong> {mindmapErrorMessage}
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Summary Modal -->
{#if isSummaryModalOpen && summaryData}
  <div 
    class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-[70]"
    on:click={(e) => e.target === e.currentTarget && closeSummaryModal()}
    on:keydown={(e) => e.key === 'Escape' && closeSummaryModal()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="summary-modal-title"
    tabindex="-1"
  >
    <div class="bg-white border-4 border-black w-full max-w-4xl max-h-[90vh] flex flex-col">
      <!-- Summary Modal Header -->
      <div class="flex justify-between items-center p-4 border-b-4 border-black bg-white">
        <div>
          <h2 id="summary-modal-title" class="text-xl font-bold font-mono text-black mb-1">
            Content Summary
          </h2>
          <p class="text-sm text-gray-600">
            AI-generated summary of {summaryData.topic_name}
          </p>
        </div>
        <button 
          class="bg-brand-pink text-white border-2 border-black rounded px-3 py-2 font-mono font-bold cursor-pointer text-lg hover:bg-opacity-90"
          on:click={closeSummaryModal}
          aria-label="Close summary modal"
        >
          ×
        </button>
      </div>

      <!-- Summary Modal Body -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- Summary metadata -->
        <div class="bg-gray-50 border-2 border-gray-300 p-4 mb-6 text-sm">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span class="font-bold text-gray-700">Content Items:</span>
              <div class="text-gray-600">{summaryData.content_items_processed}</div>
            </div>
            <div>
              <span class="font-bold text-gray-700">Total Length:</span>
              <div class="text-gray-600">{summaryData.total_content_length.toLocaleString()} chars</div>
            </div>
            <div>
              <span class="font-bold text-gray-700">Summary Length:</span>
              <div class="text-gray-600">{summaryData.summary_length.toLocaleString()} chars</div>
            </div>
            <div>
              <span class="font-bold text-gray-700">Processing Time:</span>
              <div class="text-gray-600">{summaryData.processing_time_seconds}s</div>
            </div>
          </div>
        </div>

        <!-- Summary content -->
        <div class="prose max-w-none">
          <div class="text-gray-800 leading-relaxed">
            {@html formatResponseText(summaryData.summary)}
          </div>
        </div>

        <!-- Copy summary button -->
        <div class="mt-6 pt-4 border-t-2 border-gray-200">
          <button 
            class="bg-brand-blue text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer hover:bg-opacity-90"
            on:click={() => summaryData && copyToClipboard(summaryData.summary, 'summary')}
          >
            {copiedMessageId === 'summary' ? 'Copied!' : 'Copy Summary'}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Mindmap Modal -->
{#if isMindmapModalOpen && mindmapData}
  <div 
    class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-[70]"
    on:click={(e) => e.target === e.currentTarget && closeMindmapModal()}
    on:keydown={(e) => e.key === 'Escape' && closeMindmapModal()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="mindmap-modal-title"
    tabindex="-1"
  >
    <div class="bg-white border-4 border-black w-full max-w-6xl max-h-[95vh] flex flex-col">
      <!-- Mindmap Modal Header -->
      <div class="flex justify-between items-center p-4 border-b-4 border-black bg-white">
        <div>
          <h2 id="mindmap-modal-title" class="text-xl font-bold font-mono text-black mb-1">
            Study Mindmap
          </h2>
          <p class="text-sm text-gray-600">
            Visual knowledge map of {mindmapData.topic_name}
          </p>
        </div>
        <button 
          class="bg-brand-pink text-white border-2 border-black rounded px-3 py-2 font-mono font-bold cursor-pointer text-lg hover:bg-opacity-90"
          on:click={closeMindmapModal}
          aria-label="Close mindmap modal"
        >
          ×
        </button>
      </div>

      <!-- Mindmap Modal Body -->
      <div class="flex-1 overflow-y-auto">
        <!-- Mindmap metadata -->
        <div class="bg-gray-50 border-b-2 border-gray-300 p-4 text-sm">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span class="font-bold text-gray-700">Content Items:</span>
              <div class="text-gray-600">{mindmapData.content_items_processed}</div>
            </div>
            <div>
              <span class="font-bold text-gray-700">Total Length:</span>
              <div class="text-gray-600">{mindmapData.total_content_length.toLocaleString()} chars</div>
            </div>
            <div>
              <span class="font-bold text-gray-700">Mindmap Size:</span>
              <div class="text-gray-600">{mindmapData.mindmap_length.toLocaleString()} chars</div>
            </div>
            <div>
              <span class="font-bold text-gray-700">Processing Time:</span>
              <div class="text-gray-600">{mindmapData.processing_time_seconds}s</div>
            </div>
          </div>
          {#if mindmapData.cached}
            <div class="mt-2 text-blue-600 text-xs">
              💾 Cached result - generated previously
            </div>
          {/if}
        </div>

        <!-- Mindmap visualization container -->
        <div class="p-6 flex justify-center">
          <div class="w-full max-w-full overflow-hidden">
            <div 
              id="mindmap-container" 
              class="min-h-[400px] border-2 border-gray-300 rounded bg-white p-4 flex items-center justify-center relative overflow-hidden cursor-grab select-none"
              class:cursor-grabbing={isDragging}
              role="img"
              aria-label="Interactive mindmap visualization - scroll to zoom, drag to pan"
              on:wheel={handleMindmapWheel}
              on:mousedown={handleMindmapMouseDown}
              on:mousemove={handleMindmapMouseMove}
              on:mouseup={handleMindmapMouseUp}
              on:mouseleave={handleMindmapMouseUp}
              style="transform: translate({mindmapTranslateX}px, {mindmapTranslateY}px) scale({mindmapScale}); transform-origin: 0 0;"
            >
              <div class="text-gray-500">Loading mindmap...</div>
            </div>
          </div>
        </div>

        <!-- Zoom and Pan Controls -->
        <div class="p-4 border-t-2 border-gray-200 bg-gray-50">
          <div class="flex gap-3 justify-center mb-4">
            <!-- Zoom controls -->
            <div class="flex gap-2 items-center bg-white border-2 border-black rounded px-3 py-2">
              <button 
                class="w-8 h-8 bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded text-center text-sm font-bold flex items-center justify-center"
                on:click={() => mindmapScale = Math.max(0.1, mindmapScale * 0.8)}
                title="Zoom out"
              >
                −
              </button>
              <span class="text-sm font-mono px-2 min-w-[4rem] text-center">
                {Math.round(mindmapScale * 100)}%
              </span>
              <button 
                class="w-8 h-8 bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded text-center text-sm font-bold flex items-center justify-center"
                on:click={() => mindmapScale = Math.min(5, mindmapScale * 1.25)}
                title="Zoom in"
              >
                +
              </button>
            </div>

            <!-- View controls -->
            <button 
              class="bg-yellow-500 text-white border-2 border-black rounded px-3 py-2 font-mono font-bold text-sm cursor-pointer hover:bg-opacity-90"
              on:click={resetMindmapView}
              title="Reset zoom and pan"
            >
              Reset View
            </button>
            <button 
              class="bg-purple-500 text-white border-2 border-black rounded px-3 py-2 font-mono font-bold text-sm cursor-pointer hover:bg-opacity-90"
              on:click={fitMindmapToContainer}
              title="Fit mindmap to container"
            >
              Fit to View
            </button>
          </div>

          <!-- Help text -->
          <div class="text-xs text-gray-600 text-center mb-4">
            🖱️ Scroll to zoom • Drag to pan • Use controls above for precise adjustments
          </div>

          <!-- Action buttons -->
          <div class="flex gap-3 justify-center">
            <button 
              class="bg-brand-blue text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer hover:bg-opacity-90"
              on:click={() => mindmapData && copyToClipboard(mindmapData.mindmap, 'mindmap')}
            >
              {copiedMessageId === 'mindmap' ? 'Copied!' : 'Copy Mermaid Code'}
            </button>
            <button 
              class="bg-green-500 text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer hover:bg-opacity-90"
              on:click={() => {
                const svg = document.querySelector('#mindmap-container svg');
                if (svg) {
                  const svgData = new XMLSerializer().serializeToString(svg);
                  const blob = new Blob([svgData], { type: 'image/svg+xml' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${mindmapData?.topic_name.replace(/[^a-zA-Z0-9]/g, '_')}_mindmap.svg`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);
                }
              }}
            >
              Download SVG
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Reference Content Modal -->
{#if isReferenceModalOpen && selectedReference}
  <div 
    class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-[80]"
    on:click={(e) => e.target === e.currentTarget && closeReferenceModal()}
    on:keydown={(e) => e.key === 'Escape' && closeReferenceModal()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="reference-modal-title"
    tabindex="-1"
  >
    <div class="bg-white border-4 border-black w-full max-w-4xl max-h-[90vh] flex flex-col">
      <!-- Reference Modal Header -->
      <div class="flex justify-between items-center p-4 border-b-4 border-black bg-white">
        <div class="flex-1 mr-4">
          <h2 id="reference-modal-title" class="text-xl font-bold font-mono text-black mb-1">
            {selectedReference.title}
          </h2>
          <div class="flex items-center gap-4 text-sm text-gray-600">
            <span class="uppercase font-bold">{selectedReference.content_type}</span>
            <span>{selectedReference.content_length} chars • {selectedReference.number_tokens} tokens</span>
          </div>
        </div>
        <button 
          class="bg-brand-pink text-white border-2 border-black rounded px-3 py-2 font-mono font-bold cursor-pointer text-lg hover:bg-opacity-90"
          on:click={closeReferenceModal}
          aria-label="Close reference modal"
        >
          ×
        </button>
      </div>

      <!-- Reference Modal Body -->
      <div class="flex-1 overflow-y-auto">
        
        <!-- Source Info Section -->
        <div class="bg-gray-50 border-b-2 border-gray-300 p-4">
          <div class="flex flex-wrap gap-4 items-center">
            <!-- Source URL (for YouTube/Web content) -->
            {#if selectedReference.source_url}
              <div class="flex items-center gap-2">
                <span class="font-bold text-gray-700">Source:</span>
                <a 
                  href={selectedReference.source_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="text-blue-600 hover:text-blue-800 underline break-all"
                >
                  {selectedReference.source_url}
                </a>
                <button
                  class="bg-blue-500 text-white border border-black rounded px-2 py-1 text-xs font-mono font-bold hover:bg-opacity-90"
                  on:click={() => window.open(selectedReference.source_url, '_blank')}
                >
                  Open Link
                </button>
              </div>
            <!-- File Path (for documents) -->
            {:else if selectedReference?.file_path}
              <div class="flex items-center gap-2">
                <span class="font-bold text-gray-700">File:</span>
                <span class="text-green-600 font-mono text-sm">
                  {selectedReference.file_path.split('/').pop()}
                </span>
                <button
                  class="bg-green-500 text-white border border-black rounded px-2 py-1 text-xs font-mono font-bold hover:bg-opacity-90"
                  on:click={() => selectedReference && downloadReference(selectedReference)}
                >
                  Download
                </button>
              </div>
            {/if}
          </div>
          
          <!-- Metadata if available -->
          {#if selectedReference.metadata}
            <div class="mt-3 text-xs text-gray-600">
              <span class="font-bold">Metadata:</span>
              <pre class="mt-1 bg-white border border-gray-300 rounded p-2 text-xs overflow-x-auto">{JSON.stringify(JSON.parse(selectedReference.metadata), null, 2)}</pre>
            </div>
          {/if}
        </div>

        <!-- Content Section -->
        <div class="p-6">
          <div class="mb-4 flex justify-between items-center">
            <h3 class="text-lg font-bold font-mono text-black">Content</h3>
            <button 
              class="bg-brand-blue text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer hover:bg-opacity-90"
              on:click={() => selectedReference && copyToClipboard(selectedReference.content, `reference-${selectedReference.content_id}`)}
            >
              {copiedMessageId === `reference-${selectedReference.content_id}` ? 'Copied!' : 'Copy Content'}
            </button>
          </div>
          
          <!-- Content Display -->
          <div class="bg-gray-50 border-2 border-gray-300 rounded p-4 max-h-96 overflow-y-auto">
            <pre class="whitespace-pre-wrap text-sm leading-6 font-mono text-gray-800">{selectedReference.content}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- End of conditional modal rendering -->

<style>
  textarea {
    min-height: 60px;
    max-height: 120px;
  }
  
  textarea::-webkit-scrollbar {
    width: 4px;
  }
  
  textarea::-webkit-scrollbar-track {
    background: #f1f1f1;
  }
  
  textarea::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 2px;
  }
  
  textarea::-webkit-scrollbar-thumb:hover {
    background: #555;
  }

  /* Mindmap pan and zoom styles */
  .cursor-grabbing {
    cursor: grabbing !important;
  }

  #mindmap-container {
    transition: none;
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
  }

  #mindmap-container svg {
    pointer-events: none;
  }
</style>