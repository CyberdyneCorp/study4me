<script lang="ts">
  export let graphData: any = null
  export let width = 800
  export let height = 600
  
  let canvasElement: HTMLCanvasElement
  
  $: if (canvasElement && graphData) {
    renderGraph()
  }
  
  function renderGraph() {
    const ctx = canvasElement.getContext('2d')
    if (!ctx) return
    
    ctx.clearRect(0, 0, width, height)
    ctx.fillStyle = '#FFF200'
    ctx.fillRect(0, 0, width, height)
    
    ctx.strokeStyle = '#000000'
    ctx.lineWidth = 4
    ctx.strokeRect(0, 0, width, height)
    
    ctx.fillStyle = '#000000'
    ctx.font = 'bold 16px "IBM Plex Mono"'
    ctx.textAlign = 'center'
    ctx.fillText('Knowledge Graph Visualization', width / 2, 50)
    
    if (!graphData) {
      ctx.fillText('No graph data available', width / 2, height / 2)
      return
    }
    
    ctx.fillText(`Nodes: ${graphData.nodes?.length || 0}`, width / 2, height / 2 - 20)
    ctx.fillText(`Edges: ${graphData.edges?.length || 0}`, width / 2, height / 2 + 20)
  }
</script>

<div class="neo-card p-4">
  <h3 class="text-lg font-heading font-bold mb-4">Knowledge Graph</h3>
  <canvas
    bind:this={canvasElement}
    {width}
    {height}
    class="border-4 border-border-black rounded-neo"
  ></canvas>
</div>