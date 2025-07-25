import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { nodePolyfills } from 'vite-plugin-node-polyfills'

export default defineConfig({
  plugins: [
    svelte(),
    nodePolyfills({
      exclude: ['fs'],
      globals: {
        Buffer: true,
        global: true,
        process: true,
      },
    }),
  ],
  server: {
    port: 3000
  },
  css: {
    postcss: './postcss.config.js'
  },
  define: {
    global: 'globalThis',
  },
  optimizeDeps: {
    include: ['@web3auth/modal', '@web3auth/base', '@reown/appkit', '@reown/appkit-adapter-wagmi'],
  },
  resolve: {
    alias: {
      process: 'process/browser',
      buffer: 'buffer',
    },
  },
})