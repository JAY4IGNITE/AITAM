import { useQuery } from '@tanstack/react-query';
import { 
  Settings as SettingsIcon, Server, Shield, CheckCircle, AlertTriangle, 
  Database, Cpu, GlobeLock, RefreshCw, Key
} from 'lucide-react';

export const Settings = () => {
  const { data: health, isLoading, refetch } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => fetch('/api/health').then(res => res.json()),
    refetchInterval: 10000
  });

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <SettingsIcon className="w-8 h-8 text-primary" />
            System Diagnostics & Settings
          </h1>
          <p className="text-gray-400 mt-1">Monitor connected threat intelligence engines, PostgreSQL, Redis, and Celery workers.</p>
        </div>
        <button
          onClick={() => refetch()}
          className="bg-white/5 border border-white/10 hover:bg-white/10 text-gray-300 font-semibold px-4 py-2 rounded-md transition text-xs flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-check Health
        </button>
      </div>

      {/* System Service Health */}
      <div className="glass-panel p-6 border border-white/10 space-y-6">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Server className="w-5 h-5 text-primary" /> Infrastructure Services
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <HealthCard 
            title="PostgreSQL Threat Database" 
            status={health?.services?.database} 
            icon={Database} 
            desc="Asyncpg SQLAlchemy connection pooling for indicators, findings, & cases"
          />
          <HealthCard 
            title="Redis Cache & Celery Broker" 
            status={health?.services?.redis} 
            icon={Cpu} 
            desc="Threat intel 1-hour caching layer & async agent message broker"
          />
          <HealthCard 
            title="Celery Multi-Agent Worker" 
            status={health?.services?.celery} 
            icon={Server} 
            desc="Distributed async agent task runner"
          />
          <HealthCard 
            title="Playwright Sandbox Container" 
            status={health?.services?.sandbox} 
            icon={GlobeLock} 
            desc="Isolated headless Chromium container for zero-trust browser detonation"
          />
        </div>
      </div>

      {/* Threat Intel Provider Connectors */}
      <div className="glass-panel p-6 border border-white/10 space-y-6">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Shield className="w-5 h-5 text-amber-400" /> Active Threat Intelligence Providers
        </h2>

        <div className="space-y-3">
          {health?.services?.threat_intel_providers?.map((p: any, idx: number) => (
            <div key={idx} className="bg-black/40 border border-white/5 p-4 rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded bg-white/5">
                  <Key className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <h4 className="font-bold text-white text-sm">{p.provider_name}</h4>
                  <p className="text-xs text-gray-400 font-mono">Status: {p.status}</p>
                </div>
              </div>
              <div className="text-right">
                <span className={`px-2.5 py-1 rounded text-xs font-bold ${
                  p.enabled ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {p.enabled ? 'OPERATIONAL' : 'DISABLED'}
                </span>
                <div className="text-[10px] text-gray-500 font-mono mt-1">Latency: {p.latency_ms ? `${Math.round(p.latency_ms)}ms` : 'Instant'}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Security Architecture Details */}
      <div className="glass-panel p-6 border border-white/10 space-y-3 text-xs text-gray-400">
        <h3 className="font-bold text-white text-sm">Deployment Security Guarantees</h3>
        <p>• <strong>Zero-Trust Sandbox Isolation:</strong> Untrusted URLs and QR code payloads are never executed on the host server.</p>
        <p>• <strong>API Key Concealment:</strong> Threat intelligence keys (URLHAUS_AUTH_KEY, VIRUSTOTAL_API_KEY, GOOGLE_SAFE_BROWSING_API_KEY) are evaluated solely on the backend engine and never leaked in client network responses.</p>
        <p>• <strong>SSRF Protection:</strong> Internal RFC1918 and loopback IP addresses (127.0.0.1, 10.0.0.0/8, 192.168.0.0/16) are rejected before HTTP fetching.</p>
      </div>

    </div>
  );
};

const HealthCard = ({ title, status, icon: Icon, desc }: any) => {
  const isHealthy = status === 'healthy';
  return (
    <div className="bg-black/40 border border-white/5 p-4 rounded-lg space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-primary" />
          <h4 className="font-bold text-white text-sm">{title}</h4>
        </div>
        <span className={`px-2 py-0.5 rounded text-[11px] font-bold flex items-center gap-1 ${
          isHealthy ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
        }`}>
          {isHealthy ? <CheckCircle className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
          {isHealthy ? 'HEALTHY' : 'DEGRADED'}
        </span>
      </div>
      <p className="text-xs text-gray-400">{desc}</p>
    </div>
  );
};
