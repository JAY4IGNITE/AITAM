# ThreatLens - Autonomous Multi-Agent SOC Platform

ThreatLens is a state-of-the-art, autonomous, multi-agent Security Operations Center (SOC) designed to ingest, investigate, and respond to cybersecurity threats across diverse input vectors (URLs, SMS, Emails, QR codes, Social Media). 

Built as a Hackathon project, it demonstrates an LLM-driven architecture that can triage alerts, orchestrate independent intelligence agents, detonate suspicious payloads in isolated environments, and formulate actionable response recommendations for human analysts.

## Key Features

- **Universal Input Processor**: Accepts any type of input (URLs, raw text, emails, QR codes) and normalizes it for analysis.
- **Autonomous Multi-Agent Architecture**: Uses an Investigation Coordinator to dynamically spawn agents (URL Intelligence, Threat Intelligence, Sandbox, Phishing Detection) based on the input risk level.
- **Explainable Evidence Graph**: Maps the relationships between extracted IOCs, agent observations, and threat intelligence into an "Attack Journey" that explains *how* and *why* a threat is dangerous.
- **Isolated Detonation Sandbox**: Spins up a headless Playwright instance in an untrusted Docker container (`aitam-sandbox-1`) to safely evaluate zero-day threats.
- **Professional SOC Interface**: A stunning, dark-mode, high-density React dashboard designed for security professionals to review incidents and approve response actions.

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.10+ (for local backend development)

### 2. Run the Stack (Docker)

```bash
docker-compose up -d --build
```

This will spin up:
- PostgreSQL (`postgres:5432`)
- Redis (`redis:6379`)
- ThreatLens API (`localhost:8000`)
- ThreatLens Celery Worker (Background tasks)
- ThreatLens Detonation Sandbox (`aitam-sandbox-1`)

### 3. Start the Frontend (Local)

```bash
cd frontend
npm install
npm run dev
```

The SOC Dashboard will be available at `http://localhost:5173`.

## Documentation

- [System Architecture](docs/ARCHITECTURE.md)
- [Hackathon Demo Guide](docs/HACKATHON_DEMO.md)

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (Async), PostgreSQL
- **Task Queue**: Celery + Redis
- **Agents/LLM**: Simulated dynamic LLM intelligence via autonomous Python agents
- **Frontend**: React (Vite), Tailwind CSS, React Query, Lucide Icons
- **Sandbox**: Headless Playwright (Chromium)

## Hackathon Mode
To reset the system state for a live demonstration, use the demo endpoints:
```bash
POST /api/demo/reset
POST /api/demo/run
```
