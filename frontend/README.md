# Study4Me Frontend

A Neobrutalist-styled frontend built with Svelte, Vite, and Tailwind CSS for the Study4Me blockchain-gated study platform.

## Features

- **Neobrutalist Design**: Bold colors, thick borders, high contrast styling
- **Responsive Layout**: Mobile-first design with Tailwind breakpoints
- **Component-Based Architecture**: Reusable Svelte components
- **Web3Auth Integration**: Social authentication with Google
- **Blockchain Wallet Support**: WalletConnect integration for crypto wallets
- **Type-Safe**: Full TypeScript support
- **Modern Tooling**: Vite for fast development and building

## Tech Stack

- **Framework**: Svelte 5
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom Neobrutalism theme
- **Routing**: svelte-spa-router
- **Language**: TypeScript
- **State Management**: Svelte stores
- **Authentication**: Web3Auth v10+ for social login
- **Wallet Connection**: WalletConnect integration

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Button.svelte
│   ├── Card.svelte
│   ├── Input.svelte
│   ├── Navbar.svelte
│   ├── WalletModal.svelte    # Web3Auth wallet connection modal
│   └── GraphViewer.svelte
├── pages/              # Page components
│   ├── Dashboard.svelte
│   ├── TopicCreation.svelte
│   ├── TopicDetail.svelte
│   └── Settings.svelte
├── stores/             # Svelte stores for state management
│   ├── auth.ts
│   ├── topicStore.ts
│   ├── uiStore.ts
│   └── web3AuthStore.ts      # Web3Auth state management
├── lib/                # Service layers and utilities
│   ├── web3AuthService.ts    # Web3Auth integration service
│   ├── api.ts
│   ├── web3.ts
│   └── ipfs.ts
├── App.svelte         # Main app component
├── main.ts            # Entry point
└── app.css            # Global styles and Tailwind imports
```

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Web3Auth Client ID (get from [Web3Auth Dashboard](https://dashboard.web3auth.io/))

### Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   ```bash
   cp .env .env.local
   # Edit .env.local with your actual Web3Auth client ID
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Build for production**:
   ```bash
   npm run build
   ```

5. **Preview production build**:
   ```bash
   npm run preview
   ```

## Design System

### Colors
- **Primary Background**: #FFF200 (Yellow)
- **Accent Blue**: #0050FF (Electric Blue)
- **Accent Red**: #FF2C2C (Red Alert)
- **Secondary Text**: #222222 (Dark Gray)
- **Borders & Text**: #000000 (Black)

### Typography
- **Headings**: IBM Plex Mono, JetBrains Mono, Space Mono
- **Body Text**: Inter, DM Sans, Lexend Deca
- **Code**: JetBrains Mono

### Components
- **neo-card**: White cards with black borders
- **neo-button**: Blue buttons that turn red on hover
- **neo-input**: Form inputs with thick black borders

## Development Guidelines

1. **Component Structure**: Keep components small and focused
2. **Styling**: Use Tailwind utility classes, avoid custom CSS
3. **State Management**: Use Svelte stores for global state
4. **Accessibility**: Include proper ARIA labels and keyboard navigation
5. **Responsiveness**: Mobile-first approach with responsive utilities

## Environment Variables

Create a `.env` file with the following variables:

### Required Variables
```bash
# Web3Auth Configuration (Required)
VITE_WEB3AUTH_CLIENT_ID=your_client_id_from_dashboard

# Web3Auth Network (Optional - defaults to SAPPHIRE_DEVNET)
VITE_WEB3AUTH_NETWORK=SAPPHIRE_DEVNET  # or SAPPHIRE_MAINNET for production

# Blockchain Configuration (Optional - defaults provided)
VITE_CHAIN_ID=0x1
VITE_RPC_TARGET=https://rpc.ankr.com/eth
VITE_CHAIN_NAME=Ethereum Mainnet
VITE_BLOCK_EXPLORER=https://etherscan.io/
VITE_TICKER=ETH
VITE_TICKER_NAME=Ethereum

# App Branding (Optional)
VITE_APP_NAME=Study4Me
VITE_APP_LOGO=https://your-app-logo.com/logo.png

# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_PINATA_JWT=your_pinata_jwt_token
```

### Getting Your Web3Auth Client ID
1. Visit [Web3Auth Dashboard](https://dashboard.web3auth.io/)
2. Create a new project or select existing one
3. Copy the Client ID from your project settings
4. Add it to your `.env` file as `VITE_WEB3AUTH_CLIENT_ID`

## Web3Auth Integration

### Supported Authentication Providers
- **Google** - OAuth 2.0 authentication

### Authentication Flow
1. User clicks "Connect Wallet" in navigation
2. Modal opens with Web3Auth social login options
3. User selects Google authentication
4. Web3Auth handles secure authentication
5. User receives wallet and profile information
6. App dispatches connection event with user data

### Usage in Components
```typescript
import { web3AuthState, isWeb3AuthConnected, web3AuthUser } from '../stores/web3AuthStore'
import { loginWithWeb3Auth, logoutFromWeb3Auth } from '../lib/web3AuthService'

// Check if user is connected
$: isConnected = $isWeb3AuthConnected

// Get current user info
$: currentUser = $web3AuthUser

// Login with specific provider
await loginWithWeb3Auth('google')

// Logout
await logoutFromWeb3Auth()
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Run Svelte type checking
- `npm run test` - Run Playwright E2E tests
- `npm run test:ui` - Run tests with Playwright UI

## Contributing

1. Follow the Neobrutalist design principles
2. Maintain component modularity
3. Use TypeScript for type safety
4. Test components before committing
5. Keep accessibility in mind