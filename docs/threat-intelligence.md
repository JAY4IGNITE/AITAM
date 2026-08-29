# Threat Intelligence Integration

ThreatLens features a resilient threat intelligence subsystem aggregating external security vendors, abuse feeds, and local PostgreSQL indicator caches.

```mermaid
sequenceDiagram
    participant Agent as ThreatIntelAgent
    participant Registry as ThreatIntelRegistry
    participant Redis as Redis Cache (1h TTL)
    participant UH as URLhaus (abuse.ch)
    participant VT as VirusTotal v3
    participant GSB as Google Safe Browsing
    participant DB as PostgreSQL Indicators DB

    Agent->>Registry: lookup(indicator, type)
    Registry->>Redis: GET threatintel:{type}:{indicator}
    alt Cache Hit
        Redis-->>Registry: Cached Verdicts JSON
        Registry-->>Agent: Return Cached Results
    else Cache Miss
        par Query Providers Concurrently
            Registry->>UH: POST /v1/url/ (Auth-Key)
            Registry->>VT: GET /api/v3/urls/{id} (x-apikey)
            Registry->>GSB: POST /v4/threatMatches:find (key)
            Registry->>DB: SELECT * FROM threat_indicators
        end
        UH-->>Registry: URLhaus Verdict (malware tags)
        VT-->>Registry: Detection Stats (malicious/clean)
        GSB-->>Registry: Threat Matches
        DB-->>Registry: Local Indicator Record
        Registry->>Redis: SETEX threatintel:{type}:{indicator} 3600 JSON
        Registry-->>Agent: Return Aggregated Results
    end
```

---

## Supported Providers

| Provider | Supported Indicator Types | Authentication Method | Fallback Behavior |
|---|---|---|---|
| **URLhaus (`abuse.ch`)** | `URL`, `DOMAIN`, `IP`, `HASH` | `Auth-Key` Header via `URLHAUS_AUTH_KEY` | Gracefully returns `UNKNOWN` on network error / rate limit |
| **VirusTotal v3** | `URL`, `DOMAIN`, `IP`, `HASH` | `x-apikey` Header via `VIRUSTOTAL_API_KEY` | Gracefully returns `UNKNOWN` if quota exhausted |
| **Google Safe Browsing** | `URL` | API Query Key via `GOOGLE_SAFE_BROWSING_API_KEY` | Returns `UNKNOWN` on configuration omission |
| **ThreatLens Local DB** | `URL`, `DOMAIN`, `IP`, `HASH`, `EMAIL` | Direct PostgreSQL asyncpg session | Instant local matching against synchronized feed |

---

## Automated Feed Ingestion

The Celery task `sync_threat_intel_feed_task` periodically fetches recent active malicious URLs from URLhaus (`/v1/urls/recent/`), normalizes the tags, and updates the local PostgreSQL `threat_indicators` table with deduplication and updated timestamps.
