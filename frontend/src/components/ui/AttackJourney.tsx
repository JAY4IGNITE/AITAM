import React from 'react';
import { ArrowDown, AlertTriangle, Info, MapPin } from 'lucide-react';

interface AttackJourneyProps {
  journey: any[];
}

export const AttackJourney = ({ journey }: AttackJourneyProps) => {
  if (!journey || journey.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500 h-full">
        <MapPin className="w-8 h-8 mb-3 opacity-20" />
        <p className="text-sm">Attack journey visualization will generate upon investigation completion.</p>
      </div>
    );
  }

  return (
    <div className="space-y-0 relative py-4">
      {journey.map((step, idx) => (
        <div key={idx} className="relative flex group">
          
          {/* Vertical Line Container */}
          <div className="flex flex-col items-center mr-6">
            <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold text-xs shrink-0 z-10 transition ${
              step.risk_after > step.risk_before 
                ? 'border-red-500 bg-red-500/10 text-red-400 group-hover:bg-red-500 group-hover:text-white' 
                : 'border-blue-500 bg-blue-500/10 text-blue-400 group-hover:bg-blue-500 group-hover:text-white'
            }`}>
              {step.sequence}
            </div>
            {idx < journey.length - 1 && (
              <div className="w-0.5 h-full bg-white/10 my-1 min-h-[40px] group-hover:bg-white/20 transition"></div>
            )}
          </div>
          
          {/* Content Box */}
          <div className="flex-1 pb-6">
            <div className="bg-black/30 border border-white/5 rounded-lg p-4 group-hover:border-white/10 group-hover:bg-black/50 transition">
              <div className="flex justify-between items-start mb-1">
                <h3 className="font-bold text-sm text-gray-200">{step.title}</h3>
                <span className="text-[10px] text-gray-500 font-mono tracking-tighter">
                  +{(step.timestamp || 0).toFixed(2)}s
                </span>
              </div>
              
              <p className="text-xs text-gray-400 mb-3 leading-relaxed">{step.description}</p>
              
              <div className="flex items-center gap-4">
                {step.risk_after > step.risk_before ? (
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-red-400 bg-red-500/10 px-2 py-1 rounded border border-red-500/20 uppercase tracking-wider">
                    <ArrowDown className="w-3 h-3 rotate-180" />
                    Risk Increased ({step.risk_before} → {step.risk_after})
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-blue-400 bg-blue-500/10 px-2 py-1 rounded border border-blue-500/20 uppercase tracking-wider">
                    <Info className="w-3 h-3" />
                    No Risk Change
                  </div>
                )}
                
                {step.confidence && (
                  <div className="text-[10px] text-gray-500">
                    Confidence: <span className="font-bold text-gray-300">{Math.round(step.confidence * 100)}%</span>
                  </div>
                )}
              </div>
            </div>
          </div>
          
        </div>
      ))}
    </div>
  );
};
