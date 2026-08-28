# ThreatLens Architecture

ThreatLens follows an event-driven, multi-agent microservice architecture designed for isolation, scalability, and deterministic autonomous reasoning.

## High-Level Architecture Diagram

```mermaid
graph TD
    subgraph Frontend [SOC Dashboard (React)]
        UI[Investigation View]
        Incident[Incident Queue]
    end

    subgraph Backend [FastAPI Application]
        API[API Endpoints]
        Router[Universal Input Processor]
        Coord[Investigation Coordinator]
        Risk[Risk Engine]
    end

    subgraph Async Layer [Celery Workers]
        Worker[Celery Task Consumer]
        AgentSystem[Multi-Agent System]
        Planner[Investigation Planner]
        Threat[Threat Intel Agent]
        URL[URL Intelligence Agent]
        Phish[Phishing Agent]
        Resp[Response Agent]
    end

    subgraph Sandbox Environment [Isolated Docker Network]
        SandboxCtrl[Sandbox Controller]
        Playwright[Playwright Headless Browser]
    end

    subgraph Data Layer [State & Storage]
        PG[(PostgreSQL)]
        Redis[(Redis Broker)]
    end

    UI -->|REST| API
    API --> Router
    Router --> Coord
    Coord -->|Enqueue Agent Tasks| Redis
    Redis --> Worker
    Worker --> AgentSystem
    AgentSystem --> Planner
    AgentSystem --> Threat
    AgentSystem --> URL
    AgentSystem --> Phish
    
    URL --> SandboxCtrl
    SandboxCtrl -->|Isolated gRPC/HTTP| Playwright
    
    AgentSystem -->|Write Findings| PG
    Worker -->|Update Risk| Risk
    Risk -->|Generate Incident| PG
    
    Coord --> Resp
    Resp -->|Recommend Block| PG
    Incident -->|Approve/Reject| API
```

## Component Overview

### 1. Universal Input Processor
The gateway to the system. It ingests arbitrary raw text, emails, URLs, or SMS messages, normalizes them, determines the underlying `InputType`, and kicks off an `Investigation`.

### 2. Investigation Coordinator
The autonomous engine of the SOC. It operates on an iterative loop:
1. **Observe**: Read current findings from the database.
2. **Reassess**: Compute a rolling risk score via the Risk Engine.
3. **Plan**: Run the `InvestigationPlannerAgent` to dynamically route the payload to necessary intelligence agents.
4. **Execute**: Dispatch Celery tasks.

### 3. Multi-Agent System
A swarm of specialized Python classes inheriting from `BaseAgent`. Each agent evaluates a specific threat vector (e.g., `BrandImpersonationAgent` checks for logo spoofing).
- Agents are executed asynchronously via **Celery**.
- Agents write their observations as `Finding` records mapped to an `Investigation`.

### 4. Sandbox Controller (Untrusted Detonation)
To safely evaluate zero-day links or suspected malware, ThreatLens implements a dedicated Sandbox environment (`aitam-sandbox-1`).
- Uses **Playwright** inside a completely isolated container with no host-filesystem access.
- Navigates to malicious URLs, records network intercepts, captures screenshots, and assesses DOM behavior.

### 5. Evidence Graph & Attack Journey
Raw findings are distilled into an Evidence Graph, linking IOCs (Indicators of Compromise) to observed behaviors. The resulting graph is parsed into a human-readable **Attack Journey**, explaining exactly how the threat operates.
