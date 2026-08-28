import React from 'react';
import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';

interface TimelineProps {
  investigation: any;
}

export const InvestigationTimeline = ({ investigation }: TimelineProps) => {
  const status = investigation?.status;
  const stage = investigation?.current_stage;
  
  // A deterministic mapping of stages based on typical SOC flow
  const steps = [
    { id: 'triage', label: 'INPUT RECEIVED & TRIAGE' },
    { id: 'planning', label: 'AGENT PLANNING' },
    { id: 'analysis', label: 'MULTI-AGENT ANALYSIS' },
    { id: 'correlation', label: 'THREAT CORRELATION & RISK SCORING' },
    { id: 'response', label: 'INCIDENT CREATION & RESPONSE' }
  ];

  let currentStepIdx = 0;
  if (status === 'COMPLETED') currentStepIdx = 5;
  else if (stage?.includes('Planning')) currentStepIdx = 1;
  else if (stage?.includes('Agent Analysis')) currentStepIdx = 2;
  else if (stage?.includes('Risk') || stage?.includes('Correlation')) currentStepIdx = 3;
  else if (stage?.includes('Incident') || stage?.includes('Response')) currentStepIdx = 4;
  else if (status === 'FAILED') currentStepIdx = -1;

  return (
    <div className="space-y-6 relative before:absolute before:inset-0 before:ml-2.5 before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-primary/50 before:via-white/10 before:to-transparent">
      {steps.map((step, idx) => {
        let state = 'pending';
        if (status === 'FAILED') {
          state = idx === currentStepIdx ? 'failed' : 'pending';
        } else if (idx < currentStepIdx) {
          state = 'completed';
        } else if (idx === currentStepIdx && status !== 'COMPLETED') {
          state = 'active';
        }

        return (
          <div key={step.id} className="relative flex items-center gap-4">
            <div className={`relative z-10 w-5 h-5 rounded-full flex items-center justify-center bg-background ${
              state === 'completed' ? 'text-green-500' :
              state === 'active' ? 'text-primary animate-pulse' :
              state === 'failed' ? 'text-red-500' :
              'text-gray-600'
            }`}>
              {state === 'completed' ? <CheckCircle2 className="w-5 h-5 bg-background" /> :
               state === 'active' ? <Loader2 className="w-5 h-5 animate-spin bg-background" /> :
               state === 'failed' ? <AlertCircle className="w-5 h-5 bg-background" /> :
               <Circle className="w-4 h-4 bg-background" />}
            </div>
            <div className={`text-sm font-semibold tracking-wider ${
              state === 'completed' ? 'text-gray-300' :
              state === 'active' ? 'text-primary font-bold' :
              state === 'failed' ? 'text-red-500 font-bold' :
              'text-gray-600'
            }`}>
              {step.label}
            </div>
          </div>
        );
      })}
    </div>
  );
};
