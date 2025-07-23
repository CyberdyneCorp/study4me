# Backend Structure Document

## 1. Backend Architecture

### Overview
The backend of Study4Me is built with Python and FastAPI, following a modular, service-oriented design. Each major function—content ingestion, processing, storage, and querying—is encapsulated in its own Python module, making the codebase easy to navigate and extend.

### Design Patterns and Frameworks
- **FastAPI** for request handling, dependency injection, and automatic API docs (OpenAPI).
- **Service Layer Pattern** to separate business logic from HTTP request handling.
- **Repository Pattern** to abstract database operations, making it easier to swap or upgrade storage solutions.
- **Task Queue (Celery/RabbitMQ)** for offloading heavy processing jobs (e.g., transcription, OCR, graph generation).

### Scalability, Maintainability, and Performance
- **Microservices-style modules** allow independent scaling of CPU-heavy tasks (transcription, OCR) and I/O-heavy tasks (database reads/writes, blockchain queries).
- **Asynchronous endpoints** (via FastAPI’s async support) for non-blocking I/O operations.
- **Task queue workers** can be scaled horizontally to meet demand spikes (e.g., batch ingestion of large PDFs).
- **Clear module boundaries** and dependency injection ensure new features can be added without touching unrelated code.

---

## 2. Database Management

### Technologies Used
- **Relational Database (PostgreSQL)** for core application data: users, NFT ownership status, study topics, ingestion jobs, analytics logs.
- **In-Memory Store (Redis)** for caching frequently accessed data (e.g., user sessions, token validations, rate limiting counters).
- **Decentralized Storage (IPFS & ARWeave)** for raw and processed study materials (video transcripts, PDF text, OCR results, knowledge graph JSON).

### Data Structure and Practices
- **Normalized relational tables** to avoid data duplication while maintaining referential integrity (e.g., a `users` table linked to `study_topics`).
- **JSONB columns** in PostgreSQL for flexible metadata (e.g., storing LightRag graph nodes/edges).
- **Caching layer (Redis)** sits in front of PostgreSQL for read-heavy endpoints like fetching the knowledge graph or analytics dashboard.
- **Data retention policies** to archive or delete expired credits and old analytics entries after a configurable period.

---

## 3. Database Schema

### Human-Readable Overview
- **Users**: wallet address, NFT ownership status, created timestamp.
- **NFTs**: token ID, network (Base or Arbitrum), linked user.
- **StudyTopics**: title, description, status (draft/processed), owner, creation date.
- **IngestionJobs**: type (YouTube, PDF, image, web scrape), status, timestamps, related study topic.
- **KnowledgeGraphs**: serialized graph data in JSON, linked study topic.
- **AudioSummaries**: file URL on IPFS/ARWeave, generation timestamp.
- **Analytics**: event type (ingest, query, download), user, study topic, timestamp.

### PostgreSQL Schema (SQL)
```sql
-- Users table
drop table if exists users cascade;
create table users (
  id serial primary key,
  wallet_address varchar(100) unique not null,
  nft_verified boolean default false,
  created_at timestamptz default now()
);

-- Study Topics
drop table if exists study_topics cascade;
create table study_topics (
  id serial primary key,
  user_id int references users(id),
  title text not null,
  description text,
  status varchar(20) default 'draft',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Ingestion Jobs
drop table if exists ingestion_jobs cascade;
create table ingestion_jobs (
  id serial primary key,
  topic_id int references study_topics(id),
  job_type varchar(20) not null,
  status varchar(20) default 'pending',
  payload jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Knowledge Graphs
drop table if exists knowledge_graphs cascade;
create table knowledge_graphs (
  id serial primary key,
  topic_id int references study_topics(id),
  graph_data jsonb not null,
  generated_at timestamptz default now()
);

-- Audio Summaries
drop table if exists audio_summaries cascade;
create table audio_summaries (
  id serial primary key,
  topic_id int references study_topics(id),
  file_url text not null,
  generated_at timestamptz default now()
);

-- Analytics
drop table if exists analytics cascade;
create table analytics (
  id serial primary key,
  user_id int references users(id),
  topic_id int references study_topics(id),
  event_type varchar(30) not null,
  metadata jsonb,
  occurred_at timestamptz default now()
);
```  

---

## 4. API Design and Endpoints

### Approach: RESTful with FastAPI
- **Standard HTTP verbs** (GET, POST, PUT, DELETE) for resource operations.
- **JWT-based authentication** for user sessions after wallet/NFT verification.
- **OpenAPI docs** automatically generated at `/docs`.

### Key Endpoints

1. **Authentication & NFT Verification**
   - POST `/api/auth/login` – User connects wallet via Web3Auth/WalletConnect; returns a challenge.
   - POST `/api/auth/verify` – Verifies NFT ownership on Base/Arbitrum; issues JWT.

2. **User & Dashboard**
   - GET `/api/users/me` – Fetch user profile and credit balance.
   - GET `/api/analytics` – Retrieve user-specific ingestion/query/download stats.

3. **Study Topics Management**
   - POST `/api/topics` – Create a new study topic.
   - GET `/api/topics` – List user’s topics.
   - GET `/api/topics/{topic_id}` – Get topic details and status.
   - DELETE `/api/topics/{topic_id}` – Remove a topic and related data.

4. **Content Ingestion**
   - POST `/api/topics/{topic_id}/ingest` – Submit a URL (YouTube/web), file upload (PDF/image).
   - GET `/api/ingest/jobs/{job_id}` – Check ingestion job status.

5. **Knowledge Graph Generation**
   - POST `/api/topics/{topic_id}/graphs` – Trigger graph creation (LightRag).
   - GET `/api/topics/{topic_id}/graphs` – Fetch the latest graph JSON.

6. **Query Interface**
   - POST `/api/topics/{topic_id}/query` – Submit a natural-language question; returns answer with citations.

7. **Audio Summary**
   - POST `/api/topics/{topic_id}/audio` – Generate MP3 via ElevenLabs.
   - GET `/api/topics/{topic_id}/audio` – Download generated MP3 link.

8. **Miscellaneous**
   - GET `/health` – Health check for load balancers/monitoring systems.

---

## 5. Hosting Solutions

### Cloud Provider
- **Amazon Web Services (AWS)** for reliable, global infrastructure.

### Components
- **ECS/EKS** for containerized FastAPI services behind an Application Load Balancer (ALB).
- **RDS (PostgreSQL)** for managed relational database with automatic backups.
- **ElastiCache (Redis)** for managed in-memory caching.
- **S3** for temporary file uploads before pushing to IPFS/ARWeave.

### Benefits
- **High availability** across multiple Availability Zones.
- **Auto-scaling** to handle usage spikes (e.g., many concurrent content ingestions).
- **Pay-as-you-go** cost model, optimizing for development vs. production workloads.

---

## 6. Infrastructure Components

### Load Balancer
- **AWS ALB** distributes traffic across multiple FastAPI containers, enabling zero-downtime deployments.

### Caching
- **Redis** for:
  - Session and JWT token caching.
  - Rate limiting (per-IP or per-user quotas).
  - Frequently accessed graph and topic metadata.

### CDN
- **Amazon CloudFront** serves static assets (e.g., initial JS/CSS bundles) and caches audio summaries for faster downloads.

### Task Queue
- **Celery** with **RabbitMQ** or **SQS** for reliable background processing of ingestion and graph generation jobs.

### Decentralized Storage
- **IPFS & ARWeave** nodes or hosted gateways for permanent storage of processed content and audio files.

---

## 7. Security Measures

### Authentication & Authorization
- **Wallet-based login** via Web3Auth/WalletConnect.
- **JWT tokens** for session management, stored in secure HTTP-only cookies.
- **Role-based access** (e.g., admin vs. user) enforced in middleware.

### Data Encryption
- **TLS** for all in-transit data.
- **AES-256** encryption for sensitive fields (e.g., user metadata) at rest in RDS.

### Rate Limiting & DDoS Protection
- **AWS WAF** to block malicious traffic.
- **API rate limits** enforced via Redis counters.

### Compliance
- **GDPR-friendly** data handling: users can request export or deletion of their data.

---

## 8. Monitoring and Maintenance

### Monitoring Tools
- **AWS CloudWatch** for logs, metrics, and alarms (CPU, memory, error rates).
- **Prometheus & Grafana** for custom application metrics (queue length, job durations).
- **Sentry** for real-time error tracking and alerting.

### Maintenance Strategies
- **Blue/Green Deployments** via ECS/EKS to minimize downtime.
- **Automated backups** of RDS with point-in-time recovery.
- **Database migrations** managed by Alembic, with CI checks to prevent destructive changes.
- **Dependency scanning** (e.g., GitHub Dependabot) to catch vulnerabilities early.

---

## 9. Conclusion and Overall Backend Summary

The Study4Me backend is designed for reliability, scalability, and developer friendliness. By combining FastAPI with a modular service pattern, managed cloud services, and decentralized storage on IPFS/ARWeave, the system meets the project’s goals:

- **Easy content ingestion** from multiple sources.
- **Fast graph generation** and natural-language querying.
- **Secure, NFT-gated access** with blockchain-native login.
- **Permanent, censorship-resistant data storage**.
- **Robust monitoring and maintenance** ensuring high uptime.

This setup not only supports current features—knowledge graph visualization, audio summaries, analytics—but also makes it straightforward to add new LLM connectors or storage options in the future.