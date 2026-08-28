import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Shield, LayoutDashboard, Activity, FileWarning, Search, SearchCheck } from 'lucide-react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// We'll create these components next
const Dashboard = () => <div className="p-8"><h1 className="text-3xl font-bold mb-6">Dashboard</h1><div className="glass-panel p-6 h-64 flex items-center justify-center">Analytics coming soon</div></div>;

const Investigate = () => {
  const [url, setUrl] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const navigate = import('react-router-dom').then(m => m.useNavigate);
  // Note: we can't easily use hooks dynamically inside this simplified component structure if they aren't imported properly, 
  // so let's just use window.location for MVP.
  
  const submit = async () => {
    if (!url) return;
    setLoading(true);
    try {
      const res = await fetch('/api/investigations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_type: 'URL', target: url })
      });
      const data = await res.json();
      window.location.href = `/investigations/${data.id}`;
    } catch (e) {
      console.error(e);
      alert('Failed to submit');
    }
    setLoading(false);
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Start Investigation</h1>
      <div className="glass-panel p-6 flex flex-col items-center justify-center h-64">
        <input 
          type="text" 
          placeholder="Enter URL to analyze..." 
          className="w-full max-w-lg bg-black/50 border border-white/10 rounded-md p-3 mb-4 focus:outline-none focus:border-primary text-white" 
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button 
          className="bg-primary text-primary-foreground px-6 py-2 rounded-md font-semibold hover:opacity-90 transition disabled:opacity-50"
          onClick={submit}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </div>
  );
};

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';

const InvestigationDetails = () => {
  const { id } = useParams();
  
  const { data: inv } = useQuery({
    queryKey: ['investigation', id],
    queryFn: () => fetch(`/api/investigations/${id}`).then(res => res.json()),
    refetchInterval: (data) => (data?.status === 'COMPLETED' || data?.status === 'FAILED') ? false : 2000
  });

  const { data: agents } = useQuery({
    queryKey: ['agents', id],
    queryFn: () => fetch(`/api/investigations/${id}/agents`).then(res => res.json()),
    refetchInterval: 2000
  });

  const { data: risk } = useQuery({
    queryKey: ['risk', id],
    queryFn: () => fetch(`/api/investigations/${id}/risk`).then(res => res.json()),
    refetchInterval: 2000
  });

  const { data: sandbox } = useQuery({
    queryKey: ['sandbox', id],
    queryFn: () => fetch(`/api/investigations/${id}/sandbox`).then(res => res.json()),
    refetchInterval: (data) => (data?.status === 'COMPLETED' || data?.status === 'FAILED') ? false : 2000
  });

  const { data: sandboxEvents } = useQuery({
    queryKey: ['sandboxEvents', id],
    queryFn: () => fetch(`/api/investigations/${id}/sandbox/events`).then(res => res.json()),
    refetchInterval: 2000,
    enabled: !!sandbox && sandbox.status !== 'NOT_STARTED'
  });

  const { data: sandboxArtifacts } = useQuery({
    queryKey: ['sandboxArtifacts', id],
    queryFn: () => fetch(`/api/investigations/${id}/sandbox/artifacts`).then(res => res.json()),
    refetchInterval: 5000,
    enabled: !!sandbox && sandbox.status === 'COMPLETED'
  });

  const { data: graph } = useQuery({
    queryKey: ['graph', id],
    queryFn: () => fetch(`/api/investigations/${id}/graph`).then(res => res.json()),
    enabled: inv?.status === 'COMPLETED'
  });

  const { data: journey } = useQuery({
    queryKey: ['journey', id],
    queryFn: () => fetch(`/api/investigations/${id}/journey`).then(res => res.json()),
    enabled: inv?.status === 'COMPLETED'
  });

  const { data: explanation } = useQuery({
    queryKey: ['explanation', id],
    queryFn: () => fetch(`/api/investigations/${id}/explanation`).then(res => res.json()),
    enabled: inv?.status === 'COMPLETED'
  });

  if (!inv) return <div className="p-8">Loading investigation...</div>;

  const downloadReport = async () => {
    try {
      const res = await fetch(`/api/investigations/${id}/report`);
      const reportData = await res.json();
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ThreatLens-Report-${inv.display_id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Report generation failed.");
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold">{inv.display_id}</h1>
          <p className="text-gray-400 mt-1">Status: {inv.status} | Stage: {inv.current_stage}</p>
        </div>
        <div className="text-right flex items-center gap-4">
          {inv.status === 'COMPLETED' && (
            <button 
              onClick={downloadReport}
              className="bg-primary/20 text-primary border border-primary/50 px-4 py-2 rounded-md font-semibold hover:bg-primary hover:text-white transition text-sm"
            >
              Download Report
            </button>
          )}
          <div>
            <div className="text-sm text-gray-400">Overall Progress</div>
            <div className="text-2xl font-bold">{inv.progress}%</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Risk Profile & Explanation Panel */}
        <div className="glass-panel p-6">
          <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">Risk Profile</h2>
          {risk ? (
            <div>
              <div className="flex items-center gap-4 mb-6">
                <div className={`text-4xl font-bold ${risk.level === 'CRITICAL' ? 'text-red-500' : risk.level === 'HIGH' ? 'text-orange-500' : risk.level === 'MEDIUM' ? 'text-yellow-500' : 'text-green-500'}`}>
                  {risk.score}
                </div>
                <div className="text-lg uppercase font-semibold text-gray-300">
                  {risk.level}
                </div>
              </div>
              
              {explanation && (
                <div className="mt-4 p-4 bg-black/30 border border-white/5 rounded-md">
                  <h3 className="font-bold text-lg mb-2">Why is this dangerous?</h3>
                  <p className="text-gray-300 text-sm mb-4">{explanation.summary}</p>
                  <h4 className="font-medium text-xs text-gray-400 mb-2">EVIDENCE:</h4>
                  <ul className="space-y-1">
                    {explanation.evidence.map((ev: string, idx: number) => (
                      <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                        <span className="text-primary">{ev.startsWith('✓') ? ev : `✓ ${ev}`}</span>
                      </li>
                    ))}
                  </ul>
                  {explanation.sandbox_confirmation && (
                    <div className="mt-4 text-xs font-bold text-red-400 bg-red-500/10 inline-block px-2 py-1 rounded">
                      SANDBOX CONFIRMATION: YES
                    </div>
                  )}
                </div>
              )}
              
              {!explanation && (
                <>
                  <h3 className="font-medium mb-2 text-sm text-gray-400">Deterministic Reasons:</h3>
                  <ul className="space-y-2">
                    {risk.reasons.map((r: any, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-sm bg-black/20 p-2 rounded">
                        <span className="text-green-400 mt-0.5">✓</span>
                        <span>{r.finding} <span className="text-gray-500">({r.contribution})</span></span>
                      </li>
                    ))}
                    {risk.reasons.length === 0 && <li className="text-gray-500 text-sm italic">No risk indicators identified yet.</li>}
                  </ul>
                </>
              )}
            </div>
          ) : (
            <div className="text-gray-500 text-sm">Calculating risk...</div>
          )}
        </div>

        {/* Attack Journey Panel */}
        <div className="glass-panel p-6">
          <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">Attack Journey</h2>
          {journey && journey.length > 0 ? (
            <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
              {journey.map((step: any, idx: number) => (
                <div key={idx} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-bold border border-primary/50">
                      {step.sequence}
                    </div>
                    {idx < journey.length - 1 && <div className="w-px h-full bg-white/10 my-1"></div>}
                  </div>
                  <div className="pb-4">
                    <h3 className="font-semibold text-sm">{step.title}</h3>
                    <p className="text-xs text-gray-400 mt-1">{step.description}</p>
                    {step.risk_after > step.risk_before && (
                      <div className="text-xs mt-2 text-red-400 bg-red-500/10 inline-block px-2 py-1 rounded">
                        Risk Increased: {step.risk_before} → {step.risk_after}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-sm italic">Analysis must complete before journey generation.</div>
          )}
        </div>

        {/* Evidence Graph Panel */}
        <div className="glass-panel p-6 md:col-span-2">
          <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">Evidence Graph</h2>
          {graph && graph.nodes ? (
            <div className="bg-black/40 rounded-md p-4 min-h-[300px] border border-white/5 font-mono text-sm overflow-x-auto">
              <div className="text-gray-400 mb-4">Relational Node Matrix (Simplified View)</div>
              {graph.edges.map((e: any, idx: number) => {
                const src = graph.nodes.find((n: any) => n.id === e.source_node_id);
                const tgt = graph.nodes.find((n: any) => n.id === e.target_node_id);
                if (!src || !tgt) return null;
                return (
                  <div key={idx} className="mb-2 flex items-center gap-3">
                    <span className="text-blue-400">[{src.node_type}]</span>
                    <span className="text-gray-300">{src.safe_display_value}</span>
                    <span className="text-gray-500">──({e.relationship_type.toLowerCase()})──→</span>
                    <span className="text-orange-400">[{tgt.node_type}]</span>
                    <span className="text-gray-300">{tgt.safe_display_value}</span>
                  </div>
                );
              })}
              {graph.edges.length === 0 && <div className="text-gray-500">No relationships mapped.</div>}
            </div>
          ) : (
            <div className="text-gray-500 text-sm italic">Graph generates upon investigation completion.</div>
          )}
        </div>
        
        {/* Sandbox Analysis Panel */}
        <div className="glass-panel p-6 md:col-span-2">
          <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">Sandbox Dynamic Analysis</h2>
          {sandbox && sandbox.status !== 'NOT_STARTED' ? (
            <div className="space-y-4">
              <div className="flex gap-6 items-center">
                <div className={`px-3 py-1 rounded text-sm font-medium ${sandbox.status === 'COMPLETED' ? 'bg-green-500/20 text-green-400' : sandbox.status === 'FAILED' || sandbox.status === 'TIMEOUT' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                  Status: {sandbox.status}
                </div>
                <div className="text-sm text-gray-400">Events Captured: {sandbox.event_count || 0}</div>
              </div>
              
              {sandboxEvents && sandboxEvents.length > 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
                  <div>
                    <h3 className="font-medium text-sm text-gray-400 mb-2">Event Log:</h3>
                    <div className="bg-black/40 rounded-md p-3 h-64 overflow-y-auto space-y-2 border border-white/5">
                      {sandboxEvents.map((ev: any, idx: number) => (
                        <div key={idx} className="text-xs flex gap-2 border-b border-white/5 pb-1">
                          <span className="text-gray-500 min-w-[70px]">{new Date(ev.timestamp * 1000).toLocaleTimeString()}</span>
                          <span className={`font-semibold ${ev.severity === 'CRITICAL' ? 'text-red-500' : ev.severity === 'HIGH' ? 'text-orange-400' : ev.severity === 'WARNING' ? 'text-yellow-400' : 'text-blue-400'}`}>{ev.event_type}</span>
                          <span className="text-gray-300 truncate">{JSON.stringify(ev.metadata)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-sm text-gray-400 mb-2">Artifacts:</h3>
                    {sandboxArtifacts?.final ? (
                      <div className="rounded overflow-hidden border border-white/10 relative group">
                        <img src={`data:image/jpeg;base64,${sandboxArtifacts.final}`} alt="Sandbox Screenshot" className="w-full h-auto opacity-80 group-hover:opacity-100 transition" />
                        <div className="absolute bottom-2 right-2 bg-black/80 px-2 py-1 rounded text-xs">Final DOM Render</div>
                      </div>
                    ) : (
                      <div className="h-64 bg-black/20 rounded flex items-center justify-center text-sm text-gray-500 border border-white/5 border-dashed">
                        No screenshot available
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500 italic">Waiting for sandbox events...</div>
              )}
            </div>
          ) : (
            <div className="text-sm text-gray-500">Sandbox not triggered for this investigation (Risk too low or still processing).</div>
          )}
        </div>
      </div>
    </div>
  );
};

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-background text-foreground flex">
          {/* Sidebar */}
          <aside className="w-64 border-r border-white/10 flex flex-col glass-panel !border-l-0 !border-t-0 !border-b-0 !rounded-none">
            <div className="p-6 flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary" />
              <span className="text-xl font-bold tracking-tight">ThreatLens</span>
            </div>
            <nav className="flex-1 px-4 space-y-2 mt-4">
              <Link to="/" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition text-sm font-medium">
                <LayoutDashboard className="w-4 h-4 text-gray-400" />
                Dashboard
              </Link>
              <Link to="/investigate" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition text-sm font-medium">
                <Search className="w-4 h-4 text-gray-400" />
                Investigate
              </Link>
              <Link to="/investigations" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition text-sm font-medium">
                <Activity className="w-4 h-4 text-gray-400" />
                Active Cases
              </Link>
              <Link to="/threat-reports" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition text-sm font-medium">
                <FileWarning className="w-4 h-4 text-gray-400" />
                Threat Reports
              </Link>
            </nav>
            <div className="p-6 text-xs text-gray-500">
              Risk-Adaptive Analysis Engine v1.0
            </div>
          </aside>

// Threat Reports Component
const ThreatReports = () => {
  const { data: alerts } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => fetch('/api/investigations/reports/alerts').then(res => res.json()),
    refetchInterval: 5000
  });

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold mb-6">Threat Escalations & Reports</h1>
      <div className="grid grid-cols-1 gap-4">
        {alerts?.map((alert: any, idx: number) => (
          <div key={idx} className="glass-panel p-6 border-l-4" style={{borderLeftColor: alert.severity === 'CRITICAL' ? '#ef4444' : '#f97316'}}>
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-bold">{alert.title}</h3>
              <span className="text-xs bg-black/40 px-2 py-1 rounded text-gray-400">{new Date(alert.created_at).toLocaleString()}</span>
            </div>
            <p className="text-gray-300 text-sm mb-4">{alert.description}</p>
            <div className="flex justify-between items-center">
              <span className={`text-xs font-semibold px-2 py-1 rounded ${alert.status === 'OPEN' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                {alert.status}
              </span>
              <Link to={`/investigations/${alert.investigation_id}`} className="text-sm text-primary hover:underline">View Investigation →</Link>
            </div>
          </div>
        ))}
        {(!alerts || alerts.length === 0) && <div className="text-gray-500 italic">No active escalations.</div>}
      </div>
    </div>
  );
};

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/investigate" element={<Investigate />} />
              <Route path="/investigations" element={<div className="p-8">Active Investigations List</div>} />
              <Route path="/investigations/:id" element={<InvestigationDetails />} />
              <Route path="/threat-reports" element={<ThreatReports />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
