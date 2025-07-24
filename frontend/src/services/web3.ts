interface WalletProvider {
  isMetaMask?: boolean
  request: (args: { method: string; params?: any[] }) => Promise<any>
  on: (event: string, handler: (...args: any[]) => void) => void
  removeListener: (event: string, handler: (...args: any[]) => void) => void
}

declare global {
  interface Window {
    ethereum?: WalletProvider
  }
}

class Web3Service {
  private provider: WalletProvider | null = null
  
  constructor() {
    if (typeof window !== 'undefined' && window.ethereum) {
      this.provider = window.ethereum
    }
  }
  
  async connectWallet(): Promise<string> {
    if (!this.provider) {
      throw new Error('No wallet provider found. Please install MetaMask.')
    }
    
    try {
      const accounts = await this.provider.request({
        method: 'eth_requestAccounts',
      })
      
      if (accounts.length === 0) {
        throw new Error('No accounts returned from wallet')
      }
      
      return accounts[0]
    } catch (error) {
      console.error('Failed to connect wallet:', error)
      throw error
    }
  }
  
  async getAccount(): Promise<string | null> {
    if (!this.provider) return null
    
    try {
      const accounts = await this.provider.request({
        method: 'eth_accounts',
      })
      
      return accounts.length > 0 ? accounts[0] : null
    } catch (error) {
      console.error('Failed to get account:', error)
      return null
    }
  }
  
  async checkNFTOwnership(address: string): Promise<boolean> {
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      return Math.random() > 0.5
    } catch (error) {
      console.error('Failed to check NFT ownership:', error)
      return false
    }
  }
  
  onAccountsChanged(callback: (accounts: string[]) => void) {
    if (this.provider) {
      this.provider.on('accountsChanged', callback)
    }
  }
  
  onChainChanged(callback: (chainId: string) => void) {
    if (this.provider) {
      this.provider.on('chainChanged', callback)
    }
  }
  
  removeListeners() {
    if (this.provider) {
      this.provider.removeListener('accountsChanged', () => {})
      this.provider.removeListener('chainChanged', () => {})
    }
  }
  
  get isWalletInstalled(): boolean {
    return !!this.provider
  }
}

export const web3Service = new Web3Service()
export default web3Service