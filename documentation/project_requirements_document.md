# Project Requirements Document (PRD)

**Project:** Study4Me\
**Document Type:** Project Requirements Document

## 1. Project Overview

Study4Me is a Web3-powered study companion that lets students and self-learners gather information from YouTube lectures, PDFs, images, and web articles, then instantly turn that body of content into a browsable, queryable Knowledge Graph. By pinning all assets to decentralized storage (IPFS & ARWeave) and gating access via an NFT pass, Study4Me ensures data permanence, user ownership, and a seamless blockchain-native login experience.

Beyond static documents, users can ask natural-language questions against their custom “Study Topics” and get precise answers with citations, visualize concept connections via LightRag graphs, and generate downloadable audio summaries (MP3) through ElevenLabs. In short, Study4Me solves the fragmentation problem—where learners jump between videos, slides, and articles—by unifying and structuring diverse materials into one interactive learning hub.

**Key Objectives / Success Criteria**

*   Reliable ingestion of YouTube transcripts, documents, images, and web pages
*   Generation of meaningful Knowledge Graphs with pan & zoom navigation
*   Natural-language query interface that returns accurate, context-backed answers
*   NFT-based access control with three months of study credits
*   Audio class export (MP3) for offline listening
*   User analytics dashboard for ingestion, queries, and audio downloads

## 2. In-Scope vs. Out-of-Scope

**In-Scope (Version 1)**

*   YouTube transcript extraction (Whisper)
*   Document/PDF ingestion via Docling, image OCR (Tesseract), web scraping (Trafilatura)
*   Decentralized storage on IPFS & ARWeave
*   Study Topic creation & management
*   Knowledge Graph generation (LightRag) with pan/zoom viewer
*   Natural-language query interface with answer citations (timestamps, document links)
*   Audio class synthesis & MP3 download (ElevenLabs)
*   Wallet-based authentication (Web3Auth/WalletConnect) with NFT gating on Base & Arbitrum
*   Built-in analytics (ingestions, queries, downloads)

**Out-of-Scope (Planned for Later Phases)**

*   Support for transcript extraction from non-YouTube or local videos
*   Graph node editing, filtering, or exporting beyond pan/zoom
*   Role-based permissions (admins vs. learners)
*   Subscription/payment UI beyond NFT + credit model
*   In-app audio playlist scheduling or streaming beyond basic playback/download
*   Mobile-native apps or offline mode
*   Third-party LLM training or fine-tuning

## 3. User Flow

New users arrive at the Study4Me landing page and are prompted to connect their Ethereum wallet via Web3Auth or WalletConnect. The system checks for a valid Study4Me NFT—if missing, it guides users through an on-chain purchase flow on Base or Arbitrum. Once ownership and initial credits (valid for three months) are confirmed, the user lands on the main dashboard showing existing Study Topics, credit balance, expiry date, and key metrics (total ingestions, queries, audio downloads).

From the dashboard, the user clicks **“New Topic”**, gives it a name (e.g., “Quantum Computing”), then inputs content by pasting YouTube URLs, uploading PDFs/docs, dragging image files for OCR, or pasting web page links. After submitting, the backend runs ingestion pipelines, pins processed assets to IPFS/Arweave, and displays storage hashes. When ready, the user hits **“Build Graph”** to generate a LightRag Knowledge Graph. The graph appears in a pan/zoom viewer. Next, they move to the **Query** tab, type questions like “What are the advantages of superconducting qubits?”, receive AI-generated answers with citations, and see the relevant nodes highlighted. Finally, they can generate an audio class, download the MP3, or review analytics in the account section.

## 4. Core Features

*   **Authentication & Access Control**\
    • Wallet login via Web3Auth/WalletConnect on Base & Arbitrum\
    • NFT ownership check & on-chain purchase flow\
    • Credit allocation & expiry tracking
*   **Content Ingestion**\
    • YouTube transcript extraction (Whisper)\
    • PDF/document parsing (Docling)\
    • Image OCR & captioning (Tesseract)\
    • Web page scraping & text cleaning (Trafilatura)\
    • Asset pinning to IPFS/Arweave
*   **Study Topic Management**\
    • Create, rename, delete topics\
    • Add/remove content sources\
    • View ingestion statuses & storage hashes
*   **Knowledge Graph Generation**\
    • LightRag analysis to extract entities & relationships\
    • Structured graph output with color-coded nodes by source\
    • Pan & zoom interactivity (no node editing)
*   **Query Interface**\
    • Natural-language question input\
    • Context-aware AI answers with citations (timestamps, docs)\
    • Highlighted nodes in graph viewer
*   **Audio Class Generation**\
    • ElevenLabs voice synthesis for summaries\
    • Downloadable MP3 files\
    • Basic in-app audio player
*   **Analytics Dashboard**\
    • Ingestion count, query frequency, audio downloads\
    • Credit usage & renewal reminders
*   **Decentralized Storage Integration**\
    • IPFS & Arweave pinning via backend services\
    • Display of content hashes & retrieval links

## 5. Tech Stack & Tools

*   **Frontend:**\
    • Svelte (SPA framework)\
    • Tailwind CSS (Neobrutalism styling)\
    • Web3Auth & WalletConnect (wallet-based auth)
*   **Backend:**\
    • Python & FastAPI\
    • Docling (document parsing)\
    • LightRag (Knowledge Graph)\
    • OpenAI Whisper (YouTube transcription)\
    • Tesseract OCR (images)\
    • Trafilatura (web scraping)\
    • ElevenLabs SDK (audio synthesis)\
    • Web3 libraries (ethers.js / web3.py)
*   **Storage & Infrastructure:**\
    • IPFS & ARWeave (decentralized storage)\
    • PostgreSQL or SQLite (metadata & user records)\
    • Redis (caching & job queue)\
    • Docker (containerization)
*   **AI Models & Protocols:**\
    • Whisper for ASR\
    • LightRag for graph creation\
    • GPT-4 via MCP connection for advanced queries
*   **Developer Tools:**\
    • VS Code (with Svelte & Python extensions)\
    • Git & GitHub (version control)\
    • CI/CD: GitHub Actions

## 6. Non-Functional Requirements

*   **Performance:**\
    • API (< 200 ms) for frontend calls (dashboard, auth)\
    • Query response (< 2 s) for simple questions\
    • Graph rendering (< 500 ms) on average browsers
*   **Security & Compliance:**\
    • HTTPS & TLS for all data in transit\
    • JWT or signed tokens for API auth\
    • Data encryption at rest for user metadata\
    • GDPR-style data deletion upon request
*   **Reliability & Scalability:**\
    • Horizontal scaling for ingestion pipelines\
    • Retry logic for IPFS pinning & blockchain calls
*   **Usability:**\
    • Mobile-responsive design\
    • Clear UI states (hover, active, disabled)\
    • High-contrast Neobrutalism palette for readability

## 7. Constraints & Assumptions

*   **Blockchain/Storage Dependencies:**\
    • ARWeave nodes and IPFS gateways remain available\
    • Base & Arbitrum networks are accessible for NFT checks
*   **Model Availability:**\
    • Whisper, LightRag, ElevenLabs APIs maintain uptime\
    • Adequate token quotas for transcription & synthesis
*   **User Assumptions:**\
    • All learners have a crypto wallet and basic blockchain literacy\
    • Users accept wallet-based onboarding (no email/password)
*   **File Size & Formats (to be defined later):**\
    • Max PDF size, image dimensions, acceptable MIME types

## 8. Known Issues & Potential Pitfalls

*   **YouTube API Rate Limits:**\
    • Mitigation: cache transcripts, implement exponential back-off
*   **OCR & Transcript Accuracy:**\
    • Mitigation: offer manual correction interface in future versions
*   **Decentralized Storage Latency:**\
    • Mitigation: local caching of IPFS content and status indicators
*   **Blockchain Confirmation Delays:**\
    • Mitigation: show pending states and refresh buttons for NFT checks
*   **AI Answer Hallucinations:**\
    • Mitigation: always display source citations (timestamps, doc links)

This PRD serves as the single source of truth for all subsequent technical documents (Tech Stack, Frontend Guidelines, Backend Structure, App Flow, File Structure, etc.). It contains all critical functional and non-functional requirements, constraints, and known risks—ensuring that the AI model and future teams can execute Study4Me without ambiguity.
