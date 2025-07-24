<script lang="ts">
  export let type: 'text' | 'email' | 'password' | 'number' = 'text'
  export let placeholder = ''
  export let value = ''
  export let label = ''
  export let required = false
  export let disabled = false
  
  let inputElement: HTMLInputElement
  
  export const focus = () => inputElement?.focus()
</script>

<div class="w-full">
  {#if label}
    <label class="block text-sm font-heading font-bold mb-2 text-border-black" for={label}>
      {label}
      {#if required}<span class="text-accent-red">*</span>{/if}
    </label>
  {/if}
  <input
    bind:this={inputElement}
    bind:value
    {type}
    {placeholder}
    {required}
    {disabled}
    id={label}
    class="neo-input w-full {disabled ? 'opacity-50 cursor-not-allowed' : ''}"
  />
</div>