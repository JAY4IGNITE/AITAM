# ThreatLens Hackathon Demo Guide

This document outlines the ideal script for demonstrating ThreatLens to a panel of judges.

## Pre-Demo Setup

1. Ensure the entire stack is running:
   ```bash
   docker-compose up -d
   ```
2. Reset the demo environment to ensure a clean slate:
   ```bash
   curl -X POST http://localhost:8000/api/demo/reset
   ```
3. Open the frontend dashboard at `http://localhost:5173`.

---

## Demo Script

### 1. Introduction (The Problem)
"Modern Security Operation Centers (SOCs) are overwhelmed by alerts. Triage is manual, threat intelligence is scattered, and detonating suspicious links in a sandbox is time-consuming. **ThreatLens** solves this by introducing a fully autonomous, multi-agent intelligence layer that investigates threats and formulates responses in seconds, not hours."

### 2. Universal Input (The Ingestion)
1. Navigate to the **"Analyze"** tab in the dashboard.
2. Select **"SMS"** from the input type dropdown.
3. Paste the following malicious text:
   `"URGENT: Verify your crypto wallet at http://malicious.test/login before it is locked."`
4. Click **Start Analysis**.

*"Notice how the platform accepts raw unstructured text. The Universal Input Processor normalizes this and extracts the underlying indicators."*

### 3. Multi-Agent Triage (The Brain)
1. Switch to the **Investigation View**.
2. Point out the **Agent Activity Pipeline**.

*"Behind the scenes, an Investigation Coordinator acts as the central brain. It spawns a Triage Agent to determine priority. Seeing keywords like 'crypto' and 'urgent', it assigns Critical Priority. This triggers the Investigation Planner to dynamically route the URL to specialized agents."*

### 4. Sandbox Detonation (The Sandbox)
1. Click on the **Sandbox** sub-panel.

*"Because this is a Critical priority threat, the system spins up our Playwright Sandbox inside an isolated Docker container (`aitam-sandbox-1`). It securely navigates to the payload, capturing a screenshot and extracting malicious DOM activity without exposing our network."*

### 5. Evidence Graph & Attack Journey (The Explanation)
1. Scroll down to the **Attack Journey**.

*"Traditional scanners just return a 'Risk Score of 95'. ThreatLens tells you exactly WHY it's dangerous. The Attack Journey builds an explainable evidence graph, showing how the SMS leads to credential harvesting, backed by Threat Intelligence."*

### 6. Automated Response (The Resolution)
1. Navigate to the **Incidents Queue**.
2. Open the newly generated High-Severity Incident.
3. Scroll to **Recommended Actions**.

*"Once the risk threshold is exceeded, the Response Agent halts the investigation and generates a human-in-the-loop Incident. It formulates a concrete recommendation—like blocking the malicious domain at the firewall. With one click, the SOC Analyst can 'Approve' the action, neutralizing the threat."*

### 7. Executive Report
1. Click **View Threat Report**.

*"Finally, the system synthesizes the entire autonomous investigation into an executive summary, ready for compliance and auditing."*
