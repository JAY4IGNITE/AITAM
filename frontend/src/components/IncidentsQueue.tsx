import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ShieldAlert, AlertTriangle, ChevronRight, Filter } from 'lucide-react';

export const IncidentsQueue = () => {
  const { data: incidents } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => fetch('/api/incidents/').then(res => res.json()),
    refetchInterval: 5000
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-end border-b border-white/10 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">SOC Incidents</h1>
          <p className="text-gray-400">Triage and manage autonomously generated security incidents.</p>
        </div>
        <button className="flex items-center gap-2 bg-black/40 border border-white/10 px-4 py-2 rounded text-sm text-gray-300 hover:text-white transition">
          <Filter className="w-4 h-4" /> Filter
        </button>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {incidents?.map((inc: any) => {
          const severityColor = 
            inc.severity === 'CRITICAL' ? 'text-red-500 bg-red-500/10 border-red-500/20' :
            inc.severity === 'HIGH' ? 'text-orange-500 bg-orange-500/10 border-orange-500/20' :
            inc.severity === 'MEDIUM' ? 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20' :
            'text-blue-500 bg-blue-500/10 border-blue-500/20';

          return (
            <Link 
              key={inc.id} 
              to={`/incidents/${inc.id}`}
              className="glass-panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/5 transition group cursor-pointer"
            >
              <div className="flex items-start gap-4">
                <div className={`mt-1 p-2 rounded-full ${severityColor}`}>
                  {inc.severity === 'CRITICAL' || inc.severity === 'HIGH' ? <ShieldAlert className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-base font-bold text-gray-200 group-hover:text-white transition">{inc.title}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider border ${severityColor}`}>
                      {inc.severity}
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded border border-white/10 text-gray-400 bg-black/40">
                      {inc.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 font-mono flex items-center gap-2">
                    <span>{inc.display_id}</span>
                    <span>|</span>
                    <span>{new Date(inc.created_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center text-gray-500 group-hover:text-primary transition pr-2">
                <span className="text-sm font-semibold mr-2 opacity-0 group-hover:opacity-100 transition-opacity">Review Incident</span>
                <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          );
        })}
        
        {(!incidents || incidents.length === 0) && (
          <div className="flex flex-col items-center justify-center h-64 border border-white/5 border-dashed rounded-lg bg-black/20">
            <ShieldAlert className="w-12 h-12 text-gray-600 mb-4" />
            <h3 className="text-lg font-bold text-gray-400">No Incidents Found</h3>
            <p className="text-sm text-gray-500 mt-2">The SOC queue is currently clear.</p>
          </div>
        )}
      </div>
    </div>
  );
};
