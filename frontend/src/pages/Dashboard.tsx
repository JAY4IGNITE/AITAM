import { useQuery } from '@tanstack/react-query';
import { 
  Activity, AlertTriangle, Search, Shield, Zap, GlobeLock, 
  MonitorPlay, FileWarning, ArrowRight, ShieldCheck, Cpu,
  Terminal, Sparkles, Server, Radio, Clock, ExternalLink, Play
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export const Dashboard = () => {
  const navigate = useNavigate();

  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const res = await fetch('/api/dashboard/stats');
      if (!res.ok) throw new Error('Failed to fetch dashboard stats');
      return res.json();
    },
    refetchInterval: 4000
  });

  const { data: recentInvs } = useQuery({
    queryKey: ['dashboard-recent-cases'],
    queryFn: async () => {
      const res = await fetch('/api/investigations/?limit=6');
      if (!res.ok) return { items: [] };
      return res.json();
    },
    refetchInterval: 4000
  });

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-8 animate-in fade-in duration-300">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Security Operations</h1>
            <span className="bg-zinc-800 text-zinc-300 border border-zinc-700 text-[10px] px-2 py-0.5 rounded font-mono font-medium">
              Autonomous Swarm
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Real-time multi-agent threat investigation, threat intelligence, and zero-trust sandbox execution.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            to="/agent-control"
            className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-200 px-3.5 py-2 rounded-md transition text-xs font-medium flex items-center gap-2"
          >
            <Cpu className="w-3.5 h-3.5 text-zinc-400" />
            <span>Agent Control</span>
          </Link>
          <Link
            to="/analyze"
            className="bg-white hover:bg-zinc-200 text-zinc-950 font-semibold px-4 py-2 rounded-md transition text-xs flex items-center gap-2"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>New Investigation</span>
          </Link>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="Total Investigations" 
          value={stats?.total_investigations ?? 0} 
          subtitle="All vectors processed"
          icon={Search}
        />
        <MetricCard 
          title="Active Autonomous Runs" 
          value={stats?.active_analysis_count ?? 0} 
          subtitle="Concurrent agent swarms"
          icon={Activity}
          highlight={stats?.active_analysis_count > 0}
        />
        <MetricCard 
          title="Critical & High Incidents" 
          value={(stats?.critical_count || 0) + (stats?.high_count || 0)} 
          subtitle={`${stats?.critical_count || 0} Critical, ${stats?.high_count || 0} High`}
          icon={AlertTriangle}
          alert={(stats?.critical_count || 0) > 0}
        />
        <MetricCard 
          title="Threat Intel Hits" 
          value={stats?.threat_intel_matches ?? 0} 
          subtitle="Safe Browsing & URLhaus"
          icon={GlobeLock}
        />
      </div>

      {/* Autonomous Agent Status Matrix */}
      <div className="glass-panel p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">
            <Radio className="w-3.5 h-3.5 text-zinc-400" />
            <span>Autonomous AI Agent Network</span>
          </div>
          <Link to="/agent-control" className="text-xs text-zinc-400 hover:text-white flex items-center gap-1">
            View Live Graph <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { name: 'SOC Orchestrator', role: 'Master Dispatch', status: 'ONLINE', latency: '4ms' },
            { name: 'Triage Agent', role: 'P1-P4 Classifier', status: 'READY', latency: '12ms' },
            { name: 'URL Intelligence', role: 'Punycode & TLDs', status: 'ACTIVE', latency: '24ms' },
            { name: 'Safe Browsing Tool', role: 'Google API v4', status: 'SYNCED', latency: '65ms' },
            { name: 'Evidence Fusion', role: 'IoC Correlation', status: 'READY', latency: '18ms' },
            { name: 'Risk Evaluation', role: '0-100 Scoring', status: 'ACTIVE', latency: '15ms' },
          ].map((agent, i) => (
            <div key={i} className="bg-zinc-900/60 border border-zinc-800 p-3 rounded-md space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-200 truncate">{agent.name}</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              </div>
              <div className="text-[10px] text-zinc-400">{agent.role}</div>
              <div className="flex items-center justify-between pt-1 border-t border-zinc-800/60 text-[10px] font-mono text-zinc-400">
                <span className="text-zinc-300 font-semibold">{agent.status}</span>
                <span>{agent.latency}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Grid: Activity Timeline + Recent Cases */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left 7 Cols: Threat Density Timeline */}
        <div className="lg:col-span-7 glass-panel p-5 flex flex-col justify-between space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
                <Zap className="w-3.5 h-3.5 text-zinc-400" />
                <span>Threat Ingestion Activity (24h)</span>
              </h2>
            </div>
            <span className="text-[11px] font-mono text-zinc-400">
              6h Windows
            </span>
          </div>

          <div className="h-48 flex items-end justify-between gap-3 pt-4 border-b border-zinc-800/80 px-2">
            {stats?.threat_trend_24h?.length ? (
              stats.threat_trend_24h.map((point: any, idx: number) => {
                const heightPct = Math.min(100, Math.max(15, (point.count / Math.max(...stats.threat_trend_24h.map((p: any) => p.count || 1))) * 100));
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 group h-full justify-end">
                    <div className="text-[10px] font-mono text-zinc-400 opacity-0 group-hover:opacity-100 transition">
                      {point.count}
                    </div>
                    <div 
                      className="w-full bg-zinc-700 hover:bg-zinc-500 rounded-t transition-all duration-200"
                      style={{ height: `${heightPct}%` }}
                    />
                    <div className="text-[10px] font-mono text-zinc-400 truncate w-full text-center">
                      {point.time_window}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="w-full h-full flex items-center justify-center text-xs font-mono text-zinc-400">
                Awaiting telemetry streams...
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span>Quick Detonate:</span>
            <div className="flex gap-2">
              <Link to="/analyze" className="bg-zinc-900 hover:bg-zinc-800 text-zinc-300 px-2.5 py-1 rounded border border-zinc-800 transition">
                URL
              </Link>
              <Link to="/email-scanner" className="bg-zinc-900 hover:bg-zinc-800 text-zinc-300 px-2.5 py-1 rounded border border-zinc-800 transition">
                Email / TempMail
              </Link>
              <Link to="/analyze" className="bg-zinc-900 hover:bg-zinc-800 text-zinc-300 px-2.5 py-1 rounded border border-zinc-800 transition">
                SMS / QR
              </Link>
            </div>
          </div>
        </div>

        {/* Right 5 Cols: Recent Cases */}
        <div className="lg:col-span-5 glass-panel p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">
              <Shield className="w-3.5 h-3.5 text-zinc-400" />
              <span>Recent Cases</span>
            </div>
            <Link to="/investigations" className="text-xs text-zinc-400 hover:text-white">
              View All ({stats?.total_investigations ?? 0})
            </Link>
          </div>

          <div className="space-y-2">
            {!recentInvs?.items?.length ? (
              <div className="py-8 text-center text-xs font-mono text-zinc-400">No active cases in queue.</div>
            ) : (
              recentInvs.items.map((inv: any) => {
                const score = inv.final_risk_score ?? inv.initial_risk_score ?? 0;
                return (
                  <Link
                    key={inv.id}
                    to={`/investigations/${inv.id}`}
                    className="glass-panel-interactive p-2.5 flex items-center justify-between gap-3 text-xs block"
                  >
                    <div className="space-y-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white font-mono">{inv.display_id}</span>
                        <span className="bg-zinc-900 border border-zinc-800 px-1.5 py-0.2 rounded text-[10px] font-mono text-zinc-400">
                          {inv.input_type}
                        </span>
                      </div>
                      <div className="text-zinc-400 font-mono truncate text-[11px] max-w-[200px]">
                        {inv.target}
                      </div>
                    </div>

                    <div className="text-right flex items-center gap-2.5 shrink-0">
                      <div>
                        <div className="font-mono font-bold text-xs text-white">
                          {score}/100
                        </div>
                        <div className="text-[9px] font-mono text-zinc-400 uppercase">
                          {inv.classification || inv.status}
                        </div>
                      </div>
                      <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </div>

      </div>

    </div>
  );
};

const MetricCard = ({ title, value, subtitle, icon: Icon, highlight, alert }: any) => (
  <div className={`glass-panel p-4 space-y-2 ${highlight ? 'border-zinc-700' : ''} ${alert ? 'border-zinc-700' : ''}`}>
    <div className="flex items-center justify-between text-zinc-400">
      <span className="text-xs font-medium uppercase tracking-wider">{title}</span>
      <div className="p-1.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300">
        <Icon className="w-3.5 h-3.5" />
      </div>
    </div>
    <div className="text-2xl font-bold text-white tracking-tight font-mono">{value}</div>
    <div className="text-xs text-zinc-400">{subtitle}</div>
  </div>
);
