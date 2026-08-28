import React from 'react';
import { Network } from 'lucide-react';

interface EvidenceGraphProps {
  graph: any;
}

export const EvidenceGraph = ({ graph }: EvidenceGraphProps) => {
  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 h-full text-gray-500">
        <Network className="w-8 h-8 mb-3 opacity-20" />
        <p className="text-sm">Relational graph will render upon IoC extraction.</p>
      </div>
    );
  }

  // Define colors based on node type
  const getNodeColor = (type: string) => {
    switch (type.toUpperCase()) {
      case 'URL': return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
      case 'DOMAIN': return 'text-purple-400 bg-purple-500/10 border-purple-500/30';
      case 'IP': return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';
      case 'THREAT_INTELLIGENCE': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      case 'BRAND': return 'text-pink-400 bg-pink-500/10 border-pink-500/30';
      case 'BEHAVIOR': return 'text-red-400 bg-red-500/10 border-red-500/30';
      default: return 'text-gray-300 bg-white/5 border-white/10';
    }
  };

  return (
    <div className="h-[400px] w-full overflow-hidden bg-black/20 border border-white/5 rounded-lg flex flex-col font-mono text-sm">
      <div className="p-3 border-b border-white/5 bg-black/40 text-xs font-bold text-gray-500 flex justify-between">
        <span>RELATIONAL GRAPH (SIMPLIFIED)</span>
        <span>{graph.nodes.length} Nodes / {graph.edges.length} Edges</span>
      </div>
      
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {graph.edges.map((e: any, idx: number) => {
          const src = graph.nodes.find((n: any) => n.id === e.source_node_id);
          const tgt = graph.nodes.find((n: any) => n.id === e.target_node_id);
          
          if (!src || !tgt) return null;
          
          return (
            <div key={idx} className="flex items-center gap-3 w-max min-w-full hover:bg-white/5 p-2 rounded transition">
              <div className={`px-2 py-1 rounded border text-xs max-w-xs truncate ${getNodeColor(src.node_type)}`}>
                <span className="font-bold mr-2 opacity-50">[{src.node_type}]</span>
                {src.safe_display_value}
              </div>
              
              <div className="flex-1 flex items-center min-w-[120px] text-gray-500">
                <div className="h-px bg-white/10 w-4"></div>
                <div className="px-2 text-[10px] font-bold uppercase tracking-wider text-center">{e.relationship_type.replace(/_/g, ' ')}</div>
                <div className="h-px bg-white/10 flex-1"></div>
                <div className="w-1.5 h-1.5 rounded-full bg-white/30 shrink-0"></div>
              </div>
              
              <div className={`px-2 py-1 rounded border text-xs max-w-xs truncate ${getNodeColor(tgt.node_type)}`}>
                <span className="font-bold mr-2 opacity-50">[{tgt.node_type}]</span>
                {tgt.safe_display_value}
              </div>
            </div>
          );
        })}
        {graph.edges.length === 0 && (
          <div className="h-full flex items-center justify-center text-gray-500 text-sm">
            No edges mapped between extracted nodes yet.
          </div>
        )}
      </div>
    </div>
  );
};
