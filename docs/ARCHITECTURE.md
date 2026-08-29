# ThreatLens Architecture Overview

ThreatLens is an autonomous, risk-adaptive cybersecurity investigation and threat intelligence platform designed to ingest, decompose, analyze, and neutralize multi-vector malicious campaigns in real time.

```mermaid
flowchart TD
    subgraph Inputs [Universal Ingestion Vectors]
        U1[URL / Web Links]
        U2[Email / EML Headers & Body]
        U3[SMS / Smishing Text]
        U4[QR Code Image / Payload]
        U5[Web Page HTML]
        U6[Social Media DM / Post]
    end

    subgraph Preprocessing [Universal Input Processor]
        P1[Canonical Normalization]
        P2[IoC Extraction URLs, Domains, IPs, Emails, Hashes]
    end

    subgraph Orchestration [Autonomous Multi-Agent Core]
        T1[Triage Agent - Priority P1-P4]
        IP[Investigation Planner Agent]
        
        subgraph Agents [Specialized Intelligence Agents]
            A1[URL Intelligence Agent]
            A2[Email Intelligence Agent]
            A3[SMS Intelligence Agent]
            A4[Social Message Agent]
            A5[QR Code Processor]
            A6[Brand Impersonation Agent]
            A7[Content & Keyword Agent]
            A8[Threat Intelligence Agent]
        end
    end

    subgraph ThreatIntel [Threat Intelligence Engine]
        TI1[URLhaus Provider abuse.ch]
        TI2[VirusTotal v3 Provider]
        TI3[Google Safe Browsing v4]
        TI4[PostgreSQL Local Indicators DB]
        RC[(Redis Cache 1h TTL)]
    end

    subgraph Sandbox [Isolated Zero-Trust Detonation]
        SB[Headless Playwright Container]
        BA[Behavioral Telemetry & Screenshot Agent]
    end

    subgraph Synthesis [Evidence Fusion & Explainable Risk]
        EF[Evidence Fusion & Graph Service]
        RE[Deterministic 0-100 Risk Engine]
        EX[Explainable Intelligence Engine]
    end

    subgraph Actions [SOC Incident & Mitigation]
        INC[SOC Incident Queue]
        RESP[Automated Response & Action Approval]
        REP[Threat Intelligence Report JSON]
    end

    Inputs --> Preprocessing
    Preprocessing --> Orchestration
    T1 --> IP
    IP --> Agents
    A8 <--> ThreatIntel
    ThreatIntel <--> RC
    Agents --> Synthesis
    RE -->|Score >= 40 or Suspicious Heuristics| Sandbox
    Sandbox --> Synthesis
    Synthesis --> Actions
```

---

## Key Subsystems

### 1. Universal Input Normalization & Extraction
- Accepts arbitrary user inputs across 6 vectors (URLs, raw RFC822 EML emails, SMS texts, uploaded QR images/data URIs, Web Page HTML, and Social Media posts).
- Normalizes canonical formats and extracts indicators of compromise (URLs, nested domains, IP addresses, email addresses, cryptographic hashes).

### 2. Autonomous Multi-Agent Orchestration
- **Triage Agent:** Evaluates raw indicators and assigns priority (`P1_CRITICAL`, `P2_HIGH`, `P3_MEDIUM`, `P4_LOW`).
- **Investigation Planner Agent:** Analyzes the target structure and dynamically schedules specialized workers.
- **Concurrent Execution:** Dispatches agents concurrently via async event loop / Celery workers.

### 3. Real Threat Intelligence Providers & Redis Caching
- **URLhaus (`abuse.ch`):** Direct API querying using secret backend API key (`URLHAUS_AUTH_KEY`).
- **VirusTotal v3:** Correlates file hashes, domains, and IP reputations.
- **Google Safe Browsing v4:** Checks malicious social engineering and malware lists.
- **PostgreSQL Indicators Database:** Local indexed storage of confirmed threats.
- **Redis Cache Layer:** In-memory caching with 3600-second TTL prevents rate limit exhaustion.

### 4. Zero-Trust Playwright Sandbox
- Suspicious URLs (risk score $\ge 40$ or evasive heuristics) are detonated inside an isolated headless browser container.
- Captures DOM structure, console errors, network requests, redirects, and full-page visual screenshots without executing untrusted code on the host.

### 5. Explainable Risk Engine & Evidence Fusion
- Maps multi-agent evidence into a normalized graph.
- Calculates an explainable 0–100 risk score:
  - `0 - 19`: **SAFE**
  - `20 - 39`: **LOW**
  - `40 - 59`: **MEDIUM / SUSPICIOUS**
  - `60 - 79`: **HIGH**
  - `80 - 100`: **CRITICAL**
  - Missing or unverified data defaults strictly to **UNKNOWN**.
- Produces evidence-based "Why is this risky?" explanations and actionable mitigation steps.
