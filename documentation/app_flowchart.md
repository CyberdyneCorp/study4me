flowchart TD
  A[Start authentication]
  B[Connect wallet via Web3Auth or WalletConnect]
  C[NFT verification]
  D{NFT owned?}
  E[Prompt purchase NFT]
  F[Dashboard overview study topics credits analytics]
  G[Create study topic]
  H[Ingest content via Whisper Docling Tesseract Trafilatura]
  I[Store data on IPFS and Arweave]
  J[Generate knowledge graph via LightRag]
  K[Query interface natural language]
  L[Generate audio class via ElevenLabs]
  M[Download MP3 audio]
  N[Save key answers or flashcards]
  
  A --> B
  B --> C
  C --> D
  D -- Yes --> F
  D -- No --> E
  E --> C
  F --> G
  G --> H
  H --> I
  I --> J
  J --> K
  K --> L
  L --> M
  M --> N