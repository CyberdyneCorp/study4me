# Tech Stack Document for Study4Me

This document explains, in everyday language, the technology choices behind Study4Me—a study tool that turns videos, documents, images, and web pages into interactive knowledge graphs and audio classes. Every component has been chosen to ensure reliability, performance, security, and an engaging user experience, even if you don’t have a technical background.

## 1. Frontend Technologies

Our user interface (what you see and click on) is built as a Single Page Application (SPA), meaning it feels fast and smooth—pages update instantly without full reloads.

*   **Svelte**

    *   A modern JavaScript framework that compiles your code into tiny, super-fast JavaScript bundles
    *   Delivers snappy interactions and minimal load times

*   **Tailwind CSS**

    *   A utility-first styling tool that lets us rapidly build layouts and styles by composing small CSS classes
    *   Ensures a consistent look and feel without writing custom CSS from scratch

*   **Neobrutalism Design Style**

    *   Bold, high-contrast color blocks and thick borders for a playful yet readable interface
    *   Monospaced or retro-tech fonts to reinforce the “AI + crypto” vibe
    *   Visible UI states (hover, active) to give clear feedback on user actions

*   **Authentication UI**

    *   **Web3Auth** and **WalletConnect** integrations let you sign in with your crypto wallet—no username/password needed
    *   Quick on-chain NFT checks grant or deny access based on your ownership

These choices combine to provide a vibrant, responsive, and secure front-end experience that invites exploration and keeps students and blockchain enthusiasts engaged.

## 2. Backend Technologies

The backend powers all the heavy lifting: ingesting content, building knowledge graphs, handling queries, and generating audio classes.

*   **Python + FastAPI**

    *   FastAPI is a modern web framework for building APIs quickly and with automatic documentation
    *   Python’s ecosystem offers libraries for every step of our data pipeline

*   **Docling**

    *   Parses and extracts structured text from PDFs and document files
    *   Handles tables, headings, and rich formatting automatically

*   **Whisper (OpenAI)**

    *   Converts YouTube speech into accurate, timestamped transcripts
    *   Captures speaker nuances so you can jump to the exact moment you need

*   **Tesseract OCR**

    *   Reads text from uploaded images, diagrams, and screenshots

*   **Trafilatura**

    *   Cleans and extracts text from arbitrary web pages, removing ads, scripts, and clutter

*   **LightRAG**

    *   Builds a Knowledge Graph by identifying entities (concepts) and relationships from all ingested content
    *   Produces a structured, interactive map of the subject matter

*   **MCP (Model Connector Protocol)**

    *   Exposes a standard interface so other AI models can plug in and query your data or knowledge graphs

*   **ElevenLabs**

    *   Synthesizes high-quality audio summaries that users can download as MP3 files for offline listening

Together, these tools automate the transformation of raw content into searchable text, structured concepts, and audio lessons.

## 3. Infrastructure and Deployment

To keep Study4Me reliable, scalable, and easy to update, we use industry-standard infrastructure and workflows.

*   **Version Control: Git & GitHub**

    *   All code is stored in a GitHub repository, enabling easy collaboration and code reviews

*   **CI/CD: GitHub Actions**

    *   Automatically runs tests and deploys updates whenever new code is merged
    *   Ensures changes don’t break existing features

*   **Containerization: Docker**

    *   Packages the backend (and any supporting services) into containers for consistent behavior across environments

*   **Hosting & Deployment**

    *   **Frontend**: Deployed on a CDN-backed platform (e.g., Vercel or Netlify) for instant global delivery of static assets
    *   **Backend**: Hosted as Docker containers on a cloud provider (e.g., AWS ECS, DigitalOcean Apps, or similar) behind HTTPS

*   **Decentralized Storage**

    *   **IPFS** and **Arweave** automatically store and pin all ingested files and generated assets
    *   Guarantees data permanence, censorship resistance, and user ownership

These infrastructure choices mean the app can grow—from a handful of users to thousands—without major reconfiguration or downtime.

## 4. Third-Party Integrations

Study4Me leverages specialized services so we don’t have to reinvent the wheel.

*   **YouTube Data API** (for video metadata and streaming links)
*   **Whisper API** (for video transcript extraction)
*   **Docling** (for document parsing)
*   **Tesseract OCR** (for image text extraction)
*   **Trafilatura** (for web page scraping)
*   **LightRAG** (for Knowledge Graph creation)
*   **ElevenLabs** (for voice synthesis)
*   **Web3Auth** & **WalletConnect** (for wallet-based login and NFT gating)
*   **ARWeave** & **IPFS** (for decentralized storage)
*   **Analytics**: Custom backend logging plus optional integration with tools like Google Analytics or a privacy-first alternative (Matomo) to track ingestion counts, query usage, and audio downloads

These integrations speed up development and bring best-in-class capabilities to end users.

## 5. Security and Performance Considerations

We’ve built Study4Me with both security and a smooth user experience in mind.

Security Measures

*   All traffic runs over HTTPS to protect data in transit
*   Wallet-based authentication (Web3Auth/WalletConnect) removes passwords and ties access directly to on-chain identity
*   NFT checks before granting access ensure only authorized students can use the service
*   Input validation and sanitization on uploads and scraped HTML prevent malicious content from entering our system
*   Decentralized storage (IPFS/Arweave) uses content-addressing and cryptographic hashes for tamper-proof persistence

Performance Optimizations

*   Asynchronous ingestion pipelines (via FastAPI background tasks) so users can continue working while content processes
*   Cached transcripts and pre-computed graph structures to speed up repeated queries
*   Static file hosting on a CDN for instant frontend load times
*   Docker container resource limits and auto-scaling rules on the backend to handle spikes in usage without manual intervention

## 6. Conclusion and Overall Tech Stack Summary

Study4Me brings together a carefully selected set of technologies to fulfill our mission: turning scattered videos, documents, images, and web pages into an interactive, decentralized, and AI-powered learning environment. Here’s a quick recap:

*   **Frontend**: Svelte + Tailwind CSS in a Neobrutalist style, wallet-based login (Web3Auth/WalletConnect) on Base & Arbitrum
*   **Backend**: Python + FastAPI powering Docling, Whisper, Tesseract, Trafilatura, LightRAG, and ElevenLabs
*   **Storage**: IPFS & Arweave for permanent, tamper-proof file hosting
*   **Infrastructure**: GitHub (version control & CI/CD), Docker containers, CDN hosting for static files, cloud hosting for APIs
*   **Integrations**: YouTube Data API, analytics tools, and a standard MCP interface for external AI models

This stack aligns perfectly with our goals of openness, permanence, and seamless AI + crypto integration. It delivers a fast, secure, and engaging study experience that scales with our user base and remains true to blockchain-driven ownership and decentralization principles.

With this foundation in place, Study4Me is ready to support thousands of learners, unlock new AI integrations, and redefine how we interact with knowledge in a decentralized web.
