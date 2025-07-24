/**
 * Web3Auth Service - Handles Web3Auth initialization and authentication
 * 
 * This service provides a comprehensive interface for Web3Auth operations:
 * - Web3Auth initialization with proper configuration
 * - Social authentication (Google, Twitter, GitHub, etc.)
 * - User session management
 * - Error handling and logging
 * - Provider management for blockchain interactions
 */

import { Web3Auth } from '@web3auth/modal'
import { CHAIN_NAMESPACES, WEB3AUTH_NETWORK, type IProvider } from '@web3auth/base'
import { 
  web3AuthInstance, 
  web3AuthActions, 
  type UserInfo 
} from '../stores/web3AuthStore'
import { get } from 'svelte/store'

// Web3Auth configuration interface
interface Web3AuthConfig {
  clientId: string
  web3AuthNetwork: WEB3AUTH_NETWORK
  chainConfig: {
    chainNamespace: CHAIN_NAMESPACES
    chainId: string
    rpcTarget: string
    displayName?: string
    blockExplorer?: string
    ticker?: string
    tickerName?: string
  }
  uiConfig?: {
    theme?: 'light' | 'dark'
    loginMethodsOrder?: string[]
    appLogo?: string
    appName?: string
  }
}

// Supported login providers
export type LoginProvider = 
  | 'google' 
  | 'twitter' 
  | 'facebook' 
  | 'discord' 
  | 'github' 
  | 'linkedin' 
  | 'twitch'
  | 'email_passwordless'

class Web3AuthService {
  private web3auth: Web3Auth | null = null
  private isInitializing = false

  /**
   * Initialize Web3Auth with environment configuration
   * @returns Promise<boolean> - Success status
   */
  async initialize(): Promise<boolean> {
    // Prevent multiple initialization attempts
    if (this.isInitializing) {
      console.log('Web3Auth initialization already in progress')
      return false
    }

    // Check if already initialized
    if (this.web3auth) {
      console.log('Web3Auth already initialized')
      web3AuthActions.setInitialized(true)
      return true
    }

    try {
      this.isInitializing = true
      web3AuthActions.setLoading(true)
      web3AuthActions.clearError()

      // Validate required environment variables
      const clientId = import.meta.env.VITE_WEB3AUTH_CLIENT_ID
      if (!clientId || clientId === 'your_client_id_from_dashboard') {
        throw new Error('VITE_WEB3AUTH_CLIENT_ID is not configured. Please set your Web3Auth client ID in the .env file.')
      }

      // Determine Web3Auth network
      const networkEnv = import.meta.env.VITE_WEB3AUTH_NETWORK || 'SAPPHIRE_DEVNET'
      const web3AuthNetwork = networkEnv === 'SAPPHIRE_MAINNET' 
        ? WEB3AUTH_NETWORK.SAPPHIRE_MAINNET 
        : WEB3AUTH_NETWORK.SAPPHIRE_DEVNET

      // Create Web3Auth configuration
      const config: Web3AuthConfig = {
        clientId,
        web3AuthNetwork,
        chainConfig: {
          chainNamespace: CHAIN_NAMESPACES.EIP155,
          chainId: import.meta.env.VITE_CHAIN_ID || '0x1',
          rpcTarget: import.meta.env.VITE_RPC_TARGET || 'https://rpc.ankr.com/eth',
          displayName: import.meta.env.VITE_CHAIN_NAME || 'Ethereum Mainnet',
          blockExplorer: import.meta.env.VITE_BLOCK_EXPLORER || 'https://etherscan.io/',
          ticker: import.meta.env.VITE_TICKER || 'ETH',
          tickerName: import.meta.env.VITE_TICKER_NAME || 'Ethereum',
        },
        uiConfig: {
          theme: 'light',
          loginMethodsOrder: ['google'],
          appLogo: import.meta.env.VITE_APP_LOGO || '',
          appName: import.meta.env.VITE_APP_NAME || 'Study4Me',
        },
      }

      // Initialize Web3Auth
      this.web3auth = new Web3Auth(config)
      await this.web3auth.initModal()

      // Store instance and update state
      web3AuthInstance.set(this.web3auth)
      web3AuthActions.setInitialized(true)

      // Check if user is already connected
      if (this.web3auth.connected) {
        await this.updateUserState()
      }

      console.log('Web3Auth initialized successfully')
      return true

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to initialize Web3Auth'
      console.error('Web3Auth initialization error:', errorMessage)
      web3AuthActions.setError(errorMessage)
      return false

    } finally {
      this.isInitializing = false
      web3AuthActions.setLoading(false)
    }
  }

  /**
   * Connect with specified login provider
   * @param provider - Social login provider
   * @returns Promise<{success: boolean, user?: UserInfo, provider?: IProvider}>
   */
  async login(provider: LoginProvider = 'google'): Promise<{
    success: boolean
    user?: UserInfo
    provider?: IProvider
    error?: string
  }> {
    try {
      // Ensure Web3Auth is initialized
      if (!this.web3auth) {
        const initialized = await this.initialize()
        if (!initialized) {
          return { success: false, error: 'Failed to initialize Web3Auth' }
        }
      }

      web3AuthActions.setLoading(true)
      web3AuthActions.clearError()

      // Connect with specified provider
      const web3authProvider = await this.web3auth!.connect({
        loginProvider: provider,
      })

      if (!web3authProvider) {
        return { success: false, error: 'Failed to connect with provider' }
      }

      // Get user information
      const user = await this.web3auth!.getUserInfo()
      
      // Update state
      web3AuthActions.setConnected(user, web3authProvider)

      console.log(`Successfully connected with ${provider}:`, user)
      return { 
        success: true, 
        user, 
        provider: web3authProvider 
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : `Failed to login with ${provider}`
      console.error('Login error:', errorMessage)
      web3AuthActions.setError(errorMessage)
      return { success: false, error: errorMessage }

    } finally {
      web3AuthActions.setLoading(false)
    }
  }

  /**
   * Disconnect and logout user
   * @returns Promise<boolean> - Success status
   */
  async logout(): Promise<boolean> {
    try {
      if (!this.web3auth) {
        console.warn('Web3Auth not initialized')
        return false
      }

      web3AuthActions.setLoading(true)
      web3AuthActions.clearError()

      // Logout from Web3Auth
      await this.web3auth.logout()
      
      // Update state
      web3AuthActions.setDisconnected()

      console.log('Successfully logged out')
      return true

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to logout'
      console.error('Logout error:', errorMessage)
      web3AuthActions.setError(errorMessage)
      return false

    } finally {
      web3AuthActions.setLoading(false)
    }
  }

  /**
   * Get current user information
   * @returns Promise<UserInfo | null>
   */
  async getCurrentUser(): Promise<UserInfo | null> {
    try {
      if (!this.web3auth?.connected) {
        return null
      }

      return await this.web3auth.getUserInfo()
    } catch (error) {
      console.error('Error getting current user:', error)
      return null
    }
  }

  /**
   * Get current provider for blockchain interactions
   * @returns IProvider | null
   */
  getCurrentProvider(): IProvider | null {
    return this.web3auth?.provider || null
  }

  /**
   * Check if user is currently connected
   * @returns boolean
   */
  isConnected(): boolean {
    return this.web3auth?.connected || false
  }

  /**
   * Get Web3Auth instance
   * @returns Web3Auth | null
   */
  getInstance(): Web3Auth | null {
    return this.web3auth
  }

  /**
   * Update user state from Web3Auth
   * @private
   */
  private async updateUserState(): Promise<void> {
    try {
      if (!this.web3auth?.connected) {
        web3AuthActions.setDisconnected()
        return
      }

      const user = await this.web3auth.getUserInfo()
      const provider = this.web3auth.provider

      web3AuthActions.setConnected(user, provider)
    } catch (error) {
      console.error('Error updating user state:', error)
      web3AuthActions.setDisconnected()
    }
  }
}

// Create singleton instance
export const web3AuthService = new Web3AuthService()

// Export service methods for convenience
export const {
  initialize: initializeWeb3Auth,
  login: loginWithWeb3Auth,
  logout: logoutFromWeb3Auth,
  getCurrentUser,
  getCurrentProvider,
  isConnected: isWeb3AuthConnected,
  getInstance: getWeb3AuthInstance
} = web3AuthService