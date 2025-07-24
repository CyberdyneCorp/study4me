<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  import Button from './Button.svelte'
  
  export let isOpen = false
  export let topicTitle = ''
  export let sources: Array<{id: string, title: string, type: string}> = []
  
  const dispatch = createEventDispatcher()
  
  let chatMessages: Array<{id: string, content: string, type: 'user' | 'assistant', timestamp: Date}> = []
  let currentMessage = ''
  let isLoading = false
  
  function handleClose() {
    dispatch('close')
  }
  
  function handleOutsideClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose()
    }
  }
  
  async function handleSendMessage() {
    if (!currentMessage.trim() || isLoading) return
    
    const userMessage = {
      id: Date.now().toString(),
      content: currentMessage.trim(),
      type: 'user' as const,
      timestamp: new Date()
    }
    
    chatMessages = [...chatMessages, userMessage]
    const messageToSend = currentMessage
    currentMessage = ''
    isLoading = true
    
    // Simulate API call for now
    setTimeout(() => {
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        content: `I understand you're asking about "${messageToSend}". Based on the sources in this topic, here's what I can tell you...`,
        type: 'assistant' as const,
        timestamp: new Date()
      }
      chatMessages = [...chatMessages, assistantMessage]
      isLoading = false
    }, 1500)
  }
  
  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }
</script>

{#if isOpen}
  <!-- Modal Backdrop -->
  <div 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    on:click={handleOutsideClick}
    on:keydown={(e) => e.key === 'Escape' && handleClose()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
  >
    <!-- Modal Container -->
    <div 
      class="bg-white border-4 border-black w-full max-w-6xl h-4/5 flex flex-col"
    >
      <!-- Modal Header -->
      <div class="flex justify-between items-center p-4 border-b-4 border-black bg-white">
        <div>
          <h2 id="modal-title" class="text-xl font-bold font-mono text-black mb-1">
            Study: {topicTitle}
          </h2>
          <p class="text-sm text-gray-600">Ask questions about your topic sources</p>
        </div>
        <button 
          class="bg-brand-pink text-white border-2 border-black rounded px-3 py-2 font-mono font-bold cursor-pointer text-lg hover:bg-opacity-90"
          on:click={handleClose}
          aria-label="Close modal"
        >
          ×
        </button>
      </div>
      
      <!-- Modal Body - Chat Interface -->
      <div class="flex flex-1 overflow-hidden">
        <!-- Left Sidebar - Sources List -->
        <div class="w-1/4 border-r-4 border-black p-4 overflow-y-auto bg-brand-yellow">
          <h3 class="text-lg font-bold mb-4 font-mono text-black">
            Sources
          </h3>
          {#if sources.length === 0}
            <p class="text-sm text-gray-600">No sources available</p>
          {:else}
            <div class="flex flex-col gap-2">
              {#each sources as source}
                <div class="p-3 border-2 border-black bg-white cursor-pointer transition-all duration-300 hover:bg-brand-blue group">
                  <div class="font-bold text-sm font-mono text-black group-hover:text-white transition-colors duration-300">
                    {source.title}
                  </div>
                  <div class="text-xs text-gray-600 uppercase group-hover:text-white transition-colors duration-300">
                    {source.type}
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
        
        <!-- Center - Chat Messages -->
        <div class="flex-1 flex flex-col">
          <!-- Messages Container -->
          <div class="flex-1 p-4 overflow-y-auto bg-gray-50">
            {#if chatMessages.length === 0}
              <div class="text-center text-gray-600 mt-8">
                <p class="text-lg font-bold mb-2 font-mono">
                  Start a conversation
                </p>
                <p class="text-sm">Ask questions about your topic to get insights from your sources.</p>
              </div>
            {:else}
              <div class="flex flex-col gap-4">
                {#each chatMessages as message}
                  <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'}">
                    <div class="max-w-sm lg:max-w-md xl:max-w-lg p-3 border-2 border-black {message.type === 'user' ? 'bg-blue-100' : 'bg-white'}">
                      <div class="font-bold text-xs mb-1 uppercase font-mono">
                        {message.type === 'user' ? 'You' : 'Study4Me AI'}
                      </div>
                      <div class="text-sm leading-6">
                        {message.content}
                      </div>
                      <div class="text-xs text-gray-600 mt-2">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                {/each}
                
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
          
          <!-- Message Input -->
          <div class="p-4 border-t-4 border-black bg-white">
            <div class="flex gap-2">
              <textarea
                bind:value={currentMessage}
                on:keydown={handleKeyPress}
                placeholder="Ask a question about your topic..."
                class="flex-1 p-3 border-2 border-black resize-none font-inter min-h-15 max-h-30"
                rows="2"
                disabled={isLoading}
              ></textarea>
              <button 
                class="bg-brand-blue text-white border-4 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer {!currentMessage.trim() || isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-opacity-90'}"
                on:click={handleSendMessage}
                disabled={!currentMessage.trim() || isLoading}
              >
                Send
              </button>
            </div>
            <div class="text-xs text-gray-600 mt-2">
              Press Enter to send, Shift+Enter for new line
            </div>
          </div>
        </div>
        
        <!-- Right Sidebar - Session Actions -->
        <div class="w-1/5 border-l-4 border-black p-4 bg-brand-yellow">
          <h3 class="text-lg font-bold mb-4 font-mono text-black">
            Session
          </h3>
          
          <div class="flex flex-col gap-3">
            <button class="w-full h-12 p-3 border-2 border-black bg-brand-pink text-white cursor-pointer font-mono font-bold text-sm flex items-center justify-center gap-2 hover:bg-opacity-90">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
              </svg>
              Create Podcast
            </button>
            
            <button class="w-full h-12 p-3 border-2 border-black bg-brand-pink text-white cursor-pointer font-mono font-bold text-sm flex items-center justify-center gap-2 hover:bg-opacity-90">
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
            
            <button class="w-full h-12 p-3 border-2 border-black bg-brand-pink text-white cursor-pointer font-mono font-bold text-sm flex items-center justify-center gap-2 hover:bg-opacity-90">
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