<!--
  SourcesModal.svelte - Modal for managing topic source materials
  
  This modal provides a comprehensive interface for users to add various types
  of source materials to their study topics:
  - File uploads (PDF, text, markdown, audio)
  - Website scraping for articles and documentation
  - YouTube video processing for transcripts
  
  Features:
  - Tabbed interface for different source types
  - Drag-and-drop file upload
  - Real-time file management with removal capabilities
  - URL validation and processing
  - Source limit tracking
  - Accessible design with proper ARIA attributes
-->

<script lang="ts">
  import { createEventDispatcher, onDestroy } from 'svelte'
  import { apiService } from '../services/api'
  import { webSocketService } from '../services/websocket'
  import type { 
    UploadDocumentsResponse, 
    ProcessWebpageResponse, 
    ProcessYouTubeResponse,
    TaskStatusResponse 
  } from '../services/api'
  import type { TaskUpdate } from '../services/websocket'
  
  // Props passed from parent component
  export let isOpen = false          // Controls modal visibility
  export let topicTitle = ''         // Title of the topic being managed
  export let studyTopicId = ''       // UUID of the study topic for backend operations
  
  // Event dispatcher for parent communication
  const dispatch = createEventDispatcher()
  
  // Tab management state
  let activeTab = 'upload'           // Current active tab ('upload', 'website', 'youtube')
  
  // Form input states
  let websiteUrl = ''                // Website URL input value
  let youtubeUrl = ''                // YouTube URL input value
  
  // Drag and drop state
  let isDragging = false             // Flag for drag-over visual feedback
  
  // File management state
  let selectedFiles: File[] = []     // Actual File objects for upload
  let uploadedFiles: Array<{name: string, size: number, type: string}> = []  // Display list of files
  
  // Processing state management
  interface ProcessingTask {
    id: string
    type: 'upload' | 'webpage' | 'youtube'
    name: string
    status: 'pending' | 'processing' | 'done' | 'failed'
    progress?: number
    message?: string
    error?: string
    createdAt: Date
  }
  
  let processingTasks: ProcessingTask[] = []
  let isProcessing = false
  let processingError = ''
  
  // WebSocket subscriptions tracking
  let wsUnsubscribeFunctions: (() => void)[] = []
  
  // Cleanup WebSocket subscriptions on component destroy
  onDestroy(() => {
    wsUnsubscribeFunctions.forEach(unsubscribe => unsubscribe())
  })

  /**
   * Closes the sources modal and notifies parent component
   * Resets any temporary state when modal closes
   */
  function handleClose() {
    // Clean up WebSocket subscriptions
    wsUnsubscribeFunctions.forEach(unsubscribe => unsubscribe())
    wsUnsubscribeFunctions = []
    
    // Reset state
    resetModalState()
    
    dispatch('close')
  }

  /**
   * Reset all modal state to initial values
   */
  function resetModalState() {
    activeTab = 'upload'
    websiteUrl = ''
    youtubeUrl = ''
    isDragging = false
    selectedFiles = []
    uploadedFiles = []
    processingTasks = []
    isProcessing = false
    processingError = ''
  }

  /**
   * Create a new processing task and subscribe to WebSocket updates or start polling
   */
  function createProcessingTask(
    taskId: string, 
    type: 'upload' | 'webpage' | 'youtube', 
    name: string
  ): ProcessingTask {
    const task: ProcessingTask = {
      id: taskId,
      type,
      name,
      status: 'processing', // Start as processing since we just initiated it
      createdAt: new Date()
    }
    
    processingTasks = [...processingTasks, task]
    
    // Try WebSocket first, fall back to polling if WebSocket is not available
    if (webSocketService.isConnected) {
      // Subscribe to WebSocket updates for this task
      const unsubscribe = webSocketService.subscribeToTask(taskId, (update: TaskUpdate) => {
        updateProcessingTask(taskId, update)
      })
      wsUnsubscribeFunctions.push(unsubscribe)
    } else {
      // Fall back to polling the task status
      startTaskPolling(taskId)
    }
    
    return task
  }

  /**
   * Poll task status when WebSocket is not available
   */
  async function startTaskPolling(taskId: string) {
    const maxAttempts = 60 // Poll for up to 5 minutes (60 * 5s = 300s)
    let attempts = 0
    
    const poll = async () => {
      try {
        const status = await apiService.getTaskStatus(taskId)
        
        updateProcessingTask(taskId, {
          task_id: taskId,
          status: status.status,
          result: status.result
        })
        
        // Continue polling if still processing and haven't exceeded max attempts
        if (status.status === 'processing' && attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 5000) // Poll every 5 seconds
        }
      } catch (error) {
        console.error('Failed to poll task status:', error)
        // Stop polling on error
        updateProcessingTask(taskId, {
          task_id: taskId,
          status: 'failed',
          error: 'Failed to get task status'
        })
      }
    }
    
    // Start polling after a short delay
    setTimeout(poll, 2000)
  }

  /**
   * Update a processing task based on WebSocket update
   */
  function updateProcessingTask(taskId: string, update: TaskUpdate) {
    processingTasks = processingTasks.map(task => {
      if (task.id === taskId) {
        return {
          ...task,
          status: update.status,
          progress: update.progress,
          message: update.message,
          error: update.error
        }
      }
      return task
    })
    
    // Update global processing state
    const hasProcessingTasks = processingTasks.some(task => task.status === 'processing')
    isProcessing = hasProcessingTasks
    
    // If task completed successfully, dispatch event to refresh content
    if (update.status === 'done') {
      dispatch('contentAdded', { taskId, result: update.result })
    }
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
   * Switches between different source type tabs
   * @param tab - Tab identifier ('upload', 'website', or 'youtube')
   */
  function setActiveTab(tab: string) {
    activeTab = tab
  }
  
  /**
   * Handles dragover events for file drop zone
   * Prevents default behavior and shows visual feedback
   * @param event - Drag event from file being dragged over drop zone
   */
  function handleDragOver(event: DragEvent) {
    event.preventDefault()  // Prevent default to allow drop
    isDragging = true      // Show visual feedback
  }
  
  /**
   * Handles dragleave events when file leaves drop zone
   * Removes visual feedback when drag leaves the area
   * @param event - Drag event from file leaving drop zone
   */
  function handleDragLeave(event: DragEvent) {
    event.preventDefault()
    isDragging = false     // Remove visual feedback
  }
  
  /**
   * Handles file drop events in the drop zone
   * Processes dropped files and adds them to the upload list
   * @param event - Drop event containing the dropped files
   */
  function handleDrop(event: DragEvent) {
    event.preventDefault()
    isDragging = false
    const files = Array.from(event.dataTransfer?.files || [])
    processFiles(files)   // Process the dropped files
  }
  
  /**
   * Handles file selection from the file input element
   * Triggered when user clicks "choose file" and selects files
   * @param event - Change event from file input element
   */
  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement
    const files = Array.from(target.files || [])
    processFiles(files)  // Process the selected files
  }
  
  /**
   * Processes an array of files and adds them to the uploaded files list
   * Extracts relevant file information and updates the UI
   * @param files - Array of File objects to process
   */
  function processFiles(files: File[]) {
    // Filter files by supported types
    const supportedExtensions = ['.pdf', '.docx', '.xls', '.xlsx', '.txt', '.md', '.mp3', '.wav', '.m4a']
    const validFiles = files.filter(file => {
      const extension = '.' + file.name.split('.').pop()?.toLowerCase()
      return supportedExtensions.includes(extension)
    })
    
    if (validFiles.length !== files.length) {
      processingError = `${files.length - validFiles.length} file(s) skipped due to unsupported format`
      setTimeout(() => processingError = '', 5000)
    }
    
    // Add to selected files for upload
    selectedFiles = [...selectedFiles, ...validFiles]
    
    // Add to display list
    const newFiles = validFiles.map(file => ({
      name: file.name,              // Original filename
      size: file.size,              // File size in bytes
      type: file.type || 'Unknown'  // MIME type or fallback
    }))
    uploadedFiles = [...uploadedFiles, ...newFiles]  // Add to existing files
  }
  
  /**
   * Removes a file from the uploaded files list
   * @param index - Index of the file to remove from the array
   */
  function removeFile(index: number) {
    selectedFiles = selectedFiles.filter((_, i) => i !== index)
    uploadedFiles = uploadedFiles.filter((_, i) => i !== index)
  }

  /**
   * Upload selected files to the backend
   */
  async function uploadFiles() {
    console.log('Upload files called:', {
      selectedFilesCount: selectedFiles.length,
      studyTopicId: studyTopicId,
      studyTopicIdType: typeof studyTopicId
    })
    
    if (selectedFiles.length === 0) {
      processingError = 'No files selected'
      return
    }
    
    if (!studyTopicId || studyTopicId.trim() === '') {
      processingError = 'Study topic ID not available. Please close and reopen the modal.'
      return
    }

    try {
      processingError = '' // Clear any previous errors
      const response = await apiService.uploadDocuments(selectedFiles, studyTopicId)
      
      // Create processing task for tracking
      createProcessingTask(
        response.task_id, 
        'upload', 
        `Uploading ${response.files.length} file(s)`
      )
      
      // Clear selected files after successful upload initiation
      selectedFiles = []
      uploadedFiles = []
      
    } catch (error) {
      console.error('Upload failed:', error)
      processingError = error instanceof Error ? error.message : 'Upload failed'
    }
  }
  
  /**
   * Formats file size from bytes to human-readable format
   * @param bytes - File size in bytes
   * @returns Formatted string like "1.5 MB", "234 KB", etc.
   */
  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  /**
   * Handles website URL submission for scraping
   */
  async function handleWebsiteSubmit() {
    if (!websiteUrl.trim() || !studyTopicId) {
      processingError = 'Please enter a valid URL and ensure study topic is available'
      return
    }

    try {
      const response = await apiService.processWebpage(websiteUrl.trim(), studyTopicId)
      
      // Create processing task for tracking
      createProcessingTask(
        response.task_id, 
        'webpage', 
        `Processing: ${websiteUrl.trim()}`
      )
      
      // Clear input after successful submission
      websiteUrl = ''
      processingError = ''
    } catch (error) {
      console.error('Website processing failed:', error)
      processingError = error instanceof Error ? error.message : 'Website processing failed'
    }
  }
  
  /**
   * Handles YouTube URL submission for video processing
   */
  async function handleYouTubeSubmit() {
    console.log('YouTube submit called:', {
      youtubeUrl: youtubeUrl,
      studyTopicId: studyTopicId,
      studyTopicIdType: typeof studyTopicId
    })
    
    if (!youtubeUrl.trim()) {
      processingError = 'Please enter a valid YouTube URL'
      return
    }
    
    if (!studyTopicId || studyTopicId.trim() === '') {
      processingError = 'Study topic ID not available. Please close and reopen the modal.'
      return
    }

    try {
      processingError = '' // Clear any previous errors
      const response = await apiService.processYouTubeVideo(youtubeUrl.trim(), studyTopicId)
      
      // Create processing task for tracking
      createProcessingTask(
        response.task_id, 
        'youtube', 
        `Processing: ${youtubeUrl.trim()}`
      )
      
      // Clear input after successful submission
      youtubeUrl = ''
      
    } catch (error) {
      console.error('YouTube processing failed:', error)
      processingError = error instanceof Error ? error.message : 'YouTube processing failed'
    }
  }
</script>

<!-- 
  ========================================
  SOURCES MODAL TEMPLATE
  ========================================
  
  Multi-tab interface for adding different types of source materials:
  1. Upload Tab: File drag-and-drop and selection
  2. Website Tab: URL scraping for articles/documentation
  3. YouTube Tab: Video transcript extraction
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
    aria-labelledby="sources-modal-title"
    tabindex="-1"
  >
    <!-- 
      Modal Container
      - Large modal for comprehensive source management
      - Neobrutalism styling with thick black border
      - Flexbox column layout for header, tabs, content, and footer
    -->
    <div 
      class="bg-white border-4 border-black w-full max-w-4xl h-4/5 flex flex-col"
    >
      <!-- 
        Modal Header
        - Contains topic title and close button
        - Fixed height with bottom border separator
      -->
      <div class="flex justify-between items-center p-4 border-b-4 border-black bg-white">
        <!-- Title section -->
        <div>
          <h2 id="sources-modal-title" class="text-xl font-bold font-mono text-black mb-1">
            Add sources: {topicTitle}
          </h2>
          <p class="text-sm text-gray-600">Upload files, scrape websites, or add YouTube videos to enhance your topic</p>
          {#if !studyTopicId}
            <p class="text-xs text-red-600 mt-1">⚠️ Study Topic ID missing</p>
          {:else}
            <p class="text-xs text-green-600 mt-1">✓ Topic ID: {studyTopicId.slice(0, 8)}...</p>
          {/if}
        </div>
        
        <!-- Close button -->
        <button 
          class="bg-brand-pink text-white border-2 border-black rounded px-3 py-2 font-mono font-bold cursor-pointer text-lg hover:bg-opacity-90"
          on:click={handleClose}
          aria-label="Close modal"
        >
          ×
        </button>
      </div>
      
      <!-- 
        Modal Body
        - Main content area with tabbed interface
        - Flexible layout to accommodate different content types
      -->
      <div class="flex-1 flex flex-col overflow-hidden">
        
        <!-- 
          Tab Navigation
          - Three tabs for different source types
          - Yellow background for visual consistency
          - Active tab highlighted with white background
        -->
        <div class="flex border-b-4 border-black bg-brand-yellow">
          <!-- Upload Files Tab -->
          <button 
            class="flex-1 p-4 font-mono font-bold text-sm border-none border-r-2 border-black cursor-pointer text-black {activeTab === 'upload' ? 'bg-white' : 'bg-transparent'}"
            on:click={() => setActiveTab('upload')}
          >
            📁 Upload Files
          </button>
          
          <!-- Website Scraping Tab -->
          <button 
            class="flex-1 p-4 font-mono font-bold text-sm border-none border-r-2 border-black cursor-pointer text-black {activeTab === 'website' ? 'bg-white' : 'bg-transparent'}"
            on:click={() => setActiveTab('website')}
          >
            🌐 Website
          </button>
          
          <!-- YouTube Processing Tab -->
          <button 
            class="flex-1 p-4 font-mono font-bold text-sm border-none cursor-pointer text-black {activeTab === 'youtube' ? 'bg-white' : 'bg-transparent'}"
            on:click={() => setActiveTab('youtube')}
          >
            📺 YouTube
          </button>
        </div>
        
        <!-- 
          Tab Content Area
          - Scrollable content area for each tab
          - Light gray background to distinguish from white modal elements
        -->
        <div class="flex-1 p-8 overflow-y-auto bg-gray-50">
          
          <!-- UPLOAD TAB CONTENT -->
          {#if activeTab === 'upload'}
            <div class="h-full flex flex-col gap-6">
              
              <!-- 
                Drag & Drop Upload Area
                - Large interactive area for file uploads
                - Visual feedback during drag operations
                - Accessible with keyboard navigation and ARIA labels
                - Click to open file picker as alternative to drag-drop
              -->
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
                <!-- Upload icon -->
                <div class="text-5xl mb-4">📤</div>
                
                <!-- Upload instructions -->
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
              
              <!-- Hidden file input element -->
              <input 
                id="file-input"
                type="file"
                multiple
                accept=".pdf,.txt,.md,.mp3,.wav,.m4a"
                class="hidden"
                on:change={handleFileSelect}
              />
              
              <!-- 
                Selected Files List
                - Shows only when files have been selected
                - Scrollable list with file details and remove buttons
                - Each file shows name, size, and type information
              -->
              {#if uploadedFiles.length > 0}
                <div class="border-2 border-black bg-white p-4">
                  <h4 class="font-bold font-mono mb-4">
                    Selected Files ({uploadedFiles.length})
                  </h4>
                  
                  <!-- Scrollable file list -->
                  <div class="flex flex-col gap-2 max-h-48 overflow-y-auto">
                    {#each uploadedFiles as file, index}
                      <!-- Individual file entry -->
                      <div class="flex justify-between items-center p-3 border border-black bg-gray-50">
                        <!-- File information -->
                        <div class="flex-1">
                          <div class="font-bold text-sm">{file.name}</div>
                          <div class="text-xs text-gray-600">{formatFileSize(file.size)} • {file.type}</div>
                        </div>
                        
                        <!-- Remove button -->
                        <button 
                          class="bg-brand-red text-white border border-black rounded px-2 py-1 cursor-pointer text-xs hover:bg-opacity-90"
                          on:click={() => removeFile(index)}
                          disabled={isProcessing}
                        >
                          Remove
                        </button>
                      </div>
                    {/each}
                  </div>
                  
                  <!-- Upload button -->
                  <div class="mt-4 pt-4 border-t border-gray-300">
                    <button 
                      class="w-full bg-brand-blue text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer hover:bg-opacity-90 {isProcessing ? 'opacity-50 cursor-not-allowed' : ''}"
                      on:click={uploadFiles}
                      disabled={isProcessing || uploadedFiles.length === 0}
                    >
                      {isProcessing ? 'Processing...' : `Upload ${uploadedFiles.length} File(s)`}
                    </button>
                  </div>
                </div>
              {/if}
            </div>
            
          <!-- WEBSITE TAB CONTENT -->
          {:else if activeTab === 'website'}
            <div class="h-full flex flex-col gap-4">
              
              <!-- Website scraping introduction -->\n              <div class="text-center mb-4">
                <div class="text-3xl mb-2">🌐</div>
                <h3 class="text-base font-bold font-mono mb-1">
                  Scrape Website
                </h3>
                <p class="text-gray-600 text-sm">
                  Enter a website URL to extract and analyze its content
                </p>
              </div>
              
              <!-- \n                Website URL Input Section\n                - Input field with label and submit button\n                - TODO: Implement actual scraping functionality\n              -->\n              <div class="bg-white border-2 border-black p-4">
                <label for="website-url-input" class="block font-bold font-mono mb-2 text-sm">
                  Website URL
                </label>
                <div class="flex gap-2">
                  <!-- URL input field -->\n                  <input 
                    id="website-url-input"
                    type="url"
                    bind:value={websiteUrl}
                    placeholder="https://example.com"
                    class="flex-1 p-2 border-2 border-black font-inter text-sm"
                  />
                  <!-- Scrape button -->
                  <button 
                    class="bg-brand-pink text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer text-sm hover:bg-opacity-90 {isProcessing ? 'opacity-50 cursor-not-allowed' : ''}"
                    on:click={handleWebsiteSubmit}
                    disabled={isProcessing || !websiteUrl.trim()}
                  >
                    {isProcessing ? 'Processing...' : 'Scrape'}
                  </button>
                </div>
              </div>
              
              <!-- \n                Quick Actions Grid\n                - Preset buttons for common website types\n                - Visual categories to help users choose appropriate scraping method\n                - TODO: Implement functionality for each quick action\n              -->\n              <div class="bg-white border-2 border-black p-4">
                <h4 class="font-bold font-mono mb-3 text-sm">
                  Quick Actions
                </h4>
                <div class="grid grid-cols-2 gap-2">
                  <!-- Article/Blog preset -->\n                  <button class="p-3 border-2 border-black bg-gray-50 text-left cursor-pointer font-mono text-xs hover:bg-brand-yellow">
                    📄 Article/Blog
                  </button>
                  <!-- Documentation preset -->\n                  <button class="p-3 border-2 border-black bg-gray-50 text-left cursor-pointer font-mono text-xs hover:bg-brand-yellow">
                    📚 Documentation
                  </button>
                  <!-- News article preset -->\n                  <button class="p-3 border-2 border-black bg-gray-50 text-left cursor-pointer font-mono text-xs hover:bg-brand-yellow">
                    📰 News Article
                  </button>
                  <!-- Company page preset -->\n                  <button class="p-3 border-2 border-black bg-gray-50 text-left cursor-pointer font-mono text-xs hover:bg-brand-yellow">
                    🏢 Company Page
                  </button>
                </div>
              </div>
            </div>
            
          <!-- YOUTUBE TAB CONTENT -->
          {:else if activeTab === 'youtube'}
            <div class="h-full flex flex-col gap-4">
              
              <!-- YouTube processing introduction -->
              <div class="text-center mb-4">
                <div class="text-3xl mb-2">📺</div>
                <h3 class="text-base font-bold font-mono mb-1">
                  YouTube Video
                </h3>
                <p class="text-gray-600 text-sm">
                  Add YouTube videos to extract transcripts and analyze content
                </p>
              </div>
              
              <!-- 
                YouTube URL Input Section
                - Input field for YouTube video URLs
                - TODO: Implement actual YouTube transcript extraction
              -->
              <div class="bg-white border-2 border-black p-4">
                <label for="youtube-url-input" class="block font-bold font-mono mb-2 text-sm">
                  YouTube URL
                </label>
                <div class="flex gap-2">
                  <!-- YouTube URL input field -->
                  <input 
                    id="youtube-url-input"
                    type="url"
                    bind:value={youtubeUrl}
                    placeholder="https://youtube.com/watch?v=..."
                    class="flex-1 p-2 border-2 border-black font-inter text-sm"
                  />
                  <!-- Add video button -->
                  <button 
                    class="bg-brand-pink text-white border-2 border-black rounded px-4 py-2 font-mono font-bold cursor-pointer text-sm hover:bg-opacity-90 {isProcessing ? 'opacity-50 cursor-not-allowed' : ''}"
                    on:click={handleYouTubeSubmit}
                    disabled={isProcessing || !youtubeUrl.trim()}
                  >
                    {isProcessing ? 'Processing...' : 'Add Video'}
                  </button>
                </div>
              </div>
              
              <!-- 
                YouTube Features Information
                - Shows what capabilities are available for YouTube processing
                - Helps users understand what they'll get from adding videos
              -->
              <div class="bg-white border-2 border-black p-4">
                <h4 class="font-bold font-mono mb-3 text-sm">
                  Features
                </h4>
                <!-- Features grid with checkmark indicators -->
                <div class="grid grid-cols-2 gap-2">
                  <!-- Transcript extraction feature -->
                  <div class="flex items-center gap-1">
                    <span class="text-green-500 text-xs">✓</span>
                    <span class="text-xs">Transcript extraction</span>
                  </div>
                  <!-- Metadata analysis feature -->
                  <div class="flex items-center gap-1">
                    <span class="text-green-500 text-xs">✓</span>
                    <span class="text-xs">Metadata analysis</span>
                  </div>
                  <!-- Chapter detection feature -->
                  <div class="flex items-center gap-1">
                    <span class="text-green-500 text-xs">✓</span>
                    <span class="text-xs">Chapter detection</span>
                  </div>
                  <!-- Multi-language support feature -->
                  <div class="flex items-center gap-1">
                    <span class="text-green-500 text-xs">✓</span>
                    <span class="text-xs">Multi-language</span>
                  </div>
                </div>
              </div>
            </div>
          {/if}
        </div>
        
        <!-- Processing Tasks Status -->
        {#if processingTasks.length > 0}
          <div class="p-4 border-t-2 border-black bg-gray-50">
            <h4 class="font-bold font-mono mb-3 text-sm">
              Processing Tasks ({processingTasks.length})
            </h4>
            
            <div class="flex flex-col gap-2 max-h-32 overflow-y-auto">
              {#each processingTasks as task}
                <div class="flex items-center justify-between p-2 border border-black bg-white text-xs">
                  <!-- Task info -->
                  <div class="flex-1">
                    <div class="font-bold">{task.name}</div>
                    {#if task.message}
                      <div class="text-gray-600">{task.message}</div>
                    {/if}
                    {#if task.error}
                      <div class="text-red-600">Error: {task.error}</div>
                    {/if}
                  </div>
                  
                  <!-- Status indicator -->
                  <div class="ml-2">
                    {#if task.status === 'processing'}
                      <div class="flex items-center gap-1">
                        <div class="animate-spin w-3 h-3 border border-gray-400 border-t-transparent rounded-full"></div>
                        <span class="text-blue-600">Processing</span>
                      </div>
                    {:else if task.status === 'done'}
                      <span class="text-green-600">✓ Done</span>
                    {:else if task.status === 'failed'}
                      <span class="text-red-600">✗ Failed</span>
                    {:else}
                      <span class="text-gray-600">Pending</span>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
        
        <!-- Error Display -->
        {#if processingError}
          <div class="p-3 border-t-2 border-black bg-red-100 border-red-500 text-red-700 text-sm">
            <strong>Error:</strong> {processingError}
          </div>
        {/if}
        
        <!-- 
          Modal Footer
          - Fixed at bottom of modal
          - Shows source limits and action buttons
          - Cancel and Save options for user actions
        -->
        <div class="p-4 border-t-4 border-black bg-white flex justify-between items-center">
          <!-- Processing status indicator -->
          <div class="text-sm text-gray-600">
            {#if processingTasks.length > 0}
              {processingTasks.filter(t => t.status === 'done').length} / {processingTasks.length} tasks completed
            {:else}
              Ready to add sources
            {/if}
          </div>
          
          <!-- Action buttons -->
          <div class="flex gap-2">
            <!-- Cancel button -->
            <button 
              class="bg-gray-50 text-black border-2 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer hover:bg-gray-100"
              on:click={handleClose}
            >
              {isProcessing ? 'Close' : 'Cancel'}
            </button>
            <!-- Done button -->
            <button 
              class="bg-brand-blue text-white border-2 border-black rounded px-6 py-3 font-mono font-bold cursor-pointer hover:bg-opacity-90"
              on:click={handleClose}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}