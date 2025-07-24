<script lang="ts">
  export let title = ''
  export let padding: 'sm' | 'md' | 'lg' = 'md'
  
  $: paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  }[padding]
</script>

<div class="neo-card {paddingClasses}">
  {#if title}
    <h3 class="text-xl font-bold mb-4 text-black" style="font-family: 'IBM Plex Mono', monospace;">{title}</h3>
  {/if}
  <slot />
</div>