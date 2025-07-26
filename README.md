# Study4Me

A Web3-powered study companion that transforms YouTube lectures, PDFs, images, and web articles into an interactive, queryable Knowledge Graph with decentralized storage and NFT-gated access.

## Overview

Study4Me solves the fragmentation problem where learners jump between videos, slides, and articles by unifying diverse materials into one interactive learning hub. Users can gather content from multiple sources, generate visual Knowledge Graphs, ask natural-language questions with precise citations, and create downloadable audio summaries.

### Key Features

- **Multi-Source Content Ingestion**: YouTube transcripts, PDFs, images (OCR), and web articles with topic-specific storage
- **Topic-Specific Knowledge Graphs**: Individual LightRAG instances per study topic with isolated storage
- **Dual Query System**: LightRAG for knowledge graphs OR ChatGPT with full context for content-only topics
- **Study Topics Management**: Create and manage isolated study topics with configurable processing modes
- **Token-Aware Content Analysis**: Accurate token counting with tiktoken for content and cost estimation
- **AI-Powered Q&A**: Intelligent query routing with enhanced response metadata and source citations
- **Audio Class Generation**: ElevenLabs voice synthesis for downloadable MP3 summaries
- **Web3 Authentication**: Wallet-based login with NFT access control on Base & Arbitrum
- **Decentralized Storage**: Content permanently stored on IPFS & ARWeave
- **Analytics Dashboard**: Track ingestions, queries, and downloads

## Tech Stack

### Frontend
- **Svelte**: SPA framework
- **Tailwind CSS**: Neobrutalism styling
- **Web3Auth & WalletConnect**: Wallet authentication

### Backend
- **Python & FastAPI**: API server
- **Docling**: Document parsing
- **LightRag**: Knowledge Graph generation
- **OpenAI Whisper**: YouTube transcription
- **Tesseract OCR**: Image text extraction
- **Trafilatura**: Web scraping
- **ElevenLabs SDK**: Audio synthesis

### Storage & Infrastructure
- **IPFS & ARWeave**: Decentralized storage
- **PostgreSQL/SQLite**: Metadata & user records
- **Redis**: Caching & job queue
- **Docker**: Containerization

## Project Structure

```
study4me/
├── frontend/          # Svelte application
├── backend/           # FastAPI server
├── documentation/     # Project requirements and specs
└── README.md         # This file
```

## Getting Started

### Prerequisites
- Ethereum wallet (MetaMask, WalletConnect compatible)
- Study4Me NFT (available on Base & Arbitrum networks)
- Node.js 18+ and Python 3.9+
- Reown project ID (for WalletConnect integration)

### User Flow
1. **Connect Wallet**: Login with Web3Auth or WalletConnect
2. **NFT Verification**: System checks for valid Study4Me NFT ownership
3. **Create Study Topic**: Name your learning subject (e.g., "Quantum Computing")
4. **Add Content**: Input YouTube URLs, upload PDFs, add images, or paste web links
5. **Build Knowledge Graph**: Generate interactive LightRag visualization
6. **Query & Learn**: Ask questions and get AI answers with source citations
7. **Generate Audio**: Create MP3 summaries for offline listening

## Features in Detail

### Content Ingestion
- YouTube transcript extraction via Whisper
- PDF/document parsing with Docling
- Image OCR and captioning using Tesseract
- Web page content extraction via Trafilatura
- Automatic pinning to IPFS/ARWeave for permanence

### Knowledge Graph
- Entity and relationship extraction using LightRag
- Color-coded nodes by content source
- Interactive pan & zoom navigation
- Real-time highlighting during Q&A sessions

### Query Interface
- Natural language question processing
- Context-aware AI responses
- Source citations with timestamps and document links
- Graph node highlighting for visual context

### Access Control
- NFT-based authentication on Base & Arbitrum
- Three-month credit allocation per NFT
- Wallet-native onboarding (no email/password required)

## Performance Targets

- **API Response**: < 200ms for dashboard and auth calls
- **Query Response**: < 2s for simple questions
- **Graph Rendering**: < 500ms on average browsers

## Security

- HTTPS/TLS for all data transmission
- JWT/signed tokens for API authentication
- Data encryption at rest for user metadata
- GDPR-compliant data deletion

## Development

The project is structured as a monorepo with separate frontend and backend applications. See individual directories for specific setup instructions.

### Reown AppKit Setup

Study4Me uses Reown AppKit (formerly WalletConnect AppKit) for wallet connections. Follow these steps to configure it:

#### 1. Get a Reown Project ID
1. Visit [Reown Cloud](https://cloud.reown.com/)
2. Create a new project or use an existing one
3. Copy your Project ID from the dashboard

#### 2. Environment Configuration
Create a `.env` file in the `frontend/` directory:

```bash
# Reown AppKit Configuration
VITE_REOWN_PROJECT_ID=your_project_id_here
VITE_REOWN_APP_NAME=Study4Me
VITE_REOWN_APP_DESCRIPTION=Blockchain-gated study platform
VITE_REOWN_APP_URL=https://study4me.com
VITE_REOWN_APP_ICON=https://study4me.com/icon.png
```

#### 3. Supported Networks
The AppKit is configured for:
- **Ethereum Mainnet** (default)
- **Arbitrum**
- **Polygon**

#### 4. Featured Wallets
Pre-configured wallet integrations include:
- MetaMask
- Coinbase Wallet
- Trust Wallet
- Bitget Wallet

#### 5. Implementation Details
- **Service**: `frontend/src/lib/appkitService.ts` - Main AppKit integration
- **Store**: `frontend/src/stores/appKitStore.ts` - State management
- **Component**: `frontend/src/components/WalletModal.svelte` - UI integration

#### 6. Key Features
- QR code modal for mobile wallet connections
- Multi-chain support with network switching
- Connection state management
- Error handling and logging
- Custom theming with neobrutalism design

## License

[License information to be added]

## Contributing

[Contributing guidelines to be added]