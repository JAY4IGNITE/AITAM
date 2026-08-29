import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Shield, Server, Search, AlertTriangle, CheckCircle, RefreshCw, 
  Database, Globe, Layers, ArrowUpDown, ChevronLeft, ChevronRight,
  ExternalLink
} from 'lucide-react';

export const ThreatIntel = () => {
  const queryClient = useQueryClient();
  const [indicator, setIndicator] = useState('');
  const [indicatorType, setIndicatorType] = useState('URL');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[] | null>(null);
  const [error, setError] = useState('');

  // Table pagination & search state
  const [page, setPage] = useState(1);
  const [tableSearch, setTableSearch] = useState('');
  const [tableType, setTableType] = useState('');
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: () => fetch('/api/threat-intel/providers').then(res => res.json()),
    refetchInterval: 10000
  });

  const { data: dbIndicators, isLoading: isTableLoading } = useQuery({
    queryKey: ['threat-indicators', page, tableSearch, tableType],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '10',
        ...(tableSearch ? { search: tableSearch } : {}),
        ...(tableType ? { indicator_type: tableType } : {})
      });
      const res = await fetch(`/api/threat-intel/indicators?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to load indicators');
      return res.json();
    }
  });

  const syncMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/threat-intel/sync', { method: 'POST' });
      if (!res.ok) throw new Error('Sync failed');
      return res.json();
    },
    onSuccess: (data) => {
      setSyncStatus(`Synced ${data.new_indicators_count} new, ${data.updated_indicators_count} updated threats from URLhaus.`);
      queryClient.invalidateQueries({ queryKey: ['threat-indicators'] });
    },
    onError: (err: any) => {
      setSyncStatus(`Sync error: ${err.message}`);
    }
  });

  const handleLookup = async () => {
    if (!indicator) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/threat-intel/lookup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ indicator, indicator_type: indicatorType })
      });
      if (!res.ok) throw new Error("No threat intelligence matched or lookup failed.");
      const data = await res.json();
      setResults(data);
    } catch (e: any) {
      setError(e.message);
      setResults(null);
    }
    setLoading(false);
  };

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'MALICIOUS': return 'text-red-400 bg-red-500/10 border-red-500/30';
      case 'SUSPICIOUS': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'CLEAN': return 'text-green-400 bg-green-500/10 border-green-500/30';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3 text-white">
            <Shield className="w-8 h-8 text-primary" />
            Threat Intelligence Center
          </h1>
          <p className="text-gray-400 mt-1">Real-time correlation against URLhaus (abuse.ch), VirusTotal, Google Safe Browsing, and local IoC database.</p>
        </div>
        <button 
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="bg-primary/20 border border-primary/40 hover:bg-primary/30 text-primary font-semibold px-5 py-2.5 rounded-md transition text-sm flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
          {syncMutation.isPending ? 'Syncing URLhaus...' : 'Sync URLhaus Feed'}
        </button>
      </div>

      {syncStatus && (
        <div className="bg-primary/10 border border-primary/30 p-3 rounded-lg text-xs text-primary font-medium flex items-center justify-between">
          <span>{syncStatus}</span>
          <button onClick={() => setSyncStatus(null)} className="text-gray-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Grid: Manual Lookup & Provider Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Lookup Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6 border border-white/10">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
              <Search className="w-5 h-5 text-primary" />
              Live Indicator Lookup
            </h2>
            <div className="flex flex-wrap gap-3">
              <select 
                className="bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:border-primary focus:outline-none"
                value={indicatorType}
                onChange={e => setIndicatorType(e.target.value)}
              >
                <option value="URL">URL</option>
                <option value="DOMAIN">DOMAIN</option>
                <option value="IP">IP Address</option>
                <option value="HASH">SHA256 / MD5 Hash</option>
                <option value="EMAIL">Email</option>
              </select>
              <input 
                type="text" 
                className="flex-1 min-w-[200px] bg-black/50 border border-white/10 rounded-md px-4 py-2 text-sm text-white font-mono focus:border-primary focus:outline-none placeholder:text-gray-600"
                placeholder="Enter indicator (e.g. http://malicious-site.top or domain.com)"
                value={indicator}
                onChange={e => setIndicator(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLookup()}
              />
              <button 
                className="bg-primary text-primary-foreground px-6 py-2 rounded-md font-bold text-sm hover:opacity-90 transition disabled:opacity-50"
                onClick={handleLookup}
                disabled={loading || !indicator}
              >
                {loading ? 'Querying...' : 'SEARCH'}
              </button>
            </div>
            {error && <div className="mt-3 text-red-400 text-xs">{error}</div>}
          </div>

          {/* Results Area */}
          {results && (
            <div className="glass-panel p-6 space-y-4 border border-white/10">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h2 className="text-lg font-bold text-white">Intelligence Results ({results.length} Providers)</h2>
                <span className="text-xs font-mono text-gray-400">{indicator}</span>
              </div>
              
              <div className="grid gap-3">
                {results.map((r, i) => (
                  <div key={i} className={`p-4 rounded-lg border ${getVerdictColor(r.verdict)}`}>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="text-[11px] uppercase font-bold tracking-wider mb-0.5 opacity-80">{r.provider}</div>
                        <div className="text-base font-bold">{r.verdict}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] opacity-80 uppercase tracking-wider">Confidence</div>
                        <div className="font-mono text-sm font-bold">{Math.round(r.confidence * 100)}%</div>
                      </div>
                    </div>
                    
                    {r.categories && r.categories.length > 0 && (
                      <div className="flex gap-1.5 mt-2 flex-wrap">
                        {r.categories.map((c: string, idx: number) => (
                          <span key={idx} className="bg-black/40 px-2 py-0.5 rounded text-[11px] font-mono">{c}</span>
                        ))}
                      </div>
                    )}
                    
                    {r.evidence && r.evidence.length > 0 && (
                      <ul className="mt-2.5 space-y-1">
                        {r.evidence.map((ev: string, idx: number) => (
                          <li key={idx} className="text-xs opacity-90 flex items-start gap-1.5 font-medium">
                            <span className="opacity-50">▹</span> {ev}
                          </li>
                        ))}
                      </ul>
                    )}
                    
                    <div className="mt-3 pt-2 border-t border-current/20 text-[11px] opacity-70 flex justify-between font-mono">
                      <span>Observed: {new Date(r.last_seen || r.lookup_timestamp).toLocaleString()}</span>
                      <span>{r.indicator_type}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Providers Health */}
        <div className="space-y-6">
          <div className="glass-panel p-6 border border-white/10">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
              <Server className="w-5 h-5 text-primary" />
              Connected Providers
            </h2>
            <div className="space-y-3">
              {providers ? providers.map((p: any, i: number) => (
                <div key={i} className="bg-black/40 p-3.5 rounded-lg border border-white/5 space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-sm text-white">{p.provider_name}</span>
                    {p.status.startsWith('Healthy') ? (
                      <span className="flex items-center gap-1 text-emerald-400 text-xs font-semibold">
                        <CheckCircle className="w-3.5 h-3.5" /> Online
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-amber-400 text-xs font-semibold">
                        <AlertTriangle className="w-3.5 h-3.5" /> {p.status}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-gray-400 flex justify-between font-mono">
                    <span>Latency: {p.latency_ms ? `${Math.round(p.latency_ms)}ms` : 'Cached'}</span>
                    <span className={p.enabled ? 'text-primary' : 'text-gray-500'}>
                      {p.enabled ? 'ACTIVE' : 'OFFLINE'}
                    </span>
                  </div>
                  {p.last_error && (
                    <div className="mt-1 text-[10px] text-amber-400 bg-amber-500/10 p-1 rounded font-mono truncate">
                      {p.last_error}
                    </div>
                  )}
                </div>
              )) : (
                <div className="text-xs text-gray-500">Checking provider status...</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Threat Database Table */}
      <div className="glass-panel p-6 border border-white/10 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-primary" /> Local Threat Indicators Database
            </h2>
            <p className="text-xs text-gray-400">Synchronized malicious URLs, domains, and IOCs stored locally in PostgreSQL.</p>
          </div>

          <div className="flex items-center gap-3">
            <input 
              type="text"
              placeholder="Search database..."
              className="bg-black/40 border border-white/10 rounded-md px-3 py-1.5 text-xs text-white placeholder:text-gray-600 focus:outline-none focus:border-primary"
              value={tableSearch}
              onChange={e => { setTableSearch(e.target.value); setPage(1); }}
            />
            <select
              className="bg-black/40 border border-white/10 rounded-md px-3 py-1.5 text-xs text-gray-300 focus:outline-none"
              value={tableType}
              onChange={e => { setTableType(e.target.value); setPage(1); }}
            >
              <option value="">All Types</option>
              <option value="URL">URL</option>
              <option value="DOMAIN">Domain</option>
              <option value="IP">IP</option>
              <option value="HASH">Hash</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-white/5 text-gray-400 uppercase tracking-wider font-sans text-[11px]">
              <tr>
                <th className="px-4 py-3">Indicator</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Classification</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Tags</th>
                <th className="px-4 py-3">Last Seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isTableLoading ? (
                <tr><td colSpan={6} className="text-center py-8 text-gray-500">Loading indicators...</td></tr>
              ) : dbIndicators?.items?.length ? (
                dbIndicators.items.map((item: any) => (
                  <tr key={item.id} className="hover:bg-white/5 transition">
                    <td className="px-4 py-3 font-semibold text-white max-w-sm truncate" title={item.indicator}>
                      {item.indicator}
                    </td>
                    <td className="px-4 py-3 font-sans text-gray-400">{item.indicator_type}</td>
                    <td className="px-4 py-3 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.classification === 'MALICIOUS' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        item.classification === 'SUSPICIOUS' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {item.classification}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-primary font-sans text-xs">{item.source}</td>
                    <td className="px-4 py-3 font-sans">
                      <div className="flex gap-1 flex-wrap">
                        {item.tags?.slice(0, 3).map((tag: string, tIdx: number) => (
                          <span key={tIdx} className="bg-white/5 px-1.5 py-0.5 rounded text-[10px] text-gray-300">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-sans">{new Date(item.last_seen).toLocaleDateString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    No threat indicators in database yet. Click "Sync URLhaus Feed" above to populate!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Table Pagination */}
        {dbIndicators && dbIndicators.pages > 1 && (
          <div className="flex items-center justify-between pt-3 text-xs text-gray-400">
            <div>Page {dbIndicators.page} of {dbIndicators.pages} ({dbIndicators.total} total indicators)</div>
            <div className="flex gap-2">
              <button 
                disabled={page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="bg-white/5 px-3 py-1 rounded border border-white/10 disabled:opacity-30 flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Prev
              </button>
              <button 
                disabled={page >= dbIndicators.pages}
                onClick={() => setPage(p => p + 1)}
                className="bg-white/5 px-3 py-1 rounded border border-white/10 disabled:opacity-30 flex items-center gap-1"
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Autonomous SIEM / YARA Rule Generator Card */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" />
            <h3 className="text-base font-bold text-white uppercase tracking-wider font-mono">Autonomous Threat Rule Generator (YARA / Suricata)</h3>
          </div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            Auto-Synthesized
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-2">
            <span className="text-xs font-mono text-gray-400">YARA Phishing & Malware Rule:</span>
            <pre className="bg-black/80 border border-white/10 rounded-lg p-3 text-[11px] font-mono text-emerald-400 overflow-x-auto">
{`rule ThreatLens_Autonomous_Phish_Block {
    meta:
        description = "Automated IoC detection rule"
        author = "ThreatLens Autonomous SOC"
        date = "${new Date().toISOString().split('T')[0]}"
        severity = "HIGH"
    strings:
        $login1 = "auth/verify" nocase
        $login2 = "account-update" nocase
        $cred1 = "password" nocase
        $cred2 = "credit card" nocase
    condition:
        any of ($login*) and 1 of ($cred*)
}`}
            </pre>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-mono text-gray-400">Suricata / Snort Network Signature:</span>
            <pre className="bg-black/80 border border-white/10 rounded-lg p-3 text-[11px] font-mono text-cyan-400 overflow-x-auto">
{`alert http $HOME_NET any -> $EXTERNAL_NET any (
    msg:"THREATLENS Inbound Phishing Domain Redirection Detected";
    flow:established,to_server;
    content:"POST"; http_method;
    content:"/auth/login"; http_uri;
    classtype:trojan-activity;
    sid:9001042; rev:1;
)`}
            </pre>
          </div>
        </div>
      </div>

    </div>
  );
};

