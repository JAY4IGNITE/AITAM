import { useQuery } from '@tanstack/react-query';
import { 
  Activity, AlertTriangle, Search, Shield, Zap, GlobeLock, 
  MonitorPlay, FileWarning, ArrowRight, ShieldCheck
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const res = await fetch('/api/dashboard/stats');
      if (!res.ok) throw new Error('Failed to fetch dashboard stats');
      return res.json();
    },
    refetchInterval: 5000
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight text-white">SOC Command Center</h1>
            <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> LIVE
            </span>
          </div>
          <p className="text-gray-400 mt-1">Autonomous multi-agent threat investigation, threat intelligence, and sandbox detonation platform.</p>
        </div>
        <div className="flex items-center gap-3">
          <Link 
            to="/threat-intel" 
            className="bg-white/5 border border-white/10 hover:bg-white/10 text-gray-300 font-semibold px-4 py-2.5 rounded-md transition text-sm flex items-center gap-2"
          >
            <GlobeLock className="w-4 h-4 text-primary" />
            Threat Database
          </Link>
          <Link 
            to="/analyze" 
            className="bg-primary text-primary-foreground font-semibold px-6 py-2.5 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center gap-2 text-sm"
          >
            <Search className="w-4 h-4" />
            New Investigation
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="Total Investigations" 
          value={stats?.total_investigations ?? 0} 
          subtitle="All vectors processed"
          icon={Search}
          color="text-blue-500"
          bg="bg-blue-500/10"
        />
        <MetricCard 
          title="Active Analysis" 
          value={stats?.active_analysis_count ?? 0} 
          subtitle="Multi-agent pipelines running"
          icon={Activity}
          color="text-emerald-500"
          bg="bg-emerald-500/10"
          pulse={stats?.active_analysis_count > 0}
        />
        <MetricCard 
          title="Critical / High Threats" 
          value={(stats?.critical_count || 0) + (stats?.high_count || 0)} 
          subtitle={`${stats?.critical_count || 0} Critical, ${stats?.high_count || 0} High`}
          icon={AlertTriangle}
          color="text-red-500"
          bg="bg-red-500/10"
        />
        <MetricCard 
          title="Threat Intel Matches" 
          value={stats?.threat_intel_matches ?? 0} 
          subtitle="URLhaus & vendor IoC detections"
          icon={GlobeLock}
          color="text-amber-500"
          bg="bg-amber-500/10"
        />
      </div>

      {/* Secondary Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-4 border border-white/5 flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg">
            <MonitorPlay className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats?.sandbox_executions ?? 0}</div>
            <div className="text-xs text-gray-400 font-medium">Adaptive Sandbox Detonations</div>
          </div>
        </div>

        <div className="glass-panel p-4 border border-white/5 flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats?.safe_count ?? 0}</div>
            <div className="text-xs text-gray-400 font-medium">Verified Clean / Safe Artifacts</div>
          </div>
        </div>

        <div className="glass-panel p-4 border border-white/5 flex items-center gap-4">
          <div className="p-3 bg-rose-500/10 text-rose-400 rounded-lg">
            <FileWarning className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats?.pending_reports ?? 0}</div>
            <div className="text-xs text-gray-400 font-medium">Pending Community Threat Reports</div>
          </div>
        </div>
      </div>

      {/* Threat Distribution & 24h Activity Graph */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* 24h Activity Visual Chart */}
        <div className="lg:col-span-8 glass-panel p-6 border border-white/5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Zap className="w-5 h-5 text-primary" /> Threat Ingestion & Investigation Timeline (24h)
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">Aggregated investigation volume and malicious detection density</p>
            </div>
            <span className="text-xs font-mono bg-black/40 px-2.5 py-1 rounded border border-white/10 text-gray-400">
              6h Windows
            </span>
          </div>

          <div className="h-56 flex items-end justify-between gap-4 pt-6 border-b border-white/10 px-4">
            {stats?.threat_trend_24h?.length ? (
              stats.threat_trend_24h.map((point: any, idx: number) => {
                const maxVal = Math.max(...stats.threat_trend_24h.map((p: any) => p.count), 5);
                const heightPct = Math.max(12, Math.round((point.count / maxVal) * 100));
                
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-2 group h-full justify-end">
                    <div className="text-[11px] font-mono text-gray-400 opacity-0 group-hover:opacity-100 transition">
                      {point.count} cases ({point.malicious} mal)
                    </div>
                    <div className="w-full max-w-[48px] bg-black/40 rounded-t border border-white/10 flex flex-col justify-end overflow-hidden" style={{ height: `${heightPct}%` }}>
                      {point.malicious > 0 && (
                        <div 
                          className="bg-red-500/80 w-full transition-all" 
                          style={{ height: `${(point.malicious / (point.count || 1)) * 100}%` }}
                          title={`${point.malicious} Malicious`}
                        />
                      )}
                      {point.suspicious > 0 && (
                        <div 
                          className="bg-amber-500/80 w-full transition-all" 
                          style={{ height: `${(point.suspicious / (point.count || 1)) * 100}%` }}
                          title={`${point.suspicious} Suspicious`}
                        />
                      )}
                      <div 
                        className="bg-primary/60 w-full transition-all" 
                        style={{ height: `${(point.safe / (point.count || 1)) * 100}%` }}
                        title={`${point.safe} Safe / Clean`}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-gray-500">{point.timestamp}</span>
                  </div>
                );
              })
            ) : (
              <div className="w-full text-center text-gray-500 py-12">
                No activity detected in the last 24h timeframe.
              </div>
            )}
          </div>

          <div className="flex items-center justify-center gap-6 mt-4 text-xs font-medium text-gray-400">
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-red-500/80"></span> High / Critical</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-amber-500/80"></span> Medium / Suspicious</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-primary/60"></span> Clean / Safe</span>
          </div>
        </div>

        {/* Risk Distribution Breakdown */}
        <div className="lg:col-span-4 glass-panel p-6 border border-white/5 flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-white mb-1">Threat Classification</h2>
            <p className="text-xs text-gray-400 mb-6">Distribution across severity levels</p>
            
            <div className="space-y-4">
              <RiskRow label="Critical (80-100)" count={stats?.critical_count || 0} total={stats?.total_investigations || 1} color="bg-red-500" text="text-red-400" />
              <RiskRow label="High (60-79)" count={stats?.high_count || 0} total={stats?.total_investigations || 1} color="bg-orange-500" text="text-orange-400" />
              <RiskRow label="Medium (40-59)" count={stats?.medium_count || 0} total={stats?.total_investigations || 1} color="bg-yellow-500" text="text-yellow-400" />
              <RiskRow label="Low (20-39)" count={stats?.low_count || 0} total={stats?.total_investigations || 1} color="bg-blue-500" text="text-blue-400" />
              <RiskRow label="Safe (0-19)" count={stats?.safe_count || 0} total={stats?.total_investigations || 1} color="bg-green-500" text="text-green-400" />
              <RiskRow label="Unknown" count={stats?.unknown_count || 0} total={stats?.total_investigations || 1} color="bg-gray-500" text="text-gray-400" />
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-white/5 text-center">
            <Link to="/investigations" className="text-primary hover:underline text-xs font-semibold flex items-center justify-center gap-1">
              View all investigation records <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Investigations Table */}
      <div className="glass-panel p-6 border border-white/5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white">Recent Investigations</h2>
            <p className="text-xs text-gray-400">Latest threat items submitted for multi-agent evaluation</p>
          </div>
          <Link to="/investigations" className="text-xs text-primary hover:underline font-semibold flex items-center gap-1">
            Full Case List <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-white/5 text-gray-400 uppercase tracking-wider font-sans text-[11px]">
              <tr>
                <th className="px-4 py-3">Case ID</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Target</th>
                <th className="px-4 py-3">Risk Level</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                <tr><td colSpan={7} className="text-center py-8 text-gray-500">Loading cases...</td></tr>
              ) : stats?.recent_investigations?.length ? (
                stats.recent_investigations.map((item: any) => (
                  <tr key={item.id} className="hover:bg-white/5 transition">
                    <td className="px-4 py-3 font-bold text-white">
                      <Link to={`/investigations/${item.id}`} className="text-primary hover:underline">{item.display_id}</Link>
                    </td>
                    <td className="px-4 py-3 font-sans text-gray-300">{item.input_type}</td>
                    <td className="px-4 py-3 text-gray-400 max-w-xs truncate" title={item.target}>{item.target}</td>
                    <td className="px-4 py-3 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.classification === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        item.classification === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                        item.classification === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                        item.classification === 'LOW' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                        item.classification === 'SAFE' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {item.classification} {item.final_risk_score != null ? `(${item.final_risk_score})` : ''}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] ${
                        item.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400' :
                        item.status === 'FAILED' ? 'bg-red-500/10 text-red-400' :
                        'bg-blue-500/10 text-blue-400 animate-pulse'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-sans">{new Date(item.created_at).toLocaleTimeString()}</td>
                    <td className="px-4 py-3 text-right font-sans">
                      <Link to={`/investigations/${item.id}`} className="text-primary hover:underline font-semibold">Inspect →</Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={7} className="text-center py-8 text-gray-500">No recent investigations found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
    </div>
  );
};

const MetricCard = ({ title, value, subtitle, icon: Icon, color, bg, pulse }: any) => (
  <div className="glass-panel p-5 border border-white/5 flex flex-col justify-between">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-2.5 rounded-md ${bg}`}>
        <Icon className={`w-5 h-5 ${color} ${pulse ? 'animate-pulse' : ''}`} />
      </div>
    </div>
    <div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm font-semibold text-gray-300">{title}</div>
      <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
    </div>
  </div>
);

const RiskRow = ({ label, count, total, color, text }: any) => {
  const pct = Math.round((count / (total || 1)) * 100);
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className={text}>{label}</span>
        <span className="text-gray-400 font-mono">{count} ({pct}%)</span>
      </div>
      <div className="w-full bg-black/40 h-2 rounded-full overflow-hidden border border-white/5">
        <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }}></div>
      </div>
    </div>
  );
};
