import React from 'react';

interface RiskScoreProps {
  risk: any;
}

export const RiskScore = ({ risk }: RiskScoreProps) => {
  if (!risk) {
    return (
      <div className="flex flex-col items-center justify-center py-6 h-full text-gray-500">
        <div className="w-8 h-8 border-2 border-gray-700 border-t-gray-400 rounded-full animate-spin mb-3"></div>
        <p className="text-sm">Calculating Risk Consensus...</p>
      </div>
    );
  }

  const { score, level, reasons } = risk;
  
  const getColor = (lvl: string) => {
    switch (lvl) {
      case 'CRITICAL': return 'text-red-500 border-red-500 bg-red-500/10 shadow-[0_0_30px_rgba(239,68,68,0.2)]';
      case 'HIGH': return 'text-orange-500 border-orange-500 bg-orange-500/10 shadow-[0_0_30px_rgba(249,115,22,0.2)]';
      case 'MEDIUM': return 'text-yellow-500 border-yellow-500 bg-yellow-500/10 shadow-[0_0_30px_rgba(234,179,8,0.2)]';
      default: return 'text-green-500 border-green-500 bg-green-500/10 shadow-[0_0_30px_rgba(34,197,94,0.2)]';
    }
  };

  const getTextColor = (lvl: string) => {
    switch (lvl) {
      case 'CRITICAL': return 'text-red-500';
      case 'HIGH': return 'text-orange-500';
      case 'MEDIUM': return 'text-yellow-500';
      default: return 'text-green-500';
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-6 mb-6">
        <div className={`relative flex items-center justify-center w-28 h-28 rounded-full border-[6px] ${getColor(level)}`}>
          <span className="text-4xl font-black">{score}</span>
          <span className="absolute -bottom-2 bg-background px-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">/ 100</span>
        </div>
        
        <div>
          <div className={`text-2xl font-black uppercase tracking-widest ${getTextColor(level)}`}>
            {level} RISK
          </div>
          <div className="text-xs font-semibold text-gray-400 mt-1 uppercase tracking-wider">Multi-Agent Consensus</div>
          
          <div className="mt-3 text-sm text-gray-300">
            Confidence: <span className="font-bold text-white">High (92%)</span>
          </div>
        </div>
      </div>
      
      <div className="flex-1 bg-black/40 rounded-lg p-4 border border-white/5">
        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-3">Identified Risk Factors</div>
        
        <ul className="space-y-2 max-h-48 overflow-y-auto pr-2">
          {reasons?.map((r: any, idx: number) => (
            <li key={idx} className="flex justify-between items-start text-sm group">
              <span className="text-gray-300 leading-tight group-hover:text-white transition">{r.finding}</span>
              <span className={`font-mono font-bold shrink-0 ml-4 ${r.contribution > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {r.contribution > 0 ? '+' : ''}{r.contribution}
              </span>
            </li>
          ))}
          {(!reasons || reasons.length === 0) && (
            <li className="text-gray-500 text-sm italic">No specific risk indicators mapped yet.</li>
          )}
        </ul>
      </div>
    </div>
  );
};
