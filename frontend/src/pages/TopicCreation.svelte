<script lang="ts">
  import { onMount } from 'svelte'
  import { push } from 'svelte-spa-router'
  import Card from '../components/Card.svelte'
  import Button from '../components/Button.svelte'
  import Input from '../components/Input.svelte'
  import { topicActions } from '../stores/topicStore'
  import { uiActions } from '../stores/uiStore'
  
  let title = ''
  let description = ''
  let contentFile: FileList | null = null
  let contentUrl = ''
  let contentType: 'file' | 'url' = 'file'
  let isSubmitting = false
  
  function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement
    contentFile = target.files
  }
  
  async function handleSubmit() {
    if (!title.trim() || !description.trim()) {
      uiActions.addNotification({
        type: 'error',
        message: 'Please fill in all required fields'
      })
      return
    }
    
    if (contentType === 'file' && (!contentFile || contentFile.length === 0)) {
      uiActions.addNotification({
        type: 'error',
        message: 'Please select a file to upload'
      })
      return
    }
    
    if (contentType === 'url' && !contentUrl.trim()) {
      uiActions.addNotification({
        type: 'error',
        message: 'Please enter a valid URL'
      })
      return
    }
    
    isSubmitting = true
    
    try {
      const newTopic = {
        id: Math.random().toString(36).substr(2, 9),
        title: title.trim(),
        description: description.trim(),
        status: 'processing' as const,
        createdAt: new Date().toISOString().split('T')[0],
        updatedAt: new Date().toISOString().split('T')[0]
      }
      
      topicActions.addTopic(newTopic)
      
      uiActions.addNotification({
        type: 'success',
        message: 'Topic created successfully! Processing will begin shortly.'
      })
      
      push('/')
    } catch (error) {
      uiActions.addNotification({
        type: 'error',
        message: 'Failed to create topic. Please try again.'
      })
    } finally {
      isSubmitting = false
    }
  }
</script>

<div class="max-w-4xl mx-auto p-6">
  <div class="mb-8">
    <h1 class="text-4xl font-heading font-bold mb-4">Create New Topic</h1>
    <p class="text-lg text-secondary-text">
      Upload content and let AI build your knowledge graph
    </p>
  </div>
  
  <Card>
    <form on:submit|preventDefault={handleSubmit} class="space-y-6">
      <Input
        label="Topic Title"
        placeholder="Enter a descriptive title for your topic"
        bind:value={title}
        required
      />
      
      <div>
        <label class="block text-sm font-heading font-bold mb-2 text-border-black">
          Description <span class="text-accent-red">*</span>
        </label>
        <textarea
          bind:value={description}
          placeholder="Describe what you want to learn about this topic"
          required
          class="neo-input w-full h-32 resize-none"
        ></textarea>
      </div>
      
      <div>
        <label class="block text-sm font-heading font-bold mb-4 text-border-black">
          Content Source
        </label>
        
        <div class="flex space-x-4 mb-4">
          <label class="flex items-center">
            <input
              type="radio"
              bind:group={contentType}
              value="file"
              class="mr-2"
            />
            <span class="font-heading">Upload File</span>
          </label>
          <label class="flex items-center">
            <input
              type="radio"
              bind:group={contentType}
              value="url"
              class="mr-2"
            />
            <span class="font-heading">From URL</span>
          </label>
        </div>
        
        {#if contentType === 'file'}
          <div>
            <input
              type="file"
              on:change={handleFileChange}
              accept=".pdf,.txt,.md,.docx"
              class="neo-input w-full file:mr-4 file:py-2 file:px-4 file:rounded-neo file:border-2 file:border-border-black file:text-sm file:font-heading file:bg-accent-blue file:text-white hover:file:bg-accent-red"
            />
            <p class="text-sm text-secondary-text mt-2">
              Supported formats: PDF, TXT, MD, DOCX
            </p>
          </div>
        {:else}
          <Input
            placeholder="https://example.com/article"
            bind:value={contentUrl}
            label="Content URL"
          />
        {/if}
      </div>
      
      <div class="flex space-x-4 pt-4">
        <Button
          variant="primary"
          size="lg"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Creating...' : 'Create Topic'}
        </Button>
        <Button
          variant="secondary"
          size="lg"
          onclick={() => push('/')}
        >
          Cancel
        </Button>
      </div>
    </form>
  </Card>
</div>