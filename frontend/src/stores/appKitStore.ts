/**
 * Reown AppKit Store - Manages AppKit wallet connection state
 * 
 * This store provides centralized state management for Reown AppKit integration:
 * - AppKit instance management
 * - Wallet connection state
 * - Loading and error states
 * - Chain and account information
 */

import { writable, type Writable } from 'svelte/store'
import type { AppKit } from '@reown/appkit'

// Wallet information interface
export interface WalletInfo {
  isConnected: boolean
  address?: string
  chainId?: number
  balance?: string
}

// AppKit state interface
export interface AppKitState {
  isInitialized: boolean
  isLoading: boolean
  error: string | null
  walletInfo: WalletInfo
}

// Initial state
const initialWalletInfo: WalletInfo = {
  isConnected: false,
  address: undefined,
  chainId: undefined,
  balance: undefined
}

const initialState: AppKitState = {
  isInitialized: false,
  isLoading: false,
  error: null,
  walletInfo: initialWalletInfo
}

// Create writable stores
export const appKitInstance: Writable<AppKit | null> = writable(null)
export const appKitState: Writable<AppKitState> = writable(initialState)

// Store actions for updating state
export const appKitActions = {
  // Set initialization state
  setInitialized: (initialized: boolean) => {
    appKitState.update(state => ({
      ...state,
      isInitialized: initialized,
      error: initialized ? null : state.error
    }))
  },

  // Set loading state
  setLoading: (loading: boolean) => {
    appKitState.update(state => ({
      ...state,
      isLoading: loading
    }))
  },

  // Set wallet information
  setWalletInfo: (walletInfo: WalletInfo) => {
    appKitState.update(state => ({
      ...state,
      walletInfo,
      error: null
    }))
  },

  // Set connected state with wallet info
  setConnected: (address: string, chainId: number, balance?: string) => {
    appKitState.update(state => ({
      ...state,
      walletInfo: {
        isConnected: true,
        address,
        chainId,
        balance
      },
      error: null
    }))
  },

  // Set disconnected state
  setDisconnected: () => {
    appKitState.update(state => ({
      ...state,
      walletInfo: initialWalletInfo,
      error: null
    }))
  },

  // Set chain ID
  setChainId: (chainId: number) => {
    appKitState.update(state => ({
      ...state,
      walletInfo: {
        ...state.walletInfo,
        chainId
      }
    }))
  },

  // Set error state
  setError: (error: string) => {
    appKitState.update(state => ({
      ...state,
      error,
      isLoading: false
    }))
  },

  // Clear error state
  clearError: () => {
    appKitState.update(state => ({
      ...state,
      error: null
    }))
  },

  // Reset entire state
  reset: () => {
    appKitState.set(initialState)
    appKitInstance.set(null)
  }
}

// Derived stores for easier access to specific state properties
export const isAppKitInitialized = writable(false)
export const isAppKitLoading = writable(false)
export const appKitWalletInfo = writable<WalletInfo>(initialWalletInfo)
export const appKitError = writable<string | null>(null)

// Subscribe to main state and update derived stores
appKitState.subscribe(state => {
  isAppKitInitialized.set(state.isInitialized)
  isAppKitLoading.set(state.isLoading)
  appKitWalletInfo.set(state.walletInfo)
  appKitError.set(state.error)
})

// Additional derived stores for specific wallet properties
export const isWalletConnected = writable(false)
export const walletAddress = writable<string | undefined>(undefined)
export const walletChainId = writable<number | undefined>(undefined)
export const walletBalance = writable<string | undefined>(undefined)

// Subscribe to wallet info changes and update specific stores
appKitWalletInfo.subscribe(walletInfo => {
  isWalletConnected.set(walletInfo.isConnected)
  walletAddress.set(walletInfo.address)
  walletChainId.set(walletInfo.chainId)
  walletBalance.set(walletInfo.balance)
})