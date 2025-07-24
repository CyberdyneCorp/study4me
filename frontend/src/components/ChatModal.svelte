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
    style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; padding: 1rem; z-index: 1000;"
    on:click={handleOutsideClick}
    on:keydown={(e) => e.key === 'Escape' && handleClose()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
  >
    <!-- Modal Container -->
    <div 
      style="background-color: white; border: 4px solid black; width: 100%; max-width: 72rem; height: 80vh; display: flex; flex-direction: column;"
    >
      <!-- Modal Header -->
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; border-bottom: 4px solid black; background-color: white;">
        <div>
          <h2 id="modal-title" style="font-size: 1.25rem; font-weight: bold; font-family: 'IBM Plex Mono', monospace; color: black; margin-bottom: 0.25rem;">
            Study: {topicTitle}
          </h2>
          <p style="font-size: 0.875rem; color: #666;">Ask questions about your topic sources</p>
        </div>
        <button 
          style="background-color: #EC4899; color: white; border: 2px solid black; border-radius: 4px; padding: 0.5rem 0.75rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 1.125rem;"
          on:click={handleClose}
          aria-label="Close modal"
        >
          ×
        </button>
      </div>
      
      <!-- Modal Body - Chat Interface -->
      <div style="display: flex; flex: 1; overflow: hidden;">
        <!-- Left Sidebar - Sources List -->
        <div style="width: 25%; border-right: 4px solid black; padding: 1rem; overflow-y: auto; background-color: #FFF200;">
          <h3 style="font-size: 1.125rem; font-weight: bold; margin-bottom: 1rem; font-family: 'IBM Plex Mono', monospace; color: black;">
            Sources
          </h3>
          {#if sources.length === 0}
            <p style="font-size: 0.875rem; color: #666;">No sources available</p>
          {:else}
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
              {#each sources as source}
                <div 
                  style="padding: 0.75rem; border: 2px solid black; background-color: white; cursor: pointer; transition: all 0.3s ease;"
                  on:mouseenter={(e) => {
                    e.target.style.backgroundColor = '#0050FF';
                    const title = e.target.querySelector('.source-title');
                    const type = e.target.querySelector('.source-type');
                    if (title) title.style.color = 'white';
                    if (type) type.style.color = 'white';
                  }}
                  on:mouseleave={(e) => {
                    e.target.style.backgroundColor = 'white';
                    const title = e.target.querySelector('.source-title');
                    const type = e.target.querySelector('.source-type');
                    if (title) title.style.color = 'black';
                    if (type) type.style.color = '#666';
                  }}
                >
                  <div class="source-title" style="font-weight: bold; font-size: 0.875rem; font-family: 'IBM Plex Mono', monospace; color: black; transition: color 0.3s ease;">
                    {source.title}
                  </div>
                  <div class="source-type" style="font-size: 0.75rem; color: #666; text-transform: uppercase; transition: color 0.3s ease;">
                    {source.type}
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
        
        <!-- Center - Chat Messages -->
        <div style="flex: 1; display: flex; flex-direction: column;">
          <!-- Messages Container -->
          <div style="flex: 1; padding: 1rem; overflow-y: auto; background-color: #f9f9f9;">
            {#if chatMessages.length === 0}
              <div style="text-align: center; color: #666; margin-top: 2rem;">
                <p style="font-size: 1.125rem; font-weight: bold; margin-bottom: 0.5rem; font-family: 'IBM Plex Mono', monospace;">
                  Start a conversation
                </p>
                <p style="font-size: 0.875rem;">Ask questions about your topic to get insights from your sources.</p>
              </div>
            {:else}
              <div style="display: flex; flex-direction: column; gap: 1rem;">
                {#each chatMessages as message}
                  <div style="display: flex; {message.type === 'user' ? 'justify-content: flex-end;' : 'justify-content: flex-start;'}">
                    <div 
                      style="max-width: 70%; padding: 0.75rem; border: 2px solid black; background-color: {message.type === 'user' ? '#DBEAFE' : 'white'};"
                    >
                      <div style="font-weight: bold; font-size: 0.75rem; margin-bottom: 0.25rem; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace;">
                        {message.type === 'user' ? 'You' : 'Study4Me AI'}
                      </div>
                      <div style="font-size: 0.875rem; line-height: 1.5;">
                        {message.content}
                      </div>
                      <div style="font-size: 0.75rem; color: #666; margin-top: 0.5rem;">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                {/each}
                
                {#if isLoading}
                  <div style="display: flex; justify-content: flex-start;">
                    <div style="max-width: 70%; padding: 0.75rem; border: 2px solid black; background-color: white;">
                      <div style="font-weight: bold; font-size: 0.75rem; margin-bottom: 0.25rem; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace;">
                        Study4Me AI
                      </div>
                      <div style="font-size: 0.875rem;">
                        <span>Thinking...</span>
                      </div>
                    </div>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
          
          <!-- Message Input -->
          <div style="padding: 1rem; border-top: 4px solid black; background-color: white;">
            <div style="display: flex; gap: 0.5rem;">
              <textarea
                bind:value={currentMessage}
                on:keydown={handleKeyPress}
                placeholder="Ask a question about your topic..."
                style="flex: 1; padding: 0.75rem; border: 2px solid black; resize: none; font-family: Inter, sans-serif; min-height: 60px; max-height: 120px;"
                rows="2"
                disabled={isLoading}
              ></textarea>
              <button 
                style="background-color: #0050FF; color: white; border: 4px solid black; border-radius: 4px; padding: 0.75rem 1.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; {!currentMessage.trim() || isLoading ? 'opacity: 0.5; cursor: not-allowed;' : ''}"
                on:click={handleSendMessage}
                disabled={!currentMessage.trim() || isLoading}
              >
                Send
              </button>
            </div>
            <div style="font-size: 0.75rem; color: #666; margin-top: 0.5rem;">
              Press Enter to send, Shift+Enter for new line
            </div>
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