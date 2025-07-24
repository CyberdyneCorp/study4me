<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'danger' = 'primary'
  export let size: 'sm' | 'md' | 'lg' = 'md'
  export let disabled = false
  export let onclick: (() => void) | undefined = undefined

  $: buttonClass = `neo-button ${getVariantClass(variant)} ${getSizeClass(size)} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`
  
  function getVariantClass(variant: string) {
    switch (variant) {
      case 'secondary': return 'bg-white text-black hover:bg-gray-100'
      case 'danger': return 'bg-red-500 text-white hover:bg-red-600'
      default: return ''
    }
  }
  
  function getSizeClass(size: string) {
    switch (size) {
      case 'sm': return 'text-sm px-4 py-2'
      case 'lg': return 'text-lg px-8 py-4'
      default: return 'text-base px-6 py-3'
    }
  }
</script>

<button 
  class={buttonClass}
  {disabled}
  on:click={onclick}
>
  <slot />
</button>