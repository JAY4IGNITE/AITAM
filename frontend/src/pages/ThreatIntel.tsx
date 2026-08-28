import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, Server, Search, AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';

export const ThreatIntel = () => {
  const [indicator, setIndicator] = React.useState('');
  const [indicatorType, setIndicatorType] = React.useState('URL');
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState<any[] | null>(null);
  const [error, setError] = React.useState('');

  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: () => fetch('/api/threat-intel/providers').then(res => res.json()),
    refetchInterval: 10000
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
      if (!res.ok) throw new Error("Failed to fetch intelligence or indicator not found");
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
      case 'MALICIOUS': return 'text-red-500 bg-red-500/10 border-red-500/30';
      case 'SUSPICIOUS': return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
      case 'CLEAN': return 'text-green-500 bg-green-500/10 border-green-500/30';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Shield className="w-8 h-8 text-primary" />
            Threat Intelligence Center
          </h1>
          <p className="text-gray-400 mt-2">Correlate indicators across global reputation providers.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Lookup Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Search className="w-5 h-5 text-primary" />
              Manual Indicator Lookup
            </h2>
            <div className="flex gap-4">
              <select 
                className="bg-black/50 border border-white/10 rounded-md p-3 text-white focus:border-primary focus:outline-none"
                value={indicatorType}
                onChange={e => setIndicatorType(e.target.value)}
              >
                <option value="URL">URL</option>
                <option value="DOMAIN">DOMAIN</option>
                <option value="IP">IP</option>
                <option value="HASH">HASH</option>
                <option value="EMAIL">EMAIL</option>
              </select>
              <input 
                type="text" 
                className="flex-1 bg-black/50 border border-white/10 rounded-md p-3 text-white focus:border-primary focus:outline-none"
                placeholder="Enter indicator (e.g. malicious.test)"
                value={indicator}
                onChange={e => setIndicator(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLookup()}
              />
              <button 
                className="bg-primary text-primary-foreground px-6 py-2 rounded-md font-semibold hover:opacity-90 transition disabled:opacity-50"
                onClick={handleLookup}
                disabled={loading || !indicator}
              >
                {loading ? 'Searching...' : 'LOOK UP'}
              </button>
            </div>
            {error && <div className="mt-4 text-red-400 text-sm">{error}</div>}
          </div>

          {/* Results Area */}
          {results && (
            <div className="glass-panel p-6 space-y-4">
              <h2 className="text-xl font-bold border-b border-white/10 pb-2">Intelligence Results</h2>
              {results.length === 0 && <p className="text-gray-400">No data found across providers.</p>}
              
              <div className="grid gap-4">
                {results.map((r, i) => (
                  <div key={i} className={`p-4 rounded-md border ${getVerdictColor(r.verdict)}`}>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="text-xs uppercase font-bold tracking-wider mb-1 opacity-80">{r.provider}</div>
                        <div className="text-lg font-bold">{r.verdict}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs opacity-80">Confidence</div>
                        <div className="font-mono">{Math.round(r.confidence * 100)}%</div>
                      </div>
                    </div>
                    
                    {r.categories && r.categories.length > 0 && (
                      <div className="flex gap-2 mt-3 flex-wrap">
                        {r.categories.map((c: string, idx: number) => (
                          <span key={idx} className="bg-black/30 px-2 py-1 rounded text-xs">{c}</span>
                        ))}
                      </div>
                    )}
                    
                    {r.evidence && r.evidence.length > 0 && (
                      <ul className="mt-3 space-y-1">
                        {r.evidence.map((ev: string, idx: number) => (
                          <li key={idx} className="text-sm opacity-90 flex items-start gap-2">
                            <span className="opacity-50 mt-1">▹</span> {ev}
                          </li>
                        ))}
                      </ul>
                    )}
                    
                    <div className="mt-4 pt-3 border-t border-current/20 text-xs opacity-70 flex justify-between">
                      <span>Last Seen: {new Date(r.last_seen || r.lookup_timestamp).toLocaleString()}</span>
                      {r.provider_metadata?.mock && <span className="font-bold">DEMO / SIMULATED INTELLIGENCE</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Providers */}
        <div className="space-y-6">
          <div className="glass-panel p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Server className="w-5 h-5 text-primary" />
              Provider Health
            </h2>
            <div className="space-y-4">
              {providers ? providers.map((p: any, i: number) => (
                <div key={i} className="bg-black/40 p-4 rounded-md border border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-sm">{p.provider_name}</span>
                    {p.status === 'Healthy' ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-orange-500" />
                    )}
                  </div>
                  <div className="text-xs text-gray-400 flex justify-between">
                    <span>Latency: {p.latency_ms ? `${Math.round(p.latency_ms)}ms` : 'N/A'}</span>
                    <span className={p.enabled ? 'text-blue-400' : 'text-gray-500'}>
                      {p.enabled ? 'ACTIVE' : 'DISABLED'}
                    </span>
                  </div>
                  {p.last_error && (
                    <div className="mt-2 text-xs text-red-400 bg-red-500/10 p-1 rounded truncate">
                      {p.last_error}
                    </div>
                  )}
                </div>
              )) : (
                <div className="text-sm text-gray-500">Loading providers...</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
