import { writable } from 'svelte/store'

export interface AuthState {
  isConnected: boolean
  walletAddress: string | null
  hasNFT: boolean
  isLoading: boolean
}

const initialState: AuthState = {
  isConnected: false,
  walletAddress: null,
  hasNFT: false,
  isLoading: false
}

export const authStore = writable<AuthState>(initialState)

export const authActions = {
  setLoading: (loading: boolean) => {
    authStore.update(state => ({ ...state, isLoading: loading }))
  },
  
  connectWallet: async (address: string) => {
    authStore.update(state => ({
      ...state,
      isConnected: true,
      walletAddress: address,
      isLoading: false
    }))
  },
  
  setNFTStatus: (hasNFT: boolean) => {
    authStore.update(state => ({ ...state, hasNFT }))
  },
  
  disconnect: () => {
    authStore.set(initialState)
  }
}