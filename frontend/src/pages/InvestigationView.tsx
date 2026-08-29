import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { 
  AlertTriangle, Download, Activity, MonitorPlay, ShieldAlert,
  GlobeLock, CheckCircle, Clock, ArrowRight, ShieldCheck, HelpCircle,
  FileText, Sparkles, Layers, Eye, X, Shield, Terminal, BookOpen,
  ListOrdered, ExternalLink, ShieldX, Link2
} from 'lucide-react';

import { InvestigationTimeline } from '../components/ui/InvestigationTimeline';
import { AgentActivity } from '../components/ui/AgentActivity';
import { RiskScore } from '../components/ui/RiskScore';
import { AttackJourney } from '../components/ui/AttackJourney';
import { EvidenceGraph } from '../components/ui/EvidenceGraph';
import { SandboxPanel } from '../components/ui/SandboxPanel';

export const InvestigationView = () => {
  const { id } = useParams();
  const [downloading, setDownloading] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  
  const { data: inv } = useQuery({
    queryKey: ['investigation', id],
    queryFn: () => fetch(`/api/investigations/${id}`).then(res => res.json()),
    refetchInterval: (query: any) => {
      const data = query?.state?.data;
      return (data?.status === 'COMPLETED' || data?.status === 'FAILED') ? false : 2000;
    }
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

  const { data: explanation } = useQuery({
    queryKey: ['explanation', id],
    queryFn: () => fetch(`/api/investigations/${id}/explanation`).then(res => res.json()),
    enabled: inv?.status === 'COMPLETED'
  });

  const { data: threatIntel } = useQuery({
    queryKey: ['threatIntel', id],
    queryFn: () => fetch(`/api/investigations/${id}/threat-intelligence`).then(res => res.json()),
    enabled: !!inv
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

  const { data: reportData } = useQuery({
    queryKey: ['report', id],
    queryFn: () => fetch(`/api/investigations/${id}/report`).then(res => res.json()),
    enabled: inv?.status === 'COMPLETED'
  });

  const exportReport = async () => {
    setDownloading(true);
    try {
      const res = await fetch(`/api/investigations/${id}/report`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ThreatLens_Report_${inv?.display_id || id}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (e) {
      alert('Failed to download report');
    } finally {
      setDownloading(false);
    }
  };

  if (!inv) return <div className="p-8 text-gray-500 animate-pulse font-mono">Loading real-time investigation telemetry...</div>;

  const stages = [
    { label: 'Queued', active: true, done: inv.status !== 'QUEUED' },
    { label: 'Triaging', active: ['TRIAGING', 'INITIAL_ANALYSIS', 'AGENT_ANALYSIS', 'COMPLETED'].includes(inv.status), done: ['AGENT_ANALYSIS', 'EVIDENCE_CORRELATION', 'RISK_EVALUATION', 'SANDBOX_RUNNING', 'COMPLETED'].includes(inv.status) },
    { label: 'Analyzing', active: ['AGENT_ANALYSIS', 'EVIDENCE_CORRELATION', 'RISK_EVALUATION', 'COMPLETED'].includes(inv.status), done: ['EVIDENCE_CORRELATION', 'RISK_EVALUATION', 'SANDBOX_RUNNING', 'COMPLETED'].includes(inv.status) },
    { label: 'Threat Intel', active: ['EVIDENCE_CORRELATION', 'RISK_EVALUATION', 'COMPLETED'].includes(inv.status), done: ['RISK_EVALUATION', 'SANDBOX_RUNNING', 'COMPLETED'].includes(inv.status) },
    { label: 'Sandbox', active: ['SANDBOX_QUEUED', 'SANDBOX_RUNNING', 'BEHAVIOR_ANALYSIS', 'COMPLETED'].includes(inv.status), done: ['BEHAVIOR_ANALYSIS', 'COMPLETED'].includes(inv.status) },
    { label: 'Evidence Fusion', active: ['EVIDENCE_CORRELATION', 'RE_EVALUATION', 'COMPLETED'].includes(inv.status), done: ['COMPLETED'].includes(inv.status) },
    { label: 'Risk & Mitigation', active: ['RISK_EVALUATION', 'REPORT_GENERATION', 'COMPLETED'].includes(inv.status), done: inv.status === 'COMPLETED' },
  ];

  return (
    <div className="p-8 max-w-[1600px] mx-auto space-y-6 animate-in fade-in duration-500">
      
      {/* Header Bar */}
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
              <span className="px-3 py-1 text-xs font-bold rounded uppercase tracking-wider bg-orange-500/20 text-orange-400 border border-orange-500/30">
                {autonomous.triage.priority}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="font-mono bg-black/40 px-2 py-0.5 rounded border border-white/5 font-semibold text-primary">{inv.input_type}</span>
            <span className="truncate max-w-xl font-mono text-gray-300">{inv.target}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {autonomous?.response && (
            <Link 
              to="/incidents"
              className={`px-4 py-2 rounded-md font-bold text-xs uppercase tracking-wider flex items-center gap-2 transition ${
                autonomous.response.action === 'BLOCK' ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30' :
                'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500/30'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
              RECOMMENDED: {autonomous.response.action}
            </Link>
          )}

          <button 
            onClick={() => setShowReportModal(true)}
            className="flex items-center gap-2 bg-primary/20 border border-primary/40 text-primary px-4 py-2 rounded-md hover:bg-primary/30 transition disabled:opacity-50 text-sm font-semibold"
            disabled={inv.status !== 'COMPLETED'}
          >
            <Eye className="w-4 h-4" /> View Full Report
          </button>

          <button 
            onClick={exportReport}
            className="flex items-center gap-2 bg-white/5 border border-white/10 text-gray-300 px-4 py-2 rounded-md hover:bg-white/10 transition disabled:opacity-50 text-sm font-semibold"
            disabled={inv.status !== 'COMPLETED' || downloading}
          >
            <Download className="w-4 h-4" /> {downloading ? 'Exporting...' : 'Export JSON'}
          </button>
        </div>
      </div>

      {/* Real-time Stage Progression Stepper */}
      <div className="glass-panel p-4 border border-white/10">
        <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
          <span className="font-semibold text-gray-300">Live Stage: <span className="text-primary font-mono">{inv.current_stage || inv.status}</span></span>
          <span className="font-mono">{inv.status === 'COMPLETED' ? '100% Complete' : 'In Progress...'}</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-7 gap-2 pt-2">
          {stages.map((stage, idx) => (
            <div key={idx} className={`p-2 rounded text-center border text-xs font-semibold flex items-center justify-center gap-1.5 ${
              stage.done ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
              stage.active ? 'bg-primary/20 border-primary/40 text-primary animate-pulse' :
              'bg-black/30 border-white/5 text-gray-600'
            }`}>
              {stage.done ? <CheckCircle className="w-3 h-3 text-emerald-400" /> : <Clock className="w-3 h-3 text-gray-500" />}
              <span>{stage.label}</span>
            </div>
          ))}
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
            <h2 className="text-lg font-bold mb-4 uppercase tracking-wide flex items-center gap-2">
              <Layers className="w-5 h-5 text-gray-400" />
              Agent Activity ({agents?.length || 0})
            </h2>
            <AgentActivity agents={agents} />
          </div>
        </div>

        {/* Middle & Right Column: Risk, Explanation, Threat Intel, Attack Journey, Evidence, Sandbox */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Risk Score Row */}
          <div className="glass-panel p-6">
            <RiskScore risk={risk} />
          </div>

          {/* Explainable AI Explanation Card ("Why is this risky?") */}
          {explanation && (
            <div className="glass-panel p-6 border border-primary/20 bg-primary/5 space-y-4 animate-in fade-in">
              <div className="flex items-center gap-2 text-primary font-bold text-base">
                <Sparkles className="w-5 h-5" />
                <span>EXPLAINABLE FORENSIC SUMMARY: {explanation.title}</span>
              </div>
              
              <p className="text-sm text-gray-300 leading-relaxed font-medium">
                {explanation.summary}
              </p>

              {explanation.risk_factors?.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Primary Risk Factors:</h4>
                  <div className="space-y-2">
                    {explanation.risk_factors.map((rf: any, idx: number) => (
                      <div key={idx} className="bg-black/40 border border-white/5 p-3 rounded-lg flex items-start gap-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 mt-0.5 ${
                          rf.severity === 'critical' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                          rf.severity === 'high' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          +{rf.contribution} pts
                        </span>
                        <div>
                          <div className="text-sm font-semibold text-white">{rf.factor}</div>
                          <div className="text-xs text-gray-400 mt-0.5">{rf.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {explanation.recommendations?.length > 0 && (
                <div className="bg-black/60 border border-white/10 rounded-lg p-4 mt-3">
                  <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4" /> Recommended Analyst / User Actions:
                  </h4>
                  <ul className="space-y-1.5 text-xs text-gray-300">
                    {explanation.recommendations.map((rec: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-amber-400 font-bold">•</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Threat Intelligence Indicator Correlation Card */}
          {threatIntel && threatIntel.length > 0 && (
            <div className="glass-panel p-6 space-y-4">
              <h2 className="text-lg font-bold uppercase tracking-wide flex items-center gap-2">
                <GlobeLock className="w-5 h-5 text-amber-400" />
                Threat Intelligence Correlation ({threatIntel.length} vendor lookups)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {threatIntel.map((ti: any, idx: number) => (
                  <div key={idx} className="bg-black/40 border border-white/5 p-3.5 rounded-lg space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-white">{ti.provider}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                        ti.verdict === 'MALICIOUS' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        ti.verdict === 'SUSPICIOUS' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                        ti.verdict === 'CLEAN' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {ti.verdict}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 font-mono truncate">{ti.indicator}</div>
                    {ti.evidence?.length > 0 && (
                      <div className="text-xs text-gray-300 border-t border-white/5 pt-2 space-y-1">
                        {ti.evidence.map((ev: string, eidx: number) => (
                          <div key={eidx} className="flex items-start gap-1 text-[11px] text-gray-400">
                            <span>•</span> <span>{ev}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
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
              Isolated Browser Detonation
            </h2>
            <SandboxPanel investigationId={id!} />
          </div>
          
        </div>
      </div>

      {/* Comprehensive Forensic Report Modal */}
      {showReportModal && reportData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 overflow-y-auto">
          <div className="glass-panel w-full max-w-5xl p-8 border border-white/20 shadow-2xl relative my-8 max-h-[90vh] overflow-y-auto space-y-6">
            
            {/* Header */}
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-widest font-mono">
                  <Shield className="w-4 h-4" /> ThreatLens Forensic Threat Report
                </div>
                <h2 className="text-2xl font-bold text-white mt-1">{reportData.metadata?.report_id || `REP-${inv.display_id}`}</h2>
                <p className="text-xs text-gray-400 font-mono mt-0.5">Generated: {new Date(reportData.metadata?.generated_at || Date.now()).toLocaleString()}</p>
              </div>
              <button onClick={() => setShowReportModal(false)} className="text-gray-400 hover:text-white p-1">
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Executive Summary */}
            <div className="bg-black/40 border border-white/10 p-5 rounded-lg space-y-3">
              <h3 className="text-sm font-bold text-primary uppercase tracking-wider flex items-center gap-2">
                <BookOpen className="w-4 h-4" /> Executive Summary
              </h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                {reportData.executive_summary?.summary}
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
                <div className="bg-black/60 p-2.5 rounded border border-white/5">
                  <div className="text-[10px] text-gray-400 uppercase font-mono">Risk Classification</div>
                  <div className="text-base font-bold text-white">{reportData.executive_summary?.classification}</div>
                </div>
                <div className="bg-black/60 p-2.5 rounded border border-white/5">
                  <div className="text-[10px] text-gray-400 uppercase font-mono">Calculated Score</div>
                  <div className="text-base font-bold text-primary font-mono">{reportData.executive_summary?.final_risk_score}/100</div>
                </div>
                <div className="bg-black/60 p-2.5 rounded border border-white/5">
                  <div className="text-[10px] text-gray-400 uppercase font-mono">Confidence</div>
                  <div className="text-base font-bold text-white font-mono">{reportData.executive_summary?.confidence_percentage}%</div>
                </div>
                <div className="bg-black/60 p-2.5 rounded border border-white/5">
                  <div className="text-[10px] text-gray-400 uppercase font-mono">Findings Identified</div>
                  <div className="text-base font-bold text-white font-mono">{reportData.executive_summary?.findings_count} items</div>
                </div>
              </div>
            </div>

            {/* URL Security Analysis with Google Safe Browsing Breakdown */}
            {reportData.url_security_analysis?.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Link2 className="w-4 h-4 text-emerald-400" /> URL Security Analysis & Safe Browsing
                </h3>
                <div className="space-y-3">
                  {reportData.url_security_analysis.map((item: any, idx: number) => {
                    const sb = item.safe_browsing;
                    const isThreat = sb?.status === 'THREAT_DETECTED';
                    const isClean = sb?.status === 'NO_KNOWN_THREAT_DETECTED';
                    return (
                      <div key={idx} className="bg-black/40 border border-white/10 p-4 rounded-lg space-y-2">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <span className="font-mono text-xs font-bold text-white truncate max-w-xl">{item.url}</span>
                          <span className={`px-2.5 py-0.5 rounded text-xs font-bold font-mono uppercase inline-flex items-center gap-1.5 w-fit ${
                            isThreat ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                            isClean ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                            'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                          }`}>
                            {isThreat ? <ShieldX className="w-3.5 h-3.5" /> : isClean ? <ShieldCheck className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                            {isThreat ? 'THREAT DETECTED' : isClean ? 'NO KNOWN THREAT' : 'UNABLE TO VERIFY'}
                          </span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs border-t border-white/5 pt-2">
                          <div>
                            <span className="text-[10px] text-gray-500 uppercase font-mono block">Threat Category</span>
                            <span className="text-gray-200 font-semibold">{sb?.threat_types?.join(', ') || 'None Listed'}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-gray-500 uppercase font-mono block">Severity / Source</span>
                            <span className="text-gray-200 font-semibold">{sb?.severity} • {sb?.source}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-gray-500 uppercase font-mono block">Forensic Interpretation</span>
                            <span className="text-gray-400 text-[11px] leading-tight block">{sb?.interpretation}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* MITRE ATT&CK Matrix */}
            {reportData.mitre_attack_matrix?.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" /> MITRE ATT&CK Threat Mapping
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
                  {reportData.mitre_attack_matrix.map((m: any, idx: number) => (
                    <div key={idx} className="bg-black/40 border border-white/10 p-3 rounded-lg space-y-1">
                      <div className="flex justify-between text-purple-300 font-bold">
                        <span>{m.tactic} ({m.tactic_id})</span>
                        <span>{m.technique_id}</span>
                      </div>
                      <div className="text-white text-xs font-sans font-semibold">{m.technique}</div>
                      <div className="text-gray-400 text-[11px] font-sans">{m.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tactical Containment Playbook */}
            {reportData.containment_playbook?.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-amber-400" /> Tactical Containment Playbook
                </h3>
                <div className="space-y-2">
                  {reportData.containment_playbook.map((pb: any, idx: number) => (
                    <div key={idx} className="bg-black/40 border border-white/10 p-3.5 rounded-lg space-y-1.5 font-sans">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white text-xs">{pb.step}</span>
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                          {pb.priority}
                        </span>
                      </div>
                      <p className="text-xs text-gray-300">{pb.action}</p>
                      <div className="bg-black/80 font-mono text-[11px] text-emerald-400 p-2 rounded border border-white/5">
                        $ {pb.command}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted IoCs */}
            {reportData.indicators_of_compromise?.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <GlobeLock className="w-4 h-4 text-primary" /> Indicators of Compromise (IoCs)
                </h3>
                <div className="overflow-x-auto bg-black/40 border border-white/10 rounded-lg">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-white/5 text-gray-400 uppercase text-[10px]">
                      <tr>
                        <th className="px-4 py-2">Type</th>
                        <th className="px-4 py-2">Indicator Value</th>
                        <th className="px-4 py-2">Extracted By</th>
                        <th className="px-4 py-2">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {reportData.indicators_of_compromise.map((ioc: any, idx: number) => (
                        <tr key={idx}>
                          <td className="px-4 py-2 font-bold text-primary">{ioc.type}</td>
                          <td className="px-4 py-2 text-gray-200">{ioc.value}</td>
                          <td className="px-4 py-2 text-gray-400 font-sans">{ioc.source}</td>
                          <td className="px-4 py-2 text-emerald-400">{Math.round((ioc.confidence || 0.95) * 100)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              <button 
                onClick={exportReport}
                className="bg-primary text-primary-foreground font-bold px-5 py-2 rounded text-xs hover:bg-primary/90 flex items-center gap-2"
              >
                <Download className="w-4 h-4" /> Download JSON Artifact
              </button>
              <button 
                onClick={() => setShowReportModal(false)}
                className="bg-white/5 border border-white/10 text-gray-300 font-semibold px-4 py-2 rounded text-xs hover:bg-white/10"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
