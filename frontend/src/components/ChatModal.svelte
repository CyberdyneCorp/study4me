<!--
  ChatModal.svelte - Interactive study chat interface
  
  This modal provides an AI-powered chat interface where users can:
  - Ask questions about their study topic
  - View source materials in a sidebar
  - Interact with Study4Me AI for learning assistance
  - Access study session actions (podcast, mindmap, summarize)
  
  Features:
  - Real-time chat interface with message history
  - Source materials sidebar for reference
  - Session actions for enhanced learning
  - Keyboard shortcuts (Enter to send, Escape to close)
  - Loading states and error handling
  - Accessible design with proper ARIA attributes
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  import Button from './Button.svelte'
  
  // Props passed from parent component
  export let isOpen = false           // Controls modal visibility
  export let topicTitle = ''          // Title of the topic being studied
  export let sources: Array<{id: string, title: string, type: string}> = []  // Available source materials
  
  // Event dispatcher for parent communication
  const dispatch = createEventDispatcher()
  
  // Chat state variables
  let chatMessages: Array<{id: string, content: string, type: 'user' | 'assistant', timestamp: Date}> = []  // Message history
  let currentMessage = ''             // Current message being typed
  let isLoading = false              // Loading state during AI response
  
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
   * Validates input, adds user message to chat, and initiates AI response
   * Currently uses simulated API response - will be replaced with actual AI integration
   */
  async function handleSendMessage() {
    // Prevent sending empty messages or multiple simultaneous requests
    if (!currentMessage.trim() || isLoading) return
    
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
    
    // TODO: Replace with actual AI API call
    // Simulate API response delay
    setTimeout(() => {
      const assistantMessage = {
        id: (Date.now() + 1).toString(),   // Ensure unique ID
        content: `I understand you're asking about "${messageToSend}". Based on the sources in this topic, here's what I can tell you...`,
        type: 'assistant' as const,        // AI response type
        timestamp: new Date()             // Response timestamp
      }
      chatMessages = [...chatMessages, assistantMessage]  // Add AI response to chat
      isLoading = false                                   // Clear loading state
    }, 1500)
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
          Left Sidebar - Sources List
          - 1/4 width with yellow background for visual distinction
          - Shows all available source materials for the topic
          - Scrollable if many sources are available
        -->
        <div class="w-1/4 border-r-4 border-black p-4 overflow-y-auto bg-brand-yellow">
          <h3 class="text-lg font-bold mb-4 font-mono text-black">
            Sources
          </h3>
          
          <!-- Conditional rendering based on sources availability -->
          {#if sources.length === 0}
            <!-- Empty state when no sources are available -->
            <p class="text-sm text-gray-600">No sources available</p>
          {:else}
            <!-- List of available sources -->
            <div class="flex flex-col gap-2">
              {#each sources as source}
                <!-- 
                  Individual source card
                  - White background with hover effects
                  - Shows title and type with color transitions
                  - Interactive hover state with blue background
                -->
                <div class="p-3 border-2 border-black bg-white cursor-pointer transition-all duration-300 hover:bg-brand-blue group">
                  <!-- Source title with hover color change -->
                  <div class="font-bold text-sm font-mono text-black group-hover:text-white transition-colors duration-300">
                    {source.title}
                  </div>
                  <!-- Source type indicator -->
                  <div class="text-xs text-gray-600 uppercase group-hover:text-white transition-colors duration-300">
                    {source.type}
                  </div>
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
                      <!-- Sender identification -->
                      <div class="font-bold text-xs mb-1 uppercase font-mono">
                        {message.type === 'user' ? 'You' : 'Study4Me AI'}
                      </div>
                      <!-- Message content -->
                      <div class="text-sm leading-6">
                        {message.content}
                      </div>
                      <!-- Timestamp -->
                      <div class="text-xs text-gray-600 mt-2">
                        {message.timestamp.toLocaleTimeString()}
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
          -->
          <div class="p-4 border-t-4 border-black bg-white">
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
            <!-- TODO: Implement mindmap generation functionality -->
            <button class="w-full h-12 p-3 border-2 border-black bg-brand-pink text-white cursor-pointer font-mono font-bold text-sm flex items-center justify-center gap-2 hover:bg-opacity-90">
              <!-- Network/mindmap icon -->
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
              Create Mindmap
            </button>
            
            <!-- Summarize Content Button -->
            <!-- TODO: Implement content summarization functionality -->
            <button class="w-full h-12 p-3 border-2 border-black bg-brand-pink text-white cursor-pointer font-mono font-bold text-sm flex items-center justify-center gap-2 hover:bg-opacity-90">
              <!-- Document/summary icon -->
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 3h18v18H3V3zm2 2v14h14V5H5zm2 2h10v2H7V7zm0 4h10v2H7v-2zm0 4h7v2H7v-2z"/>
              </svg>
              Summarize Content
            </button>
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
</style>