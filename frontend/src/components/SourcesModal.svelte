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
    style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; padding: 1rem; z-index: 1000;"
    on:click={handleOutsideClick}
    on:keydown={(e) => e.key === 'Escape' && handleClose()}
    role="dialog"
    aria-modal="true"
    aria-labelledby="sources-modal-title"
  >
    <!-- Modal Container -->
    <div 
      style="background-color: white; border: 4px solid black; width: 100%; max-width: 56rem; height: 80vh; display: flex; flex-direction: column;"
    >
      <!-- Modal Header -->
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; border-bottom: 4px solid black; background-color: white;">
        <div>
          <h2 id="sources-modal-title" style="font-size: 1.25rem; font-weight: bold; font-family: 'IBM Plex Mono', monospace; color: black; margin-bottom: 0.25rem;">
            Add sources: {topicTitle}
          </h2>
          <p style="font-size: 0.875rem; color: #666;">Upload files, scrape websites, or add YouTube videos to enhance your topic</p>
        </div>
        <button 
          style="background-color: #EC4899; color: white; border: 2px solid black; border-radius: 4px; padding: 0.5rem 0.75rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 1.125rem;"
          on:click={handleClose}
          aria-label="Close modal"
        >
          ×
        </button>
      </div>
      
      <!-- Modal Body -->
      <div style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
        <!-- Tab Navigation -->
        <div style="display: flex; border-bottom: 4px solid black; background-color: #FFF200;">
          <button 
            style="flex: 1; padding: 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; font-size: 0.875rem; border: none; border-right: 2px solid black; cursor: pointer; background-color: {activeTab === 'upload' ? 'white' : 'transparent'}; color: black;"
            on:click={() => setActiveTab('upload')}
          >
            📁 Upload Files
          </button>
          <button 
            style="flex: 1; padding: 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; font-size: 0.875rem; border: none; border-right: 2px solid black; cursor: pointer; background-color: {activeTab === 'website' ? 'white' : 'transparent'}; color: black;"
            on:click={() => setActiveTab('website')}
          >
            🌐 Website
          </button>
          <button 
            style="flex: 1; padding: 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; font-size: 0.875rem; border: none; cursor: pointer; background-color: {activeTab === 'youtube' ? 'white' : 'transparent'}; color: black;"
            on:click={() => setActiveTab('youtube')}
          >
            📺 YouTube
          </button>
        </div>
        
        <!-- Tab Content -->
        <div style="flex: 1; padding: 2rem; overflow-y: auto; background-color: #f9f9f9;">
          {#if activeTab === 'upload'}
            <!-- Upload Tab -->
            <div style="height: 100%; display: flex; flex-direction: column; gap: 1.5rem;">
              <!-- Drag & Drop Area -->
              <div 
                style="border: 3px dashed black; background-color: {isDragging ? '#FFF200' : 'white'}; padding: 3rem; text-align: center; cursor: pointer; transition: background-color 0.3s ease;"
                on:dragover={handleDragOver}
                on:dragleave={handleDragLeave}
                on:drop={handleDrop}
                on:click={() => document.getElementById('file-input')?.click()}
              >
                <div style="font-size: 3rem; margin-bottom: 1rem;">📤</div>
                <h3 style="font-size: 1.125rem; font-weight: bold; font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.5rem;">
                  Upload sources
                </h3>
                <p style="color: #666; margin-bottom: 1rem;">
                  Drag & drop or <span style="color: #0050FF; text-decoration: underline; cursor: pointer;">choose file</span> to upload
                </p>
                <p style="font-size: 0.875rem; color: #999;">
                  Supported file types: PDF, .txt, Markdown, Audio (e.g. mp3)
                </p>
              </div>
              
              <input 
                id="file-input"
                type="file"
                multiple
                accept=".pdf,.txt,.md,.mp3,.wav,.m4a"
                style="display: none;"
                on:change={handleFileSelect}
              />
              
              <!-- Uploaded Files List -->
              {#if uploadedFiles.length > 0}
                <div style="border: 2px solid black; background-color: white; padding: 1rem;">
                  <h4 style="font-weight: bold; font-family: 'IBM Plex Mono', monospace; margin-bottom: 1rem;">
                    Uploaded Files ({uploadedFiles.length})
                  </h4>
                  <div style="display: flex; flex-direction: column; gap: 0.5rem; max-height: 200px; overflow-y: auto;">
                    {#each uploadedFiles as file, index}
                      <div style="display: flex; justify-content: between; align-items: center; padding: 0.75rem; border: 1px solid black; background-color: #f9f9f9;">
                        <div style="flex: 1;">
                          <div style="font-weight: bold; font-size: 0.875rem;">{file.name}</div>
                          <div style="font-size: 0.75rem; color: #666;">{formatFileSize(file.size)} • {file.type}</div>
                        </div>
                        <button 
                          style="background-color: #FF2C2C; color: white; border: 1px solid black; border-radius: 2px; padding: 0.25rem 0.5rem; cursor: pointer; font-size: 0.75rem;"
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
            <div style="height: 100%; display: flex; flex-direction: column; gap: 1rem;">
              <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌐</div>
                <h3 style="font-size: 1rem; font-weight: bold; font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.25rem;">
                  Scrape Website
                </h3>
                <p style="color: #666; font-size: 0.875rem;">
                  Enter a website URL to extract and analyze its content
                </p>
              </div>
              
              <div style="background-color: white; border: 2px solid black; padding: 1rem;">
                <label style="display: block; font-weight: bold; font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.5rem; font-size: 0.875rem;">
                  Website URL
                </label>
                <div style="display: flex; gap: 0.5rem;">
                  <input 
                    type="url"
                    bind:value={websiteUrl}
                    placeholder="https://example.com"
                    style="flex: 1; padding: 0.5rem; border: 2px solid black; font-family: Inter, sans-serif; font-size: 0.875rem;"
                  />
                  <button 
                    style="background-color: #EC4899; color: white; border: 2px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;"
                    on:click={handleWebsiteSubmit}
                  >
                    Scrape
                  </button>
                </div>
              </div>
              
              <div style="background-color: white; border: 2px solid black; padding: 1rem;">
                <h4 style="font-weight: bold; font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.75rem; font-size: 0.875rem;">
                  Quick Actions
                </h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.5rem;">
                  <button style="padding: 0.75rem; border: 2px solid black; background-color: #f9f9f9; text-align: left; cursor: pointer; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;">
                    📄 Article/Blog
                  </button>
                  <button style="padding: 0.75rem; border: 2px solid black; background-color: #f9f9f9; text-align: left; cursor: pointer; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;">
                    📚 Documentation
                  </button>
                  <button style="padding: 0.75rem; border: 2px solid black; background-color: #f9f9f9; text-align: left; cursor: pointer; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;">
                    📰 News Article
                  </button>
                  <button style="padding: 0.75rem; border: 2px solid black; background-color: #f9f9f9; text-align: left; cursor: pointer; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;">
                    🏢 Company Page
                  </button>
                </div>
              </div>
            </div>
            
          {:else if activeTab === 'youtube'}
            <!-- YouTube Tab -->
            <div style="height: 100%; display: flex; flex-direction: column; gap: 1rem;">
              <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📺</div>
                <h3 style="font-size: 1rem; font-weight: bold; font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.25rem;">
                  YouTube Video
                </h3>
                <p style="color: #666; font-size: 0.875rem;">
                  Add YouTube videos to extract transcripts and analyze content
                </p>
              </div>
              
              <div style="background-color: white; border: 2px solid black; padding: 1rem;">
                <label style="display: block; font-weight: bold; font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.5rem; font-size: 0.875rem;">
                  YouTube URL
                </label>
                <div style="display: flex; gap: 0.5rem;">
                  <input 
                    type="url"
                    bind:value={youtubeUrl}
                    placeholder="https://youtube.com/watch?v=..."
                    style="flex: 1; padding: 0.5rem; border: 2px solid black; font-family: Inter, sans-serif; font-size: 0.875rem;"
                  />
                  <button 
                    style="background-color: #EC4899; color: white; border: 2px solid black; border-radius: 4px; padding: 0.5rem 1rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer; font-size: 0.875rem;"
                    on:click={handleYouTubeSubmit}
                  >
                    Add Video
                  </button>
                </div>
              </div>
              
              <div style="background-color: white; border: 2px solid black; padding: 1rem;">
                <h4 style="font-weight: bold; font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.75rem; font-size: 0.875rem;">
                  Features
                </h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                  <div style="display: flex; align-items: center; gap: 0.25rem;">
                    <span style="color: #10B981; font-size: 0.75rem;">✓</span>
                    <span style="font-size: 0.75rem;">Transcript extraction</span>
                  </div>
                  <div style="display: flex; align-items: center; gap: 0.25rem;">
                    <span style="color: #10B981; font-size: 0.75rem;">✓</span>
                    <span style="font-size: 0.75rem;">Metadata analysis</span>
                  </div>
                  <div style="display: flex; align-items: center; gap: 0.25rem;">
                    <span style="color: #10B981; font-size: 0.75rem;">✓</span>
                    <span style="font-size: 0.75rem;">Chapter detection</span>
                  </div>
                  <div style="display: flex; align-items: center; gap: 0.25rem;">
                    <span style="color: #10B981; font-size: 0.75rem;">✓</span>
                    <span style="font-size: 0.75rem;">Multi-language</span>
                  </div>
                </div>
              </div>
            </div>
          {/if}
        </div>
        
        <!-- Modal Footer -->
        <div style="padding: 1rem; border-top: 4px solid black; background-color: white; display: flex; justify-content: space-between; align-items: center;">
          <div style="font-size: 0.875rem; color: #666;">
            Source limit: 79 / 300
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <button 
              style="background-color: #f9f9f9; color: black; border: 2px solid black; border-radius: 4px; padding: 0.75rem 1.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer;"
              on:click={handleClose}
            >
              Cancel
            </button>
            <button 
              style="background-color: #0050FF; color: white; border: 2px solid black; border-radius: 4px; padding: 0.75rem 1.5rem; font-family: 'IBM Plex Mono', monospace; font-weight: bold; cursor: pointer;"
            >
              Save Sources
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}