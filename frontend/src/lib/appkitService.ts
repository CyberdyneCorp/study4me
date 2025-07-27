/**
 * Reown AppKit Service - Handles wallet connections via WalletConnect protocol
 * 
 * This service provides a comprehensive interface for Reown AppKit operations:
 * - AppKit initialization with proper configuration
 * - QR code modal for mobile wallet connections (MetaMask Mobile, etc.)
 * - Multi-chain support (Ethereum, Polygon, Arbitrum)
 * - Connection state management
 * - Error handling and logging
 */

import { createAppKit } from '@reown/appkit'
import { WagmiAdapter } from '@reown/appkit-adapter-wagmi'
import { mainnet, arbitrum, polygon } from '@reown/appkit/networks'
import type { AppKit, AppKitNetwork } from '@reown/appkit'
import { 
  appKitInstance, 
  appKitActions, 
  type WalletInfo
} from '../stores/appKitStore'
import { get } from 'svelte/store'

// AppKit configuration interface
interface AppKitConfig {
  projectId: string
  networks: AppKitNetwork[]
  defaultNetwork: AppKitNetwork
  metadata: {
    name: string
    description: string
    url: string
    icons: string[]
  }
  features?: {
    analytics?: boolean
    email?: boolean
    socials?: string[]
  }
  themeMode?: 'light' | 'dark' | 'auto'
  themeVariables?: Record<string, string>
}

class AppKitService {
  private appKit: AppKit | null = null
  private wagmiAdapter: WagmiAdapter | null = null
  private isInitializing = false

  /**
   * Initialize Reown AppKit with environment configuration
   * @returns Promise<boolean> - Success status
   */
  async initialize(): Promise<boolean> {
    console.log('AppKit initialize called, current state:', {
      isInitializing: this.isInitializing,
      hasAppKit: !!this.appKit,
      serviceInstance: !!this
    })

    // Prevent multiple initialization attempts
    if (this.isInitializing) {
      console.log('AppKit initialization already in progress')
      return false
    }

    // Check if already initialized
    if (this.appKit) {
      console.log('AppKit already initialized')
      appKitActions.setInitialized(true)
      return true
    }

    try {
      this.isInitializing = true
      appKitActions.setLoading(true)
      appKitActions.clearError()

      // Validate required environment variables
      const projectId = import.meta.env.VITE_REOWN_PROJECT_ID
      console.log('Project ID from env:', projectId)
      
      if (!projectId || projectId === 'your_reown_project_id') {
        throw new Error('VITE_REOWN_PROJECT_ID is not configured. Please set your Reown project ID in the .env file.')
      }

      // Define supported networks
      const networks = [mainnet, arbitrum, polygon]

      // Initialize Wagmi adapter
      this.wagmiAdapter = new WagmiAdapter({ 
        networks, 
        projectId 
      })

      // Create AppKit configuration
      const config: AppKitConfig = {
        projectId,
        networks,
        defaultNetwork: mainnet,
        metadata: {
          name: import.meta.env.VITE_REOWN_APP_NAME || 'Study4Me',
          description: import.meta.env.VITE_REOWN_APP_DESCRIPTION || 'Blockchain-gated study platform',
          url: import.meta.env.VITE_REOWN_APP_URL || 'https://study4me.com',
          icons: [import.meta.env.VITE_REOWN_APP_ICON || 'https://study4me.com/icon.png']
        },
        features: {
          analytics: true,
          email: false, // Disable email since we have Web3Auth for social login
          socials: [] // Disable social login since we have Web3Auth
        },
        themeMode: 'light',
        themeVariables: {
          '--w3m-color-mix': '#0050FF',
          '--w3m-color-mix-strength': 20,
          '--w3m-accent': '#FF2C2C',
          '--w3m-border-radius-master': '8px',
          '--w3m-font-family': '"JetBrains Mono", "IBM Plex Mono", monospace'
        }
      }

      // Initialize AppKit
      this.appKit = createAppKit({
        adapters: [this.wagmiAdapter],
        networks: config.networks,
        defaultNetwork: config.defaultNetwork,
        projectId: config.projectId,
        metadata: config.metadata,
        features: config.features,
        themeMode: config.themeMode,
        themeVariables: config.themeVariables,
        featuredWalletIds: [
          'c57ca95b47569778a828d19178114f4db188b89b763c899ba0be274e97267d96', // MetaMask
          'fd20dc426fb37566d803205b19bbc1d4096b248ac04548e3cfb6b3a38bd033aa', // Coinbase Wallet
          '4622a2b2d6af1c9844944291e5e7351a6aa24cd7b23099efac1b2fd875da31a0', // Trust Wallet
          '38f5d18bd8522c244bdd70cb4a68e0e718865155811c043f052fb9f1c51de662'  // Bitget Wallet
        ]
      })

      // Store instance and update state
      appKitInstance.set(this.appKit)
      appKitActions.setInitialized(true)

      // Set up event listeners
      this.setupEventListeners()

      console.log('Reown AppKit initialized successfully')
      return true

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to initialize Reown AppKit'
      console.error('AppKit initialization error:', errorMessage)
      appKitActions.setError(errorMessage)
      return false

    } finally {
      this.isInitializing = false
      appKitActions.setLoading(false)
    }
  }

  /**
   * Open the AppKit connection modal
   * This will show the QR code for mobile wallets like MetaMask Mobile
   * @returns Promise<void>
   */
  async openModal(): Promise<void> {
    try {
      console.log('AppKit openModal called, current state:', {
        hasAppKit: !!this.appKit,
        isInitializing: this.isInitializing,
        serviceInstance: !!this
      })

      // Ensure AppKit is initialized
      if (!this.appKit) {
        console.log('AppKit not initialized, attempting to initialize...')
        const initialized = await this.initialize()
        if (!initialized) {
          throw new Error('Failed to initialize AppKit')
        }
      }

      appKitActions.setLoading(true)
      appKitActions.clearError()

      // Open the connection modal
      console.log('Opening AppKit modal...')
      this.appKit?.open()

      console.log('AppKit modal opened successfully')

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to open AppKit modal'
      console.error('Open modal error:', errorMessage)
      console.error('Full error object:', error)
      appKitActions.setError(errorMessage)
    } finally {
      appKitActions.setLoading(false)
    }
  }

  /**
   * Open the AppKit modal with specific view
   * @param view - The view to open ('Connect', 'Account', 'Networks', etc.)
   */
  async openModalView(view: string): Promise<void> {
    try {
      if (!this.appKit) {
        const initialized = await this.initialize()
        if (!initialized) {
          throw new Error('Failed to initialize AppKit')
        }
      }

      this.appKit?.open({ view })
      console.log(`AppKit modal opened with view: ${view}`)

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : `Failed to open AppKit modal with view ${view}`
      console.error('Open modal view error:', errorMessage)
      appKitActions.setError(errorMessage)
    }
  }

  /**
   * Close the AppKit modal
   */
  closeModal(): void {
    this.appKit?.close()
  }

  /**
   * Get current wallet connection state
   * @returns WalletInfo | null
   */
  getWalletInfo(): WalletInfo | null {
    if (!this.appKit) {
      return null
    }

    const state = this.appKit.getState()
    
    return {
      isConnected: !!state.selectedNetworkId,
      address: state.selectedAccount?.address,
      chainId: state.selectedNetworkId,
      balance: state.selectedAccount?.balance
    }
  }

  /**
   * Disconnect the current wallet
   * @returns Promise<boolean> - Success status
   */
  async disconnect(): Promise<boolean> {
    try {
      if (!this.appKit) {
        console.warn('AppKit not initialized')
        return false
      }

      await this.appKit.disconnect()
      appKitActions.setDisconnected()

      console.log('Successfully disconnected from wallet')
      return true

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to disconnect wallet'
      console.error('Disconnect error:', errorMessage)
      appKitActions.setError(errorMessage)
      return false
    }
  }

  /**
   * Get AppKit instance
   * @returns AppKit | null
   */
  getInstance(): AppKit | null {
    return this.appKit
  }

  /**
   * Check if AppKit is initialized
   * @returns boolean
   */
  isInitialized(): boolean {
    return !!this.appKit
  }

  /**
   * Set up event listeners for AppKit state changes
   * @private
   */
  private setupEventListeners(): void {
    if (!this.appKit) return

    // Listen to modal state changes
    this.appKit.subscribeState((state) => {
      const walletInfo: WalletInfo = {
        isConnected: !!state.selectedNetworkId,
        address: state.selectedAccount?.address,
        chainId: state.selectedNetworkId,
        balance: state.selectedAccount?.balance
      }

      appKitActions.setWalletInfo(walletInfo)
      
      console.log('AppKit state changed:', {
        isConnected: walletInfo.isConnected,
        address: walletInfo.address,
        chainId: walletInfo.chainId
      })
    })

    // Listen to account changes
    this.appKit.subscribeAccount((account) => {
      console.log('Account changed:', account)
      
      if (account.isConnected) {
        const walletInfo: WalletInfo = {
          isConnected: true,
          address: account.address,
          chainId: account.chainId,
          balance: account.balance
        }
        appKitActions.setWalletInfo(walletInfo)
      } else {
        appKitActions.setDisconnected()
      }
    })

    // Listen to chain changes
    this.appKit.subscribeChainId((chainId) => {
      console.log('Chain changed:', chainId)
      appKitActions.setChainId(chainId)
    })
  }
}

// Create singleton instance
export const appKitService = new AppKitService()

// Export service methods for convenience (preserve 'this' context)
export const initializeAppKit = () => appKitService.initialize()
export const openAppKitModal = () => appKitService.openModal()
export const openAppKitModalView = (view: string) => appKitService.openModalView(view)
export const closeAppKitModal = () => appKitService.closeModal()
export const disconnectWallet = () => appKitService.disconnect()
export const getWalletInfo = () => appKitService.getWalletInfo()
export const getAppKitInstance = () => appKitService.getInstance()
export const isAppKitInitialized = () => appKitService.isInitialized()