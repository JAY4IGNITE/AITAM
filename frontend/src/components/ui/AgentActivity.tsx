import React from 'react';
import { Shield, Globe, Search, Terminal, AlertTriangle, AlertCircle } from 'lucide-react';

interface AgentActivityProps {
  agents: any[];
}

export const AgentActivity = ({ agents }: AgentActivityProps) => {
  if (!agents || agents.length === 0) {
    return <div className="text-gray-500 text-sm italic p-4">No agents have been scheduled yet.</div>;
  }

  const getIcon = (name: string) => {
    if (name.includes('url')) return Globe;
    if (name.includes('threat')) return Shield;
    if (name.includes('sandbox')) return Terminal;
    if (name.includes('brand')) return Search;
    return Search;
  };

  const getStatusColor = (status: string) => {
    if (status === 'COMPLETED') return 'text-green-400 bg-green-500/10 border-green-500/20';
    if (status === 'FAILED') return 'text-red-400 bg-red-500/10 border-red-500/20';
    return 'text-blue-400 bg-blue-500/10 border-blue-500/20 animate-pulse';
  };

  return (
    <div className="space-y-4">
      {agents.map((agent, idx) => {
        const Icon = getIcon(agent.agent_name);
        
        return (
          <div key={idx} className="bg-black/30 border border-white/5 rounded-lg p-4 transition hover:bg-black/40">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Icon className="w-4 h-4 text-gray-400" />
                <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">
                  {agent.agent_name.replace(/_/g, ' ')}
                </h3>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${getStatusColor(agent.status)}`}>
                {agent.status}
              </span>
            </div>
            
            <div className="pl-6 space-y-2">
              {agent.status === 'RUNNING' && (
                <div className="text-xs text-blue-400 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                  Analyzing artifact...
                </div>
              )}
              
              {agent.status === 'FAILED' && (
                <div className="text-xs text-red-400 flex items-start gap-2 bg-red-500/10 p-2 rounded">
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  {agent.error_message || 'Agent execution failed'}
                </div>
              )}
              
              {agent.status === 'COMPLETED' && (
                <>
                  <p className="text-sm text-gray-300 font-medium">
                    {agent.output_summary}
                  </p>
                  
                  {agent.findings && agent.findings.length > 0 && (
                    <div className="mt-3">
                      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1.5">Key Findings</div>
                      <ul className="space-y-1">
                        {agent.findings.map((f: any, fidx: number) => (
                          <li key={fidx} className="text-xs text-gray-300 flex items-start gap-2 bg-white/5 p-1.5 rounded">
                            <AlertTriangle className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${f.severity === 'high' ? 'text-orange-400' : 'text-yellow-400'}`} />
                            <span className="font-semibold text-gray-200">{f.title}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
