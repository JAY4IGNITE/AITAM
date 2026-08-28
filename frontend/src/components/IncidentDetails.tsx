import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ShieldAlert, CheckCircle2, XCircle, Clock, Search, Shield, ChevronRight } from 'lucide-react';

export const IncidentDetails = () => {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [approving, setApproving] = useState(false);
  
  const { data: incident } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => fetch(`/api/incidents/${id}`).then(res => res.json())
  });

  const { data: actions } = useQuery({
    queryKey: ['incident-actions', id],
    queryFn: () => fetch(`/api/incidents/${id}/actions`).then(res => res.json()),
    enabled: !!incident
  });

  const approveMutation = useMutation({
    mutationFn: (actionId: string) => fetch(`/api/incidents/${id}/actions/${actionId}/approve`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incident-actions', id] });
      setApproving(false);
    }
  });

  if (!incident) return <div className="p-8 text-gray-500 animate-pulse">Loading incident details...</div>;

  const severityColor = 
    incident.severity === 'CRITICAL' ? 'text-red-500 bg-red-500/10 border-red-500/20' :
    incident.severity === 'HIGH' ? 'text-orange-500 bg-orange-500/10 border-orange-500/20' :
    incident.severity === 'MEDIUM' ? 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20' :
    'text-blue-500 bg-blue-500/10 border-blue-500/20';

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start gap-4 mb-2 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold tracking-tight text-white">{incident.title}</h1>
            <span className={`px-2 py-1 text-xs font-bold uppercase tracking-wider rounded border ${severityColor}`}>
              {incident.severity}
            </span>
          </div>
          <div className="text-sm text-gray-400 font-mono flex items-center gap-2">
            ID: <span className="text-gray-300">{incident.display_id}</span>
            <span className="text-white/20">|</span>
            Created: <span className="text-gray-300">{new Date(incident.created_at).toLocaleString()}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Link to={`/investigations/${incident.investigation_id}`} className="bg-primary/20 text-primary hover:bg-primary/30 border border-primary/30 px-4 py-2 rounded-md font-semibold text-sm transition flex items-center gap-2">
            <Search className="w-4 h-4" /> View Investigation
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6 border border-white/5">
            <h2 className="text-lg font-bold mb-4 uppercase tracking-wide flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-gray-400" /> Executive Summary
            </h2>
            <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{incident.summary}</p>
          </div>
          
          <div className="glass-panel p-6 border border-white/5">
            <h2 className="text-lg font-bold mb-4 uppercase tracking-wide">Incident Timeline</h2>
            <div className="space-y-4">
              <TimelineEvent time={incident.created_at} title="Incident Created" desc="Autonomously created by SOC logic." icon={ShieldAlert} color="text-red-400" />
              {actions?.map((act: any, i: number) => (
                <TimelineEvent 
                  key={i} 
                  time={act.updated_at || act.created_at} 
                  title={`Action: ${act.action_type}`} 
                  desc={act.status} 
                  icon={act.status === 'EXECUTED' ? CheckCircle2 : Clock} 
                  color={act.status === 'EXECUTED' ? 'text-green-400' : 'text-yellow-400'} 
                />
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar Actions */}
        <div className="space-y-6">
          <div className="glass-panel p-6 border border-white/5">
            <h2 className="text-lg font-bold mb-4 uppercase tracking-wide flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" /> Response Actions
            </h2>
            
            {actions?.length > 0 ? (
              <div className="space-y-4">
                {actions.map((act: any) => (
                  <div key={act.id} className="bg-black/40 border border-white/10 p-4 rounded-lg shadow-xl">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-bold text-gray-200">{act.action_type}</h3>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                        act.status === 'PENDING_APPROVAL' ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' : 
                        act.status === 'EXECUTED' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 
                        'bg-gray-500/10 text-gray-400 border-gray-500/20'
                      }`}>
                        {act.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mb-4">{act.description}</p>
                    
                    {act.status === 'PENDING_APPROVAL' && (
                      <div className="flex gap-2">
                        <button 
                          className="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/50 py-1.5 rounded text-xs font-bold transition flex items-center justify-center gap-1 disabled:opacity-50"
                          onClick={() => { setApproving(true); approveMutation.mutate(act.id); }}
                          disabled={approving}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> APPROVE
                        </button>
                        <button 
                          className="flex-1 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/50 py-1.5 rounded text-xs font-bold transition flex items-center justify-center gap-1"
                          disabled={approving}
                        >
                          <XCircle className="w-3.5 h-3.5" /> REJECT
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500 italic">No automated actions recommended.</div>
            )}
          </div>
        </div>
        
      </div>
    </div>
  );
};

const TimelineEvent = ({ time, title, desc, icon: Icon, color }: any) => (
  <div className="flex gap-4 relative pb-4">
    <div className="flex flex-col items-center">
      <div className={`w-8 h-8 rounded-full bg-black border border-white/10 flex items-center justify-center ${color} z-10`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="w-px h-full bg-white/10 absolute top-8 left-4"></div>
    </div>
    <div>
      <div className="text-sm font-bold text-gray-200">{title}</div>
      <div className="text-xs text-gray-400 mt-1">{desc}</div>
      <div className="text-[10px] text-gray-500 mt-1 font-mono">{new Date(time).toLocaleString()}</div>
    </div>
  </div>
);
