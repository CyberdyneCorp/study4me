/**
 * Web3Auth Store - Manages Web3Auth authentication state
 * 
 * This store provides centralized state management for Web3Auth integration:
 * - Web3Auth instance management
 * - User authentication state
 * - Connection status tracking
 * - Error handling
 */

import { writable, type Writable } from 'svelte/store'
import type { Web3Auth } from '@web3auth/modal'
import type { IProvider } from '@web3auth/base'

// User information interface
export interface UserInfo {
  email?: string
  name?: string
  profileImage?: string
  aggregateVerifier?: string
  verifier: string
  verifierId: string
  typeOfLogin: string
  dappShare?: string
  oAuthIdToken?: string
  oAuthAccessToken?: string
}

// Authentication state interface
export interface Web3AuthState {
  isInitialized: boolean
  isConnected: boolean
  isLoading: boolean
  user: UserInfo | null
  provider: IProvider | null
  error: string | null
}

// Initial state
const initialState: Web3AuthState = {
  isInitialized: false,
  isConnected: false,
  isLoading: false,
  user: null,
  provider: null,
  error: null
}

// Create writable stores
export const web3AuthInstance: Writable<Web3Auth | null> = writable(null)
export const web3AuthState: Writable<Web3AuthState> = writable(initialState)

// Store actions for updating state
export const web3AuthActions = {
  // Set initialization state
  setInitialized: (initialized: boolean) => {
    web3AuthState.update(state => ({
      ...state,
      isInitialized: initialized,
      error: initialized ? null : state.error
    }))
  },

  // Set loading state
  setLoading: (loading: boolean) => {
    web3AuthState.update(state => ({
      ...state,
      isLoading: loading
    }))
  },

  // Set connection state with user and provider
  setConnected: (user: UserInfo | null, provider: IProvider | null) => {
    web3AuthState.update(state => ({
      ...state,
      isConnected: !!(user && provider),
      user,
      provider,
      error: null
    }))
  },

  // Set disconnected state
  setDisconnected: () => {
    web3AuthState.update(state => ({
      ...state,
      isConnected: false,
      user: null,
      provider: null,
      error: null
    }))
  },

  // Set error state
  setError: (error: string) => {
    web3AuthState.update(state => ({
      ...state,
      error,
      isLoading: false
    }))
  },

  // Clear error state
  clearError: () => {
    web3AuthState.update(state => ({
      ...state,
      error: null
    }))
  },

  // Reset entire state
  reset: () => {
    web3AuthState.set(initialState)
    web3AuthInstance.set(null)
  }
}

// Derived stores for easier access to specific state properties
export const isWeb3AuthInitialized = writable(false)
export const isWeb3AuthConnected = writable(false)
export const isWeb3AuthLoading = writable(false)
export const web3AuthUser = writable<UserInfo | null>(null)
export const web3AuthError = writable<string | null>(null)

// Subscribe to main state and update derived stores
web3AuthState.subscribe(state => {
  isWeb3AuthInitialized.set(state.isInitialized)
  isWeb3AuthConnected.set(state.isConnected)
  isWeb3AuthLoading.set(state.isLoading)
  web3AuthUser.set(state.user)
  web3AuthError.set(state.error)
})