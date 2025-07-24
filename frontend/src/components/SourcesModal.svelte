<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  
  export let isOpen = false
  export let topicTitle = ''
  
  const dispatch = createEventDispatcher()
  
  let activeTab = 'upload'
  let websiteUrl = ''
  let youtubeUrl = ''
  let isDragging = false
  let uploadedFiles: Array<{name: string, size: number, type: string}> = []
  
  function handleClose() {
    dispatch('close')
  }
  
  function handleOutsideClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose()
    }
  }
  
  function setActiveTab(tab: string) {
    activeTab = tab
  }
  
  function handleDragOver(event: DragEvent) {
    event.preventDefault()
    isDragging = true
  }
  
  function handleDragLeave(event: DragEvent) {
    event.preventDefault()
    isDragging = false
  }
  
  function handleDrop(event: DragEvent) {
    event.preventDefault()
    isDragging = false
    const files = Array.from(event.dataTransfer?.files || [])
    processFiles(files)
  }
  
  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement
    const files = Array.from(target.files || [])
    processFiles(files)
  }
  
  function processFiles(files: File[]) {
    const newFiles = files.map(file => ({
      name: file.name,
      size: file.size,
      type: file.type || 'Unknown'
    }))
    uploadedFiles = [...uploadedFiles, ...newFiles]
  }
  
  function removeFile(index: number) {
    uploadedFiles = uploadedFiles.filter((_, i) => i !== index)
  }
  
  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  function handleWebsiteSubmit() {
    if (websiteUrl.trim()) {
      console.log('Scraping website:', websiteUrl)
      websiteUrl = ''
    }
  }
  
  function handleYouTubeSubmit() {
    if (youtubeUrl.trim()) {
      console.log('Processing YouTube video:', youtubeUrl)
      youtubeUrl = ''
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
    aria-labelledby="sources-modal-title"
    tabindex="-1"
  >
    <!-- Modal Container -->
    <div 
      class="bg-white border-4 border-black w-full max-w-4xl h-4/5 flex flex-col"
    >
      <!-- Modal Header -->
      <div class="flex justify-between items-center p-4 border-b-4 border-black bg-white">
        <div>
          <h2 id="sources-modal-title" class="text-xl font-bold font-mono text-black mb-1">
            Add sources: {topicTitle}
          </h2>
          <p class="text-sm text-gray-600">Upload files, scrape websites, or add YouTube videos to enhance your topic</p>
        </div>
        <button 
          class="bg-brand-pink text-white border-2 border-black rounded px-3 py-2 font-mono font-bold cursor-pointer text-lg hover:bg-opacity-90"
          on:click={handleClose}
          aria-label="Close modal"
        >
          ×
        </button>
      </div>
      
      <!-- Modal Body -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Tab Navigation -->
        <div class="flex border-b-4 border-black bg-brand-yellow">
          <button 
            class="flex-1 p-4 font-mono font-bold text-sm border-none border-r-2 border-black cursor-pointer text-black {activeTab === 'upload' ? 'bg-white' : 'bg-transparent'}"
            on:click={() => setActiveTab('upload')}
          >
            📁 Upload Files
          </button>
          <button 
            class="flex-1 p-4 font-mono font-bold text-sm border-none border-r-2 border-black cursor-pointer text-black {activeTab === 'website' ? 'bg-white' : 'bg-transparent'}"
            on:click={() => setActiveTab('website')}
          >
            🌐 Website
          </button>
          <button 
            class="flex-1 p-4 font-mono font-bold text-sm border-none cursor-pointer text-black {activeTab === 'youtube' ? 'bg-white' : 'bg-transparent'}"
            on:click={() => setActiveTab('youtube')}
          >
            📺 YouTube
          </button>
        </div>
        
        <!-- Tab Content -->
        <div class="flex-1 p-8 overflow-y-auto bg-gray-50">
          {#if activeTab === 'upload'}
            <!-- Upload Tab -->
            <div class="h-full flex flex-col gap-6">
              <!-- Drag & Drop Area -->
              <div 
                class="border-4 border-dashed border-black p-12 text-center cursor-pointer transition-colors duration-300 {isDragging ? 'bg-brand-yellow' : 'bg-white'}"
                on:dragover={handleDragOver}
                on:dragleave={handleDragLeave}
                on:drop={handleDrop}
                on:click={() => document.getElementById('file-input')?.click()}
                on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && document.getElementById('file-input')?.click()}
                role="button"
                tabindex="0"
                aria-label="Upload files by clicking or dragging and dropping"
              >
                <div class="text-5xl mb-4">📤</div>
                <h3 class="text-lg font-bold font-mono mb-2">
                  Upload sources
                </h3>
                <p class="text-gray-600 mb-4">
                  Drag & drop or <span class="text-brand-blue underline cursor-pointer">choose file</span> to upload
                </p>
                <p class="text-sm text-gray-500">
                  Supported file types: PDF, .txt, Markdown, Audio (e.g. mp3)
                </p>
              </div>
              
              <input 
                id="file-input"
                type="file"
                multiple
                accept=".pdf,.txt,.md,.mp3,.wav,.m4a"
                class="hidden"
                on:change={handleFileSelect}
              />
              
              <!-- Uploaded Files List -->
              {#if uploadedFiles.length > 0}
                <div class="border-2 border-black bg-white p-4">
                  <h4 class="font-bold font-mono mb-4">
                    Uploaded Files ({uploadedFiles.length})
                  </h4>
                  <div class="flex flex-col gap-2 max-h-48 overflow-y-auto">
                    {#each uploadedFiles as file, index}
                      <div class="flex justify-between items-center p-3 border border-black bg-gray-50">
                        <div class="flex-1">
                          <div class="font-bold text-sm">{file.name}</div>
                          <div class="text-xs text-gray-600">{formatFileSize(file.size)} • {file.type}</div>
                        </div>
                        <button 
                          class="bg-brand-red text-white border border-black rounded px-2 py-1 cursor-pointer text-xs hover:bg-opacity-90"
                          on:click={() => removeFile(index)}
                        >
                          Remove
                        </button>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
            
          {:else if activeTab === 'website'}
            <!-- Website Tab -->
            <div class="h-full flex flex-col gap-4">
              <div class="text-center mb-4">
                <div class="text-3xl mb-2">🌐</div>
                <h3 class="text-base font-bold font-mono mb-1">
                  Scrape Website
                </h3>
                <p class="text-gray-600 text-sm">
                  Enter a website URL to extract and analyze its content
                </p>
              </div>
              
              <div class="bg-white border-2 border-black p-4">
                <label for="website-url-input" class="block font-bold font-mono mb-2 text-sm">
                  Website URL
                </label>
                <div class="flex gap-2">
                  <input 
                    id="website-url-input"
                    type="url"
                    bind:value={websiteUrl}
                    placeholder="https://example.com"
                    class="flex-1 p-2 border-2 border-black font-inter text-sm"
                  />
                  <button 
                    class="bg-brand-pink text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer text-sm hover:bg-opacity-90"
                    on:click={handleWebsiteSubmit}
                  >
                    Scrape
                  </button>
                </div>
              </div>
              
              <div class="bg-white border-2 border-black p-4">
                <h4 class="font-bold font-mono mb-3 text-sm">
                  Quick Actions
                </h4>
                <div class="grid grid-cols-2 gap-2">
                  <button class="p-3 border-2 border-black bg-gray-50 text-left cursor-pointer font-mono text-xs hover:bg-brand-yellow">
                    📄 Article/Blog
                  </button>
                  <button class="p-3 border-2 border-black bg-gray-50 text-left cursor-pointer font-mono text-xs hover:bg-brand-yellow">
                    📚 Documentation
                  </button>
                  <button class="p-3 border-2 border-black bg-gray-50 text-left cursor-pointer font-mono text-xs hover:bg-brand-yellow">
                    📰 News Article
                  </button>
                  <button class="p-3 border-2 border-black bg-gray-50 text-left cursor-pointer font-mono text-xs hover:bg-brand-yellow">
                    🏢 Company Page
                  </button>
                </div>
              </div>
            </div>
            
          {:else if activeTab === 'youtube'}
            <!-- YouTube Tab -->
            <div class="h-full flex flex-col gap-4">
              <div class="text-center mb-4">
                <div class="text-3xl mb-2">📺</div>
                <h3 class="text-base font-bold font-mono mb-1">
                  YouTube Video
                </h3>
                <p class="text-gray-600 text-sm">
                  Add YouTube videos to extract transcripts and analyze content
                </p>
              </div>
              
              <div class="bg-white border-2 border-black p-4">
                <label for="youtube-url-input" class="block font-bold font-mono mb-2 text-sm">
                  YouTube URL
                </label>
                <div class="flex gap-2">
                  <input 
                    id="youtube-url-input"
                    type="url"
                    bind:value={youtubeUrl}
                    placeholder="https://youtube.com/watch?v=..."
                    class="flex-1 p-2 border-2 border-black font-inter text-sm"
                  />
                  <button 
                    class="bg-brand-pink text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer text-sm hover:bg-opacity-90"
                    on:click={handleYouTubeSubmit}
                  >
                    Add Video
                  </button>
                </div>
              </div>
              
              <div class="bg-white border-2 border-black p-4">
                <h4 class="font-bold font-mono mb-3 text-sm">
                  Features
                </h4>
                <div class="grid grid-cols-2 gap-2">
                  <div class="flex items-center gap-1">
                    <span class="text-green-500 text-xs">✓</span>
                    <span class="text-xs">Transcript extraction</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <span class="text-green-500 text-xs">✓</span>
                    <span class="text-xs">Metadata analysis</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <span class="text-green-500 text-xs">✓</span>
                    <span class="text-xs">Chapter detection</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <span class="text-green-500 text-xs">✓</span>
                    <span class="text-xs">Multi-language</span>
                  </div>
                </div>
              </div>
            </div>
          {/if}
        </div>
        
        <!-- Modal Footer -->
        <div class="p-4 border-t-4 border-black bg-white flex justify-between items-center">
          <div class="text-sm text-gray-600">
            Source limit: 79 / 300
          </div>
          <div class="flex gap-2">
            <button 
              class="bg-gray-50 text-black border-2 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer hover:bg-gray-100"
              on:click={handleClose}
            >
              Cancel
            </button>
            <button 
              class="bg-brand-blue text-white border-2 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer hover:bg-opacity-90"
            >
              Save Sources
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}