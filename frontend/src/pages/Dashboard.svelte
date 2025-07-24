<script lang="ts">
  import { onMount } from 'svelte'
  import { topicStore, topicActions } from '../stores/topicStore'
  import Card from '../components/Card.svelte'
  import Button from '../components/Button.svelte'
  import { link } from 'svelte-spa-router'
  
  onMount(() => {
    topicActions.setTopics([
      {
        id: '1',
        title: 'Machine Learning Fundamentals',
        description: 'Basic concepts of ML algorithms and applications',
        status: 'completed',
        createdAt: '2024-01-15',
        updatedAt: '2024-01-16'
      },
      {
        id: '2',
        title: 'Quantum Computing Basics',
        description: 'Introduction to quantum mechanics and quantum algorithms',
        status: 'processing',
        createdAt: '2024-01-16',
        updatedAt: '2024-01-16'
      }
    ])
  })
  
  function getStatusColor(status: string) {
    switch (status) {
      case 'completed': return 'bg-green-200 text-green-900'
      case 'processing': return 'bg-yellow-200 text-yellow-900'
      case 'error': return 'bg-red-200 text-red-900'
      default: return 'bg-gray-200 text-gray-900'
    }
  }
</script>

<div class="max-w-7xl mx-auto p-6">
  <div class="mb-8">
    <h1 class="text-4xl font-heading font-bold mb-4">Dashboard</h1>
    <p class="text-lg text-secondary-text mb-6">
      Manage your study topics and knowledge graphs
    </p>
    <a href="/create" use:link>
      <Button variant="primary" size="lg">+ New Topic</Button>
    </a>
  </div>
  
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {#each $topicStore.topics as topic}
      <Card title={topic.title}>
        <p class="text-secondary-text mb-4">{topic.description}</p>
        
        <div class="flex items-center justify-between mb-4">
          <span class="inline-block px-3 py-1 rounded-neo text-sm font-heading {getStatusColor(topic.status)}">
            {topic.status}
          </span>
          <span class="text-sm text-secondary-text">{topic.createdAt}</span>
        </div>
        
        <div class="flex space-x-2">
          <a href="/topic/{topic.id}" use:link>
            <Button variant="primary" size="sm">View</Button>
          </a>
          <Button variant="secondary" size="sm">Edit</Button>
        </div>
      </Card>
    {/each}
    
    {#if $topicStore.topics.length === 0}
      <div class="col-span-full">
        <Card>
          <div class="text-center py-12">
            <h3 class="text-xl font-heading font-bold mb-4">No topics yet</h3>
            <p class="text-secondary-text mb-6">Create your first study topic to get started</p>
            <a href="/create" use:link>
              <Button variant="primary">Create Topic</Button>
            </a>
          </div>
        </Card>
      </div>
    {/if}
  </div>
</div>