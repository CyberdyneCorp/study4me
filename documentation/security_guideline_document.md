# Security Architecture Overview for Study4Me

This document maps core security controls—derived from the secure‐by‐design principles—onto the Study4Me architecture and features.

---

## 1. Authentication & Access Control

- **Wallet-Based Auth (Web3Auth / WalletConnect)**
  - Verify wallet signatures server-side to authenticate users.
  - After login, issue a short-lived JWT (HS256 or RS256) containing wallet address and NFT ownership claim.
  - Enforce token `exp`, audience (`aud`), and issuer (`iss`) checks on every request.

- **NFT Access Gate**
  - On login and on credit‐consuming endpoints, check on-chain ownership of the access NFT via a secure RPC provider.
  - Implement server‐side RBAC: “user” role can ingest/query; “admin” role can manage system.

- **Session & Token Security**
  - Store JWT in an HttpOnly, Secure, `SameSite=Lax` cookie to mitigate XSS.
  - Implement token revocation list for logout or NFT burn events.
  - Limit token lifetime (e.g., 15 min) plus refresh tokens (rotated, stored in secure HTTP cookie, invalidated on logout).

---

## 2. Input Handling & Processing

- **Content Ingestion Pipeline**
  - Whitelist allowed URL domains for YouTube and scraped web pages.
  - Validate PDF and document uploads by MIME type and file signature; reject if mismatch.
  - Sanitize filenames and reject path traversal patterns.

- **OCR & Transcript Extraction**
  - Treat Tesseract and Whisper outputs as untrusted: run context-aware sanitization before storage and graph generation.

- **Database & Storage**
  - Use parameterized queries (e.g., SQLAlchemy or FastAPI’s ORM) to avoid injection.
  - Escape any user‐supplied metadata before returning in API responses (template encoding or JSON encoding).

---

## 3. Data Protection & Privacy

- **Transport Encryption**
  - Enforce HTTPS/TLS 1.2+ on all frontend ↔ backend and backend ↔ IPFS/Arweave gateways.

- **At‐Rest Protection**
  - Encrypt sensitive metadata (e.g., user profile, credit balances) in the database with AES-256.
  - Use decentralized storage (IPFS/Arweave) only for encrypted payloads; manage keys securely.

- **Secrets Management**
  - Store API keys (ElevenLabs, blockchain RPC endpoints) in a managed vault (e.g., AWS Secrets Manager).
  - Load secrets at runtime via environment variables, with no hardcoding in source.

- **PII Handling**
  - Do not log wallet private data or transcripts that may contain PII.
  - Mask or truncate any user‐identifiable data in logs and analytics.

---

## 4. API & Service Security

- **Rate Limiting & Throttling**
  - Apply per-user and per-endpoint rate limits (e.g., 100 requests/minute) using a reverse‐proxy or FastAPI middleware.

- **CORS**
  - Restrict `Access-Control-Allow-Origin` to the official Study4Me SPA domain only.

- **Versioned Endpoints**
  - Prefix critical routes with `/v1/` and design backward‐compatible changes via `/v2/` when needed.

- **HTTP Methods**
  - Enforce GET for reads, POST for ingest and queries, PUT/PATCH for updates, DELETE for removals.

---

## 5. Web Application Security Hygiene

- **Content Security Policy (CSP)**
  - Include a strict CSP header limiting scripts/styles to self and approved CDNs (with SRI hashes).

- **Security Headers**
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: no-referrer-when-downgrade`

- **CSRF Protection**
  - Use double-submit cookie or synchronizer tokens for state-modifying POST/PUT/DELETE requests.

---

## 6. Infrastructure & Deployment

- **Server Hardening**
  - Use containerized FastAPI service with a non-root user.
  - Disable unused OS services; restrict inbound ports to 80/443.

- **TLS Configuration**
  - Enable only TLS 1.2+ with strong cipher suites (ECDHE, AES-GCM).

- **Logging & Monitoring**
  - Centralize logs in a secure SIEM; redact sensitive fields.
  - Alert on failed login spikes, API abuse, or infrastructure anomalies.

- **CI/CD Security**
  - Scan dependencies for vulnerabilities (Snyk, Dependabot, or similar).
  - Enforce branch protection and require review for PRs touching security-critical code.

---

## 7. Dependency Management

- **Lockfiles**
  - Commit `requirements.txt` (with pinned versions) and `Pipfile.lock` for deterministic builds.

- **Regular Updates**
  - Schedule monthly dependency audits and patch cycles.

- **Minimal Footprint**
  - Remove unused libraries (e.g., slim Docker image) to reduce attack surface.

---

## Project Folder Structure (Suggested)

```
├── backend/
│   ├── app/
│   │   ├── api/                 # Versioned FastAPI routers
│   │   ├── core/                # Config, security, constants
│   │   ├── models/              # Pydantic + ORM models
│   │   ├── services/            # Ingestion, graph, TTS
│   │   ├── auth/                # JWT, wallet, NFT checks
│   │   └── main.py              # FastAPI initialization + middleware
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Svelte UI components
│   │   ├── lib/                 # Stores, helpers, web3 connectors
│   │   ├── routes/              # Svelte pages
│   │   └── app.css              # Tailwind + custom styles
│   └── package.json
├── infra/
│   ├── terraform/               # (optional) cloud infra as code
│   └── nginx/                   # Reverse‐proxy + TLS config
└── docs/
    └── security-guidelines.md   # This document
```

---

By embedding these controls from day one, Study4Me will maintain a strong security posture while delivering a seamless, decentralized study experience. Feel free to review and flag any area for deeper threat modeling or code‐level design discussions.
