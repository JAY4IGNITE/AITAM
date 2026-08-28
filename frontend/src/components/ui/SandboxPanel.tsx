import React from 'react';
import { Terminal, Image as ImageIcon, Code2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

interface SandboxPanelProps {
  investigationId: string;
}

export const SandboxPanel = ({ investigationId }: SandboxPanelProps) => {
  const { data: sandbox } = useQuery({
    queryKey: ['sandbox', investigationId],
    queryFn: () => fetch(`/api/investigations/${investigationId}/sandbox`).then(res => res.json()),
    refetchInterval: (data) => (data?.status === 'COMPLETED' || data?.status === 'FAILED') ? false : 2000
  });

  const { data: events } = useQuery({
    queryKey: ['sandboxEvents', investigationId],
    queryFn: () => fetch(`/api/investigations/${investigationId}/sandbox/events`).then(res => res.json()),
    refetchInterval: 2000,
    enabled: !!sandbox && sandbox.status !== 'NOT_STARTED'
  });

  const { data: artifacts } = useQuery({
    queryKey: ['sandboxArtifacts', investigationId],
    queryFn: () => fetch(`/api/investigations/${investigationId}/sandbox/artifacts`).then(res => res.json()),
    refetchInterval: 5000,
    enabled: !!sandbox && sandbox.status === 'COMPLETED'
  });

  if (!sandbox || sandbox.status === 'NOT_STARTED') {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500 h-full">
        <Terminal className="w-8 h-8 mb-3 opacity-20" />
        <p className="text-sm">Sandbox not triggered for this analysis.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Sandbox Header */}
      <div className="flex gap-6 items-center bg-black/40 p-3 rounded-md border border-white/5">
        <div className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wider ${
          sandbox.status === 'COMPLETED' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 
          sandbox.status === 'FAILED' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 
          'bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse'
        }`}>
          Status: {sandbox.status}
        </div>
        <div className="text-xs font-mono text-gray-400">
          Events Captured: <span className="text-white">{sandbox.event_count || 0}</span>
        </div>
        {sandbox.status === 'COMPLETED' && (
          <div className="text-xs font-mono text-gray-400 ml-auto flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500"></span> Isolated Browser Engine
          </div>
        )}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
        {/* Events Log */}
        <div>
          <h3 className="font-bold text-xs text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <Code2 className="w-4 h-4" /> Telemetry Log
          </h3>
          <div className="bg-black/60 rounded-md p-3 h-64 overflow-y-auto space-y-1.5 border border-white/5 font-mono text-xs">
            {events && events.length > 0 ? events.map((ev: any, idx: number) => (
              <div key={idx} className="flex gap-3 border-b border-white/5 pb-1.5 hover:bg-white/5 transition">
                <span className="text-gray-500 min-w-[70px]">{new Date(ev.timestamp * 1000).toLocaleTimeString()}</span>
                <span className={`font-semibold shrink-0 ${
                  ev.severity === 'CRITICAL' ? 'text-red-400' : 
                  ev.severity === 'HIGH' ? 'text-orange-400' : 
                  ev.severity === 'WARNING' ? 'text-yellow-400' : 'text-blue-400'
                }`}>{ev.event_type}</span>
                <span className="text-gray-400 truncate hover:text-white hover:whitespace-normal transition">{JSON.stringify(ev.metadata)}</span>
              </div>
            )) : (
              <div className="h-full flex items-center justify-center text-gray-600">Waiting for telemetry...</div>
            )}
          </div>
        </div>
        
        {/* Artifacts (Screenshot) */}
        <div>
          <h3 className="font-bold text-xs text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <ImageIcon className="w-4 h-4" /> Artifacts
          </h3>
          {artifacts?.final ? (
            <div className="rounded-md overflow-hidden border border-white/10 relative group bg-black">
              <img src={`data:image/jpeg;base64,${artifacts.final}`} alt="Sandbox Visual DOM render" className="w-full h-64 object-contain opacity-90 group-hover:opacity-100 transition" />
              <div className="absolute bottom-2 right-2 bg-black/80 px-2 py-1 rounded text-[10px] font-bold text-gray-400 uppercase tracking-widest border border-white/10 backdrop-blur">
                Final Viewport Render
              </div>
            </div>
          ) : (
            <div className="h-64 bg-black/40 rounded-md flex flex-col items-center justify-center text-xs text-gray-500 border border-white/5 border-dashed">
              <ImageIcon className="w-6 h-6 mb-2 opacity-50" />
              No screenshot artifact captured
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
