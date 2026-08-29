# ThreatLens Specialized Intelligence Agents

ThreatLens employs 9 specialized agents that work collaboratively to assess threats.

```mermaid
classDiagram
    class BaseAgent {
        +String agent_name
        +String agent_version
        +List capabilities
        +analyze(investigation_id, session)
        +_execute(investigation_id, session, run)*
    }

    class TriageAgent {
        +evaluate_priority(input)
    }

    class InvestigationPlannerAgent {
        +plan_pipeline(triage_result)
    }

    class URLIntelligenceAgent {
        +decompose_url()
        +detect_punycode()
        +evaluate_tld_reputation()
        +detect_shorteners()
    }

    class EmailIntelligenceAgent {
        +parse_rfc822_headers()
        +detect_replyto_mismatch()
        +verify_spf_dkim()
        +extract_lures()
    }

    class SMSIntelligenceAgent {
        +detect_smishing()
        +detect_otp_theft()
        +detect_delivery_scams()
    }

    class SocialMessageIntelligenceAgent {
        +detect_crypto_giveaways()
        +detect_fake_support()
        +detect_recovery_fraud()
    }

    class QRCodeProcessor {
        +decode_qr_image()
        +detect_quishing()
    }

    class ThreatIntelligenceAgent {
        +query_urlhaus()
        +query_virustotal()
        +query_safebrowsing()
    }

    BaseAgent <|-- TriageAgent
    BaseAgent <|-- InvestigationPlannerAgent
    BaseAgent <|-- URLIntelligenceAgent
    BaseAgent <|-- EmailIntelligenceAgent
    BaseAgent <|-- SMSIntelligenceAgent
    BaseAgent <|-- SocialMessageIntelligenceAgent
    BaseAgent <|-- QRCodeProcessor
    BaseAgent <|-- ThreatIntelligenceAgent
```

---

## Agent Specifications

### 1. Triage Agent (`triage_agent.py`)
- **Capabilities:** Priority assignment (`P1_CRITICAL`, `P2_HIGH`, `P3_MEDIUM`, `P4_LOW`).
- **Logic:** Inspects keywords, input length, and urgency cues to allocate computing resources.

### 2. Investigation Planner Agent (`investigation_planner.py`)
- **Capabilities:** Dynamic worker scheduling.
- **Logic:** Maps input types (URL, Email, SMS, QR, Social) to necessary analysis agents.

### 3. URL Intelligence Agent (`url_agent.py`)
- **Capabilities:** Deep decomposition, IP-in-URL detection, Punycode/IDN homographs, suspicious TLD detection (`.top`, `.xyz`, `.click`, `.buzz`, `.cfd`, `.rest`), URL shortener detection (`bit.ly`, `tinyurl.com`, `t.co`), non-standard ports, and credential harvesting keywords.

### 4. Email Intelligence Agent (`email_agent.py`)
- **Capabilities:** RFC822 parser, Reply-To vs From domain mismatches, SPF/DKIM authentication flags, psychological pressure, financial invoice fraud lures, embedded URL extraction and forwarding.

### 5. SMS Intelligence Agent (`sms_agent.py`)
- **Capabilities:** Smishing classification, OTP / 2FA interception detection, bank fraud alerts, parcel tracking scams, urgency lures, embedded link forwarding.

### 6. Social Message Intelligence Agent (`social_agent.py`)
- **Capabilities:** Crypto doubling giveaways, fake helpdesk support redirection, account copyright suspension lures, high-yield investment fraud.

### 7. QR Code Processor (`qr_processor.py`)
- **Capabilities:** Pure image decoding (`pyzbar` / `Pillow` / `OpenCV`), multi-format barcode parsing, quishing defense, payload extraction and pipeline forwarding.

### 8. Threat Intelligence Agent (`threat_intel.py`)
- **Capabilities:** Concurrent multi-provider querying, consensus aggregation, IoC extraction, and confidence weighting.

### 9. Behavior Analysis & Sandbox Agent (`sandbox_agent.py`, `behavior_agent.py`)
- **Capabilities:** Isolated browser execution telemetry, DOM tree inspection, form action analysis, and screenshot capture.
