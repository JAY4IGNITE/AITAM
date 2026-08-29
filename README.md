<div align="center">
  <img src="https://via.placeholder.com/150/09090b/ffffff?text=ThreatLens" alt="ThreatLens Logo" width="120" height="120" />
  <h1>ThreatLens</h1>
  <p><strong>Autonomous Multi-Agent Security Operations Center (SOC)</strong></p>

  [![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg)](https://fastapi.tiangolo.com)
  [![React](https://img.shields.io/badge/React-18.x-61dafb.svg)](https://react.dev)
  [![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E.svg)](https://supabase.com/)
  [![Render](https://img.shields.io/badge/Deploy-Render-46E3B7.svg)](https://render.com/)
</div>

---

## 🚀 Overview

**ThreatLens** is a state-of-the-art, autonomous, multi-agent Security Operations Center (SOC) designed to automatically ingest, investigate, and respond to complex cybersecurity threats across diverse input vectors (URLs, SMS, Emails, QR codes, Social Media).

Built to drastically reduce Tier-1 SOC analyst workload, ThreatLens orchestrates specialized AI agents that independently triage alerts, gather threat intelligence, detonate suspicious payloads in isolated environments, and map findings to the **MITRE ATT&CK® Enterprise Matrix**.

> [!IMPORTANT]
> **Production Ready:** ThreatLens is fully migrated to **Supabase** for database management and is ready for 1-click cloud deployment on **Render**.

---

## ✨ Key Capabilities

| Capability | Description |
| :--- | :--- |
| **Universal Input Processor** | Ingests URLs, raw text, phishing emails, QR payloads, and normalizes them for unified analysis. |
| **Autonomous Multi-Agent Hive** | Dynamic orchestration of specialized agents: URL Intelligence, Sender Reputation, Attachment Sandbox, and Social Engineering Analysis. |
| **Live Email Ingestion** | Fully automated integration with **TempMail.so**. ThreatLens provisions temporary inboxes, intercepts real live emails, and triggers instant investigations. |
| **MITRE ATT&CK® Integration** | Automatically maps identified adversary tactics and techniques to the MITRE framework for standardized reporting. |
| **Explainable Evidence Graph** | Constructs a visual "Attack Journey" mapping relationships between extracted IOCs, agent observations, and final risk scores. |
| **Dark-Mode SOC Dashboard** | High-density, professional Antigravity monochrome design system (`#09090b` blacks, `#ffffff` whites) optimized for security analysts. |

---

## 🏗️ Architecture & Flow

1. **Ingestion Layer:** Accepts threat vectors via REST API or intercepts live emails.
2. **Triage Agent:** Analyzes the raw input, normalizes data, and determines the initial risk severity.
3. **Investigation Coordinator:** Dynamically spawns parallel worker agents based on the payload type (e.g., dispatching the URL Agent to VirusTotal and the Sandbox Agent to execute malicious scripts).
4. **Data Aggregation:** Agents write findings, IOCs (Indicators of Compromise), and evidence nodes directly to the Supabase PostgreSQL database.
5. **Reporting & Action:** Generates Markdown/JSON forensic dossiers and automated YARA/Suricata rules.

---

## 🛠️ Technology Stack

- **Backend / Core Engine:** Python 3.11, FastAPI, SQLAlchemy (Async), asyncpg.
- **Database:** PostgreSQL (Hosted on **Supabase** with PgBouncer connection pooling).
- **Task Queue & Caching:** Redis, Celery (optional async mode).
- **Frontend SOC Interface:** React 18, Vite, Tailwind CSS (Antigravity monochrome design), Lucide Icons, React Router.
- **Sandbox Detonation:** Headless Playwright (Chromium) operating inside isolated Docker containers.
- **Threat Intel Integrations:** Google Safe Browsing, VirusTotal, URLhaus.

---

## 📦 Local Installation & Setup

### 1. Prerequisites
- [Docker](https://www.docker.com/) and Docker Compose
- [Node.js](https://nodejs.org/) (v20+)
- [Supabase Account](https://supabase.com/)

### 2. Configure Environment Setup
Clone the repository and configure your `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Ensure your `DATABASE_URL` is configured for your Supabase transaction pooler:
```ini
DATABASE_URL=postgresql://postgres.crrlmgpdzatcwdpvunte:[YOUR-PASSWORD]@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres
```

### 3. Start the Backend via Docker
```bash
docker compose up -d --build
```
*Note: The backend application automatically creates and synchronizes all 32 required database tables on your Supabase instance during startup.*

### 4. Start the Frontend Application
```bash
cd frontend
npm install
npm run dev
```
Access the SOC Dashboard at `http://localhost:3000`.

---

## ☁️ Cloud Deployment (Render)

ThreatLens is optimized for a seamless, unified deployment on [Render](https://render.com/).

### Option A: One-Click Blueprint
We provide a `render.yaml` blueprint for instant cloud deployment.
1. Connect your repository to Render.
2. Choose **New +** > **Blueprint**.
3. Supply your Supabase `DATABASE_URL` and Threat Intel API keys when prompted.
4. Render will automatically provision both the `threatlens-api` and `threatlens-ui` services.

### Option B: Manual Setup
Please refer to the detailed [DEPLOY_RENDER.md](DEPLOY_RENDER.md) guide included in this repository.

---

## 🛡️ Live Threat Intel Providers

To utilize the full multi-agent capabilities, acquire API keys for:
- [Google Safe Browsing](https://developers.google.com/safe-browsing)
- [VirusTotal API](https://www.virustotal.com/)
- [URLhaus API](https://urlhaus.abuse.ch/api/)
- [TempMail.so API](https://tempmail.so/) (for live automated phishing analysis)

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  <p>Built with 🖤 for Security Professionals and Threat Hunters.</p>
</div>
