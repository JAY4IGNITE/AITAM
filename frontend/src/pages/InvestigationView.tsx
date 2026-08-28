import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { AlertTriangle, Download, Activity, MonitorPlay } from 'lucide-react';

import { InvestigationTimeline } from '../components/ui/InvestigationTimeline';
import { AgentActivity } from '../components/ui/AgentActivity';
import { RiskScore } from '../components/ui/RiskScore';
import { AttackJourney } from '../components/ui/AttackJourney';
import { EvidenceGraph } from '../components/ui/EvidenceGraph';
import { SandboxPanel } from '../components/ui/SandboxPanel';

export const InvestigationView = () => {
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

  const { data: autonomous } = useQuery({
    queryKey: ['autonomous', id],
    queryFn: () => fetch(`/api/investigations/${id}/autonomous`).then(res => res.json()),
    enabled: !!inv
  });

  const { data: journey } = useQuery({
    queryKey: ['journey', id],
    queryFn: () => fetch(`/api/investigations/${id}/journey`).then(res => res.json()),
    enabled: inv?.status === 'COMPLETED'
  });

  const { data: graph } = useQuery({
    queryKey: ['graph', id],
    queryFn: () => fetch(`/api/investigations/${id}/graph`).then(res => res.json()),
    enabled: inv?.status === 'COMPLETED'
  });

  if (!inv) return <div className="p-8 text-gray-500 animate-pulse">Loading investigation data...</div>;

  return (
    <div className="p-8 max-w-[1600px] mx-auto space-y-6 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <h1 className="text-3xl font-bold tracking-tight text-white">{inv.display_id}</h1>
            <span className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wider ${
              inv.status === 'COMPLETED' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
              inv.status === 'FAILED' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
              'bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse'
            }`}>
              {inv.status}
            </span>
            {autonomous?.triage && (
              <span className={`px-3 py-1 text-xs font-bold rounded uppercase tracking-wider ${
                autonomous.triage.priority === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
              }`}>
                {autonomous.triage.priority} PRIORITY
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="font-mono bg-black/40 px-2 py-0.5 rounded border border-white/5">{inv.input_type}</span>
            <span className="truncate max-w-xl">{inv.target}</span>
          </div>
        </div>
        
        <div className="flex gap-3">
          {autonomous?.response && (
            <Link 
              to="/incidents"
              className={`px-4 py-2 rounded-md font-bold text-sm flex items-center gap-2 transition ${
                autonomous.response.action === 'BLOCK' ? 'bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20' :
                'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500/20'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
              RECOMMENDED ACTION: {autonomous.response.action}
            </Link>
          )}
          <button 
            className="flex items-center gap-2 bg-white/5 border border-white/10 text-gray-300 px-4 py-2 rounded-md hover:bg-white/10 transition disabled:opacity-50 text-sm font-semibold"
            disabled={inv.status !== 'COMPLETED'}
          >
            <Download className="w-4 h-4" /> Export Report
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Timeline & Agents */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-panel p-6">
            <h2 className="text-lg font-bold mb-6 flex items-center gap-2 uppercase tracking-wide">
              <Activity className="w-5 h-5 text-primary" />
              Investigation Pipeline
            </h2>
            <InvestigationTimeline investigation={inv} />
          </div>
          
          <div className="glass-panel p-6">
            <h2 className="text-lg font-bold mb-4 uppercase tracking-wide">Agent Activity</h2>
            <AgentActivity agents={agents} />
          </div>
        </div>

        {/* Middle & Right Column: Risk, Attack Journey, Evidence, Sandbox */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Risk Score Row */}
          <div className="glass-panel p-6">
            <RiskScore risk={risk} />
          </div>
          
          {/* Attack Journey & Graph Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass-panel p-6">
              <h2 className="text-lg font-bold mb-4 uppercase tracking-wide">Attack Journey</h2>
              <AttackJourney journey={journey} />
            </div>
            
            <div className="glass-panel p-6">
              <h2 className="text-lg font-bold mb-4 uppercase tracking-wide">Evidence Graph</h2>
              <EvidenceGraph graph={graph} />
            </div>
          </div>

          {/* Sandbox Analysis Panel */}
          <div className="glass-panel p-6">
            <h2 className="text-lg font-bold mb-4 uppercase tracking-wide flex items-center gap-2">
              <MonitorPlay className="w-5 h-5 text-gray-400" />
              Isolated Browser Analysis
            </h2>
            <SandboxPanel investigationId={id!} />
          </div>
          
        </div>
      </div>
    </div>
  );
};
