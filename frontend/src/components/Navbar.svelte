<script lang="ts">
  import { link } from 'svelte-spa-router'
  import Button from './Button.svelte'
</script>

<nav class="bg-white border-b-4 border-black p-4">
  <div class="max-w-7xl mx-auto flex items-center justify-between">
    <a href="/" use:link class="text-2xl font-bold text-black" style="font-family: 'IBM Plex Mono', monospace;">
      Study4Me
    </a>
    
    <div class="flex items-center space-x-4">
      <a href="/" use:link class="font-medium text-black hover:text-blue-600" style="font-family: 'IBM Plex Mono', monospace;">
        Dashboard
      </a>
      <a href="/create" use:link class="font-medium text-black hover:text-blue-600" style="font-family: 'IBM Plex Mono', monospace;">
        New Topic
      </a>
      <a href="/analytics" use:link class="font-medium text-black hover:text-blue-600" style="font-family: 'IBM Plex Mono', monospace;">
        Analytics
      </a>
      <Button variant="primary" size="sm">
        Connect Wallet
      </Button>
    </div>
  </div>
</nav>