import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { 
  Activity, Search, Filter, ChevronLeft, ChevronRight,
  Globe, Mail, MessageSquare, QrCode, Monitor, Share2, AlertTriangle, CheckCircle, Clock
} from 'lucide-react';

export const InvestigationsList = () => {
  const [page, setPage] = useState(1);
  const [inputType, setInputType] = useState('');
  const [status, setStatus] = useState('');
  const [classification, setClassification] = useState('');
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['investigations-list', page, inputType, status, classification, search],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '15',
        ...(inputType ? { input_type: inputType } : {}),
        ...(status ? { status } : {}),
        ...(classification ? { classification } : {}),
        ...(search ? { search } : {})
      });
      const res = await fetch(`/api/investigations?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to fetch investigations');
      return res.json();
    },
    refetchInterval: 5000
  });

  const getRiskBadge = (cls?: string, score?: number) => {
    switch (cls) {
      case 'CRITICAL':
        return <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-2.5 py-1 rounded text-xs font-bold">CRITICAL ({score ?? 85})</span>;
      case 'HIGH':
        return <span className="bg-orange-500/20 text-orange-400 border border-orange-500/30 px-2.5 py-1 rounded text-xs font-bold">HIGH ({score ?? 65})</span>;
      case 'MEDIUM':
      case 'SUSPICIOUS':
        return <span className="bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2.5 py-1 rounded text-xs font-bold">MEDIUM ({score ?? 45})</span>;
      case 'LOW':
        return <span className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2.5 py-1 rounded text-xs font-bold">LOW ({score ?? 25})</span>;
      case 'SAFE':
        return <span className="bg-green-500/20 text-green-400 border border-green-500/30 px-2.5 py-1 rounded text-xs font-bold">SAFE ({score ?? 5})</span>;
      default:
        return <span className="bg-gray-500/20 text-gray-400 border border-gray-500/30 px-2.5 py-1 rounded text-xs font-bold">UNKNOWN</span>;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'URL': return <Globe className="w-4 h-4 text-blue-400" />;
      case 'EMAIL': return <Mail className="w-4 h-4 text-purple-400" />;
      case 'SMS': return <MessageSquare className="w-4 h-4 text-emerald-400" />;
      case 'QR': return <QrCode className="w-4 h-4 text-amber-400" />;
      case 'WEBPAGE': return <Monitor className="w-4 h-4 text-cyan-400" />;
      case 'SOCIAL': return <Share2 className="w-4 h-4 text-pink-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary" />
            Investigation Cases
          </h1>
          <p className="text-gray-400 mt-1">Review all autonomous multi-agent threat investigation records.</p>
        </div>
        <Link 
          to="/analyze" 
          className="bg-primary text-primary-foreground font-semibold px-6 py-2.5 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center gap-2"
        >
          <Search className="w-4 h-4" />
          New Investigation
        </Link>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel p-4 border border-white/10 flex flex-wrap items-center gap-4">
        <div className="flex-1 min-w-[240px] relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-500" />
          <input
            type="text"
            placeholder="Search by target or Display ID..."
            className="w-full bg-black/40 border border-white/10 rounded-md pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-primary/50"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>

        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-gray-500" />
          
          <select 
            className="bg-black/40 border border-white/10 rounded-md px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-primary/50"
            value={inputType}
            onChange={(e) => { setInputType(e.target.value); setPage(1); }}
          >
            <option value="">All Input Types</option>
            <option value="URL">URL</option>
            <option value="EMAIL">Email</option>
            <option value="SMS">SMS</option>
            <option value="QR">QR Code</option>
            <option value="WEBPAGE">Web Page</option>
            <option value="SOCIAL">Social</option>
          </select>

          <select 
            className="bg-black/40 border border-white/10 rounded-md px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-primary/50"
            value={classification}
            onChange={(e) => { setClassification(e.target.value); setPage(1); }}
          >
            <option value="">All Risk Levels</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium / Suspicious</option>
            <option value="LOW">Low</option>
            <option value="SAFE">Safe</option>
          </select>

          <select 
            className="bg-black/40 border border-white/10 rounded-md px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-primary/50"
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          >
            <option value="">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="AGENT_ANALYSIS">Analyzing</option>
            <option value="QUEUED">Queued</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-panel overflow-hidden border border-white/10">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 border-b border-white/10 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-4">Case ID</th>
                <th className="px-6 py-4">Type</th>
                <th className="px-6 py-4">Target Artifact</th>
                <th className="px-6 py-4">Risk Level</th>
                <th className="px-6 py-4">Status / Stage</th>
                <th className="px-6 py-4">Sandbox</th>
                <th className="px-6 py-4">Created</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono text-xs">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                    Loading investigations...
                  </td>
                </tr>
              ) : data?.items?.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                    No investigations found matching your filter criteria.
                  </td>
                </tr>
              ) : (
                data?.items?.map((item: any) => (
                  <tr key={item.id} className="hover:bg-white/5 transition">
                    <td className="px-6 py-4 font-bold text-white">
                      <Link to={`/investigations/${item.id}`} className="text-primary hover:underline">
                        {item.display_id}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-2 text-gray-300 font-sans font-medium">
                        {getTypeIcon(item.input_type)}
                        {item.input_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 max-w-xs truncate text-gray-400 font-mono" title={item.target}>
                      {item.target}
                    </td>
                    <td className="px-6 py-4 font-sans">
                      {getRiskBadge(item.classification, item.final_risk_score)}
                    </td>
                    <td className="px-6 py-4 font-sans">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold ${
                        item.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400' :
                        item.status === 'FAILED' ? 'bg-red-500/10 text-red-400' :
                        'bg-blue-500/10 text-blue-400 animate-pulse'
                      }`}>
                        {item.status === 'COMPLETED' && <CheckCircle className="w-3 h-3" />}
                        {item.status === 'FAILED' && <AlertTriangle className="w-3 h-3" />}
                        {item.status !== 'COMPLETED' && item.status !== 'FAILED' && <Clock className="w-3 h-3" />}
                        {item.current_stage || item.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-sans">
                      <span className={`text-[11px] px-2 py-0.5 rounded font-medium ${
                        item.sandbox_status === 'COMPLETED' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'text-gray-600'
                      }`}>
                        {item.sandbox_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-500 font-sans">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right font-sans">
                      <Link
                        to={`/investigations/${item.id}`}
                        className="bg-white/5 hover:bg-white/10 text-gray-300 px-3 py-1.5 rounded text-xs font-semibold transition"
                      >
                        View Case →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {data && data.pages > 1 && (
          <div className="p-4 border-t border-white/10 flex items-center justify-between text-xs text-gray-400">
            <div>
              Showing page <span className="text-white font-bold">{data.page}</span> of <span className="text-white font-bold">{data.pages}</span> ({data.total} total cases)
            </div>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="bg-white/5 px-3 py-1.5 rounded border border-white/10 disabled:opacity-30 hover:bg-white/10 flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Previous
              </button>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage(p => p + 1)}
                className="bg-white/5 px-3 py-1.5 rounded border border-white/10 disabled:opacity-30 hover:bg-white/10 flex items-center gap-1"
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};
