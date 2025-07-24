<script lang="ts">
  import { authStore, authActions } from '../stores/auth'
  import { uiStore, uiActions } from '../stores/uiStore'
  import Card from '../components/Card.svelte'
  import Button from '../components/Button.svelte'
  import Input from '../components/Input.svelte'
  
  let apiKey = ''
  let emailNotifications = true
  let autoSave = true
  
  function handleSaveSettings() {
    uiActions.addNotification({
      type: 'success',
      message: 'Settings saved successfully!'
    })
  }
  
  function handleDisconnectWallet() {
    authActions.disconnect()
    uiActions.addNotification({
      type: 'info',
      message: 'Wallet disconnected'
    })
  }
  
  function handleDeleteAccount() {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      uiActions.addNotification({
        type: 'error',
        message: 'Account deletion is not implemented yet'
      })
    }
  }
</script>

<div class="max-w-4xl mx-auto p-6">
  <div class="mb-8">
    <h1 class="text-4xl font-heading font-bold mb-4">Settings</h1>
    <p class="text-lg text-secondary-text">
      Manage your account and application preferences
    </p>
  </div>
  
  <div class="space-y-8">
    <Card title="Account Information">
      <div class="space-y-4">
        {#if $authStore.isConnected}
          <div>
            <label class="block text-sm font-heading font-bold mb-2">Wallet Address</label>
            <div class="bg-gray-50 border-4 border-border-black rounded-neo p-3 font-code text-sm">
              {$authStore.walletAddress}
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-heading font-bold mb-2">NFT Status</label>
            <span class="inline-block px-3 py-1 rounded-neo text-sm font-heading {$authStore.hasNFT ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
              {$authStore.hasNFT ? 'Verified' : 'Not Verified'}
            </span>
          </div>
          
          <Button variant="danger" onclick={handleDisconnectWallet}>
            Disconnect Wallet
          </Button>
        {:else}
          <div class="text-center py-8">
            <p class="text-secondary-text mb-4">No wallet connected</p>
            <Button variant="primary">Connect Wallet</Button>
          </div>
        {/if}
      </div>
    </Card>
    
    <Card title="API Configuration">
      <div class="space-y-4">
        <Input
          type="password"
          label="OpenAI API Key"
          placeholder="sk-..."
          bind:value={apiKey}
        />
        <p class="text-sm text-secondary-text">
          Your API key is stored locally and used for AI processing
        </p>
      </div>
    </Card>
    
    <Card title="Preferences">
      <div class="space-y-4">
        <label class="flex items-center">
          <input
            type="checkbox"
            bind:checked={emailNotifications}
            class="mr-3 w-4 h-4 text-accent-blue border-2 border-border-black rounded focus:ring-accent-blue"
          />
          <span class="font-heading">Email notifications</span>
        </label>
        
        <label class="flex items-center">
          <input
            type="checkbox"
            bind:checked={autoSave}
            class="mr-3 w-4 h-4 text-accent-blue border-2 border-border-black rounded focus:ring-accent-blue"
          />
          <span class="font-heading">Auto-save progress</span>
        </label>
        
        <div>
          <label class="block text-sm font-heading font-bold mb-2">Theme</label>
          <select class="neo-input">
            <option value="light">Light</option>
            <option value="dark" disabled>Dark (Coming Soon)</option>
          </select>
        </div>
      </div>
    </Card>
    
    <Card title="Data Management">
      <div class="space-y-4">
        <div class="flex space-x-4">
          <Button variant="secondary">Export Data</Button>
          <Button variant="secondary">Import Data</Button>
        </div>
        
        <div class="border-t-4 border-border-black pt-4">
          <h4 class="font-heading font-bold text-accent-red mb-2">Danger Zone</h4>
          <p class="text-sm text-secondary-text mb-4">
            Once you delete your account, there is no going back. Please be certain.
          </p>
          <Button variant="danger" onclick={handleDeleteAccount}>
            Delete Account
          </Button>
        </div>
      </div>
    </Card>
    
    <div class="flex justify-end">
      <Button variant="primary" size="lg" onclick={handleSaveSettings}>
        Save Settings
      </Button>
    </div>
  </div>
</div>