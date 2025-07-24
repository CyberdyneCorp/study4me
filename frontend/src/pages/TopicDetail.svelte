<script lang="ts">
  import { onMount } from 'svelte'
  import { params } from 'svelte-spa-router'
  import { topicStore, topicActions } from '../stores/topicStore'
  import Card from '../components/Card.svelte'
  import Button from '../components/Button.svelte'
  import GraphViewer from '../components/GraphViewer.svelte'
  import Input from '../components/Input.svelte'
  
  let query = ''
  let queryResult = ''
  let isQuerying = false
  
  $: topicId = $params.id
  $: topic = $topicStore.topics.find(t => t.id === topicId)
  
  onMount(() => {
    if (topicId && topic) {
      topicActions.selectTopic(topic)
    }
  })
  
  async function handleQuery() {
    if (!query.trim()) return
    
    isQuerying = true
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      queryResult = `Based on the knowledge graph for "${topic?.title}", here's what I found about "${query}": This is a simulated response that would come from the AI system analyzing the knowledge graph and providing insights.`
    } catch (error) {
      queryResult = 'Failed to process query. Please try again.'
    } finally {
      isQuerying = false
    }
  }
  
  function downloadAudio() {
    console.log('Downloading audio summary...')
  }
</script>

{#if topic}
  <div class="max-w-7xl mx-auto p-6">
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h1 class="text-4xl font-heading font-bold">{topic.title}</h1>
        <div class="flex space-x-2">
          <Button variant="secondary" size="sm">Edit</Button>
          <Button variant="danger" size="sm">Delete</Button>
        </div>
      </div>
      <p class="text-lg text-secondary-text mb-4">{topic.description}</p>
      <div class="flex items-center space-x-4">
        <span class="inline-block px-3 py-1 rounded-neo text-sm font-heading bg-green-100 text-green-800">
          {topic.status}
        </span>
        <span class="text-sm text-secondary-text">
          Created: {topic.createdAt}
        </span>
        <span class="text-sm text-secondary-text">
          Updated: {topic.updatedAt}
        </span>
      </div>
    </div>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div>
        <GraphViewer graphData={topic.graphData} />
      </div>
      
      <div class="space-y-6">
        <Card title="Query Knowledge Graph">
          <div class="space-y-4">
            <Input
              placeholder="Ask a question about this topic..."
              bind:value={query}
              label="Your Question"
            />
            <Button
              variant="primary"
              disabled={isQuerying || !query.trim()}
              onclick={handleQuery}
            >
              {isQuerying ? 'Searching...' : 'Ask Question'}
            </Button>
            
            {#if queryResult}
              <div class="bg-gray-50 border-4 border-border-black rounded-neo p-4">
                <h4 class="font-heading font-bold mb-2">Answer:</h4>
                <p class="text-secondary-text">{queryResult}</p>
              </div>
            {/if}
          </div>
        </Card>
        
        <Card title="Audio Summary">
          <div class="space-y-4">
            <p class="text-secondary-text">
              Get an AI-generated audio summary of this topic's key concepts.
            </p>
            
            {#if topic.audioSummary}
              <div class="bg-gray-50 border-2 border-border-black rounded-neo p-4">
                <audio controls class="w-full mb-4">
                  <source src={topic.audioSummary} type="audio/mpeg">
                  Your browser does not support the audio element.
                </audio>
              </div>
            {:else}
              <div class="text-center py-8">
                <p class="text-secondary-text mb-4">Audio summary not yet generated</p>
                <Button variant="primary">Generate Audio Summary</Button>
              </div>
            {/if}
            
            <Button variant="secondary" onclick={downloadAudio}>
              Download Audio
            </Button>
          </div>
        </Card>
      </div>
    </div>
  </div>
{:else}
  <div class="max-w-4xl mx-auto p-6">
    <Card>
      <div class="text-center py-12">
        <h2 class="text-2xl font-heading font-bold mb-4">Topic Not Found</h2>
        <p class="text-secondary-text mb-6">The requested topic could not be found.</p>
        <Button variant="primary" onclick={() => history.back()}>
          Go Back
        </Button>
      </div>
    </Card>
  </div>
{/if}