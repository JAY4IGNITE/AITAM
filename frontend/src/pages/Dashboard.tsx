import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, AlertTriangle, Search, Shield, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard = () => {
  // In a real app, these would come from an aggregated /api/dashboard endpoint
  // For the hackathon, we simulate some real-time metrics
  const { data: investigations } = useQuery({
    queryKey: ['recent-investigations'],
    queryFn: () => fetch('/api/investigations').then(res => res.json()).catch(() => []),
    refetchInterval: 10000
  });

  const { data: incidents } = useQuery({
    queryKey: ['recent-incidents'],
    queryFn: () => fetch('/api/incidents/').then(res => res.json()).catch(() => []),
    refetchInterval: 10000
  });

  const activeCount = investigations?.filter((i: any) => i.status !== 'COMPLETED' && i.status !== 'FAILED').length || 0;
  const criticalIncidents = incidents?.filter((i: any) => i.severity === 'CRITICAL' && i.status === 'INVESTIGATING').length || 0;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">SOC Dashboard</h1>
          <p className="text-gray-400 mt-1">Real-time threat investigation and intelligence overview.</p>
        </div>
        <Link 
          to="/analyze" 
          className="bg-primary text-primary-foreground font-semibold px-6 py-2.5 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center gap-2"
        >
          <Search className="w-4 h-4" />
          New Investigation
        </Link>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="Total Investigations" 
          value={investigations?.length ?? 0} 
          subtitle="All time"
          icon={Search}
          color="text-blue-500"
          bg="bg-blue-500/10"
        />
        <MetricCard 
          title="Active Analysis" 
          value={activeCount ?? 0} 
          subtitle="Agents running"
          icon={Activity}
          color="text-green-500"
          bg="bg-green-500/10"
          pulse
        />
        <MetricCard 
          title="Critical Threats" 
          value={criticalIncidents ?? 0} 
          subtitle="Require immediate action"
          icon={AlertTriangle}
          color="text-red-500"
          bg="bg-red-500/10"
        />
        <MetricCard 
          title="Automated Responses" 
          value={0} 
          subtitle="DNS & Email blocks"
          icon={Shield}
          color="text-purple-500"
          bg="bg-purple-500/10"
        />
      </div>

      {/* Threat Activity */}
      <div className="glass-panel p-6 border border-white/5">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold">Threat Activity</h2>
            <p className="text-sm text-gray-500">Volume of malicious indicators detected over 24h</p>
          </div>
        </div>
        <div className="h-64 flex items-center justify-center border border-white/5 border-dashed rounded bg-black/20">
          <div className="text-center text-gray-500 flex flex-col items-center">
            <Zap className="w-8 h-8 mb-2 opacity-50" />
            <p>Threat chart rendering engine initialized.</p>
            <p className="text-xs mt-1">(Aggregated timeline data will appear here)</p>
          </div>
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
