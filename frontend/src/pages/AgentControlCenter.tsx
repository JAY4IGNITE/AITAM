import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Activity, Shield, Play, Terminal, Zap, CheckCircle2, 
  AlertTriangle, RefreshCw, Cpu, Layers, GlobeLock, 
  Radio, ArrowRight, Server, Eye,
  Lock, Check, MessageSquare, Database, ExternalLink,
  ShieldCheck, ShieldAlert, MonitorPlay, Clock, Send
} from 'lucide-react';

interface AgentEventPayload {
  investigation_id: string;
  timestamp: string;
  agent_id: string;
  agent_name: string;
  event_type: string;
  status: 'IDLE' | 'QUEUED' | 'RUNNING' | 'WAITING' | 'COMPLETED' | 'FAILED';
  message: string;
  data: Record<string, any>;
}

interface AgentNodeState {
  id: string;
  name: string;
  category: 'core' | 'vector' | 'tool' | 'correlation' | 'verdict';
  status: 'IDLE' | 'QUEUED' | 'RUNNING' | 'WAITING' | 'COMPLETED' | 'FAILED';
  lastMessage: string;
  activeTool?: string;
  duration?: number;
  findingsCount?: number;
  evidenceCount?: number;
  startedAt?: number;
  completedAt?: number;
}

const INITIAL_NODES: Record<string, AgentNodeState> = {
  orchestrator: { id: 'orchestrator', name: 'SOC Orchestrator', category: 'core', status: 'IDLE', lastMessage: 'Awaiting target input artifact...' },
  triage_agent: { id: 'triage_agent', name: 'Triage Agent', category: 'core', status: 'IDLE', lastMessage: 'Standby for priority classification.' },
  investigation_planner: { id: 'investigation_planner', name: 'Investigation Planner', category: 'core', status: 'IDLE', lastMessage: 'Ready to formulate execution route.' },
  
  email_agent: { id: 'email_agent', name: 'Email Intelligence', category: 'vector', status: 'IDLE', lastMessage: 'SPF/DKIM, Header & Spoofing analyzer.' },
  url_intelligence: { id: 'url_intelligence', name: 'URL Intelligence', category: 'vector', status: 'IDLE', lastMessage: 'Decomposition, Punycode & TLD analyzer.' },
  brand_impersonation: { id: 'brand_impersonation', name: 'Brand Spoofing', category: 'vector', status: 'IDLE', lastMessage: 'Visual & lexical brand lookalike checks.' },
  phishing_detection: { id: 'phishing_detection', name: 'Phishing NLP', category: 'vector', status: 'IDLE', lastMessage: 'Lexical urgency & lure classification.' },

  safe_browsing_tool: { id: 'safe_browsing_tool', name: 'Google Safe Browsing v4', category: 'tool', status: 'IDLE', lastMessage: 'Direct Safe Browsing threat match index.' },
  threat_intel_tools: { id: 'threat_intel_tools', name: 'URLhaus & VirusTotal API', category: 'tool', status: 'IDLE', lastMessage: 'Multi-vendor global threat telemetry.' },
  sandbox_agent: { id: 'sandbox_agent', name: 'Playwright Sandbox', category: 'tool', status: 'IDLE', lastMessage: 'Zero-trust browser detonation container.' },

  threat_intelligence: { id: 'threat_intelligence', name: 'Threat Intel Correlation', category: 'correlation', status: 'IDLE', lastMessage: 'Fusing vendor verdicts & reputations.' },
  evidence_fusion: { id: 'evidence_fusion', name: 'Evidence Fusion', category: 'correlation', status: 'IDLE', lastMessage: 'Correlating cross-agent facts & IoCs.' },
  risk_agent: { id: 'risk_agent', name: 'Risk Evaluation', category: 'verdict', status: 'IDLE', lastMessage: '0-100 deterministic scoring engine.' },
  response_agent: { id: 'response_agent', name: 'SOC Response', category: 'verdict', status: 'IDLE', lastMessage: 'Automated containment & approval playbook.' },
  report_agent: { id: 'report_agent', name: 'Forensic Report', category: 'verdict', status: 'IDLE', lastMessage: 'Synthesizing incident threat dossier.' },
};

export const AgentControlCenter: React.FC = () => {
  const { id: paramId } = useParams();
  const navigate = useNavigate();

  const [selectedInvId, setSelectedInvId] = useState<string>(paramId || '');
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [events, setEvents] = useState<AgentEventPayload[]>([]);
  const [nodes, setNodes] = useState<Record<string, AgentNodeState>>(INITIAL_NODES);
  const [activeComm, setActiveComm] = useState<{ sender: string; recipient: string; message: string } | null>(null);
  const [liveRiskScore, setLiveRiskScore] = useState<number | null>(null);
  const [liveRiskLevel, setLiveRiskLevel] = useState<string | null>(null);
  const [filterAgent, setFilterAgent] = useState<string>('all');
  const [customTarget, setCustomTarget] = useState<string>('https://suspicious-bank-login.top/auth/verify');
  const [submitting, setSubmitting] = useState<boolean>(false);

  const terminalEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sseRef = useRef<EventSource | null>(null);

  const { data: recentInvs, refetch: refetchInvs } = useQuery({
    queryKey: ['recent-investigations-list'],
    queryFn: () => fetch('/api/investigations/?limit=10').then(r => r.json()),
    refetchInterval: 5000
  });

  useEffect(() => {
    if (!selectedInvId && recentInvs?.items?.length > 0) {
      setSelectedInvId(recentInvs.items[0].id);
    }
  }, [recentInvs, selectedInvId]);

  useEffect(() => {
    if (!selectedInvId) return;

    setNodes(INITIAL_NODES);
    setEvents([]);
    setLiveRiskScore(null);
    setLiveRiskLevel(null);

    fetch(`/api/investigations/${selectedInvId}/events`)
      .then(r => r.json())
      .then((history: AgentEventPayload[]) => {
        if (Array.isArray(history) && history.length > 0) {
          setEvents(history);
          history.forEach(ev => applyEventToNodes(ev));
        }
      })
      .catch(err => console.debug("Events history fetch:", err));

    connectRealtimeStream(selectedInvId);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (sseRef.current) sseRef.current.close();
    };
  }, [selectedInvId]);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const applyEventToNodes = (ev: AgentEventPayload) => {
    const agentKey = ev.agent_id.toLowerCase().replace("-", "_");

    setNodes(prev => {
      const next = { ...prev };
      const targetNode = next[agentKey] || next[ev.agent_name.toLowerCase().replace(/\s+/g, '_')];

      if (targetNode) {
        targetNode.lastMessage = ev.message;
        if (ev.status) targetNode.status = ev.status;
        if (ev.event_type === 'agent_started') {
          targetNode.status = 'RUNNING';
          targetNode.startedAt = Date.now();
        } else if (ev.event_type === 'agent_completed') {
          targetNode.status = 'COMPLETED';
          targetNode.completedAt = Date.now();
          if (ev.data?.duration_seconds) targetNode.duration = ev.data.duration_seconds;
          if (ev.data?.findings_count !== undefined) targetNode.findingsCount = ev.data.findings_count;
        } else if (ev.event_type === 'agent_failed') {
          targetNode.status = 'FAILED';
        } else if (ev.event_type === 'tool_started') {
          targetNode.activeTool = ev.data?.tool || 'External API';
        } else if (ev.event_type === 'tool_completed') {
          targetNode.activeTool = undefined;
        }
      }

      if (ev.agent_id === 'safe_browsing_tool' && next.safe_browsing_tool) {
        next.safe_browsing_tool.status = ev.event_type === 'tool_started' ? 'RUNNING' : 'COMPLETED';
        next.safe_browsing_tool.lastMessage = ev.message;
      }

      return next;
    });

    if (ev.event_type === 'agent_message' && ev.data?.sender && ev.data?.recipient) {
      const recipients = Array.isArray(ev.data.recipient) ? ev.data.recipient : [ev.data.recipient];
      recipients.forEach((rcp: string) => {
        setActiveComm({
          sender: ev.data.sender,
          recipient: rcp,
          message: ev.message
        });
        setTimeout(() => setActiveComm(null), 2500);
      });
    }

    if (ev.event_type === 'risk_updated' && ev.data?.score !== undefined) {
      setLiveRiskScore(ev.data.score);
      setLiveRiskLevel(ev.data.level);
    }
  };

  const connectRealtimeStream = (invId: string) => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/investigations/${invId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send("ping");
        }, 15000);
        ws.onclose = () => {
          clearInterval(pingInterval);
          setWsConnected(false);
        };
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'pong') return;
          setEvents(prev => [...prev, data]);
          applyEventToNodes(data);
        } catch (e) {
          console.debug("WS parse error:", e);
        }
      };

      ws.onerror = () => connectSSEFallback(invId);
      wsRef.current = ws;
    } catch (err) {
      connectSSEFallback(invId);
    }
  };

  const connectSSEFallback = (invId: string) => {
    try {
      const sse = new EventSource(`/api/investigations/${invId}/events/stream`);
      sse.onopen = () => setWsConnected(true);
      sse.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setEvents(prev => [...prev, data]);
          applyEventToNodes(data);
        } catch (e) {
          console.debug("SSE parse error:", e);
        }
      };
      sse.onerror = () => setWsConnected(false);
      sseRef.current = sse;
    } catch (e) {
      console.debug("SSE error:", e);
    }
  };

  const launchNewInvestigation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customTarget.trim()) return;
    setSubmitting(true);

    try {
      const res = await fetch('/api/investigations/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_type: 'URL',
          target: customTarget.trim()
        })
      });
      const data = await res.json();
      if (data.investigation_id) {
        setSelectedInvId(data.investigation_id);
        navigate(`/agent-control/${data.investigation_id}`);
        refetchInvs();
      }
    } catch (err) {
      alert('Failed to launch investigation');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: AgentNodeState['status']) => {
    switch (status) {
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-zinc-800 text-white border border-zinc-700">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            ACTIVE
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-zinc-900 text-zinc-300 border border-zinc-800">
            <Check className="w-3 h-3 text-zinc-400" />
            DONE
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-zinc-900 text-zinc-400 border border-zinc-800">
            <AlertTriangle className="w-3 h-3 text-zinc-500" />
            FAILED
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-zinc-900 text-zinc-400 border border-zinc-800">
            <Clock className="w-3 h-3" />
            QUEUED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono text-zinc-500 bg-zinc-900/50 border border-zinc-800/60">
            ○ IDLE
          </span>
        );
    }
  };

  const filteredEvents = filterAgent === 'all' 
    ? events 
    : events.filter(e => e.agent_id.toLowerCase().includes(filterAgent.toLowerCase()) || e.agent_name.toLowerCase().includes(filterAgent.toLowerCase()));

  const activeAgentsCount = Object.values(nodes).filter(n => n.status === 'RUNNING').length;
  const completedAgentsCount = Object.values(nodes).filter(n => n.status === 'COMPLETED').length;

  return (
    <div className="p-8 max-w-[1600px] mx-auto space-y-6 animate-in fade-in duration-300">
      
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white">Agent Control Center</h1>
            <span className="bg-zinc-800 text-zinc-300 border border-zinc-700 text-[10px] px-2 py-0.5 rounded font-mono font-medium">
              Multi-Agent Swarm
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Real-time visual telemetry, parallel execution graphs, and inter-agent communication streams.
          </p>
        </div>

        {/* Telemetry Status Strip */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-md flex items-center gap-2 text-xs font-mono">
            <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-emerald-400' : 'bg-zinc-500'}`}></span>
            <span className="text-zinc-400">Stream:</span>
            <span className="text-zinc-200 font-semibold">{wsConnected ? 'Connected' : 'Reconnecting'}</span>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-md flex items-center gap-2 text-xs font-mono">
            <span className="text-zinc-400">Active:</span>
            <span className="text-white font-bold">{activeAgentsCount}</span>
            <span className="text-zinc-600">/</span>
            <span className="text-zinc-400">Done:</span>
            <span className="text-zinc-200 font-bold">{completedAgentsCount}</span>
          </div>

          {liveRiskScore !== null && (
            <div className="bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-md flex items-center gap-2 text-xs font-mono font-semibold text-white">
              <span>Risk: {liveRiskScore}/100</span>
            </div>
          )}

          {selectedInvId && (
            <Link
              to={`/investigations/${selectedInvId}`}
              className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition"
            >
              <Eye className="w-3.5 h-3.5 text-zinc-400" />
              <span>Case Dossier</span>
            </Link>
          )}
        </div>
      </div>

      {/* Target Launch & Investigation Switcher */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        {/* Quick Launch Form */}
        <form onSubmit={launchNewInvestigation} className="lg:col-span-8 glass-panel p-2.5 flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-400 whitespace-nowrap pl-2">Target:</span>
          <input
            type="text"
            value={customTarget}
            onChange={(e) => setCustomTarget(e.target.value)}
            placeholder="Enter URL, email, or artifact to investigate..."
            className="flex-1 bg-zinc-900 border border-zinc-800 rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-zinc-600 transition"
          />
          <button
            type="submit"
            disabled={submitting}
            className="bg-white hover:bg-zinc-200 text-zinc-950 font-semibold text-xs px-4 py-1.5 rounded transition disabled:opacity-40 flex items-center gap-1.5"
          >
            {submitting ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3 fill-current" />}
            <span>Run Swarm</span>
          </button>
        </form>

        {/* Case Switcher Dropdown */}
        <div className="lg:col-span-4 glass-panel p-2.5 flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-400 whitespace-nowrap pl-1">Case:</span>
          <select
            value={selectedInvId}
            onChange={(e) => {
              setSelectedInvId(e.target.value);
              navigate(`/agent-control/${e.target.value}`);
            }}
            className="flex-1 bg-zinc-900 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-zinc-600 transition"
          >
            {recentInvs?.items?.map((inv: any) => (
              <option key={inv.id} value={inv.id}>
                {inv.display_id} — {inv.input_type} ({inv.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Inter-Agent Communication Banner */}
      {activeComm && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-md p-3 flex items-center justify-between text-xs font-mono animate-in fade-in">
          <div className="flex items-center gap-2 text-zinc-300">
            <span className="text-zinc-500">MESSAGE:</span>
            <span className="text-white font-semibold bg-zinc-800 px-2 py-0.5 rounded">{activeComm.sender}</span>
            <ArrowRight className="w-3 h-3 text-zinc-500" />
            <span className="text-white font-semibold bg-zinc-800 px-2 py-0.5 rounded">{activeComm.recipient}</span>
          </div>
          <span className="text-zinc-400 truncate max-w-lg">{activeComm.message}</span>
        </div>
      )}

      {/* Main Grid: Visual Graph (8 Cols) + Live Terminal (4 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left 8 Cols: Live Agent Graph */}
        <div className="lg:col-span-8 space-y-4">
          <div className="glass-panel p-5 space-y-5">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <Layers className="w-4 h-4 text-zinc-400" />
                <span>Multi-Agent Swarm Topology</span>
              </div>
              <div className="flex items-center gap-3 text-[11px] font-mono text-zinc-500">
                <span>● Active</span>
                <span>✓ Done</span>
                <span>○ Idle</span>
              </div>
            </div>

            {/* STAGE 1: Triage & Planner */}
            <div className="space-y-2">
              <div className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider font-mono">
                Phase 1: Ingestion & Strategic Planning
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[nodes.orchestrator, nodes.triage_agent, nodes.investigation_planner].map((node) => (
                  <div 
                    key={node.id}
                    className={`p-3 rounded-md border transition ${
                      node.status === 'RUNNING' ? 'bg-zinc-900 border-zinc-600' :
                      node.status === 'COMPLETED' ? 'bg-zinc-900/40 border-zinc-800' :
                      'bg-zinc-950 border-zinc-800/60 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-white">{node.name}</span>
                      {getStatusBadge(node.status)}
                    </div>
                    <p className="text-[11px] text-zinc-400 line-clamp-2 mb-2 font-sans">
                      {node.lastMessage}
                    </p>
                    {node.duration && (
                      <div className="text-[10px] font-mono text-zinc-500 border-t border-zinc-800 pt-1 flex justify-between">
                        <span>Time:</span>
                        <span className="text-zinc-300 font-semibold">{node.duration}s</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* STAGE 2: Specialized Parallel Vector Agents */}
            <div className="space-y-2">
              <div className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider font-mono">
                Phase 2: Parallel Vector Analysis
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {[nodes.url_intelligence, nodes.email_agent, nodes.brand_impersonation, nodes.phishing_detection].map((node) => (
                  <div 
                    key={node.id}
                    className={`p-3 rounded-md border transition ${
                      node.status === 'RUNNING' ? 'bg-zinc-900 border-zinc-600' :
                      node.status === 'COMPLETED' ? 'bg-zinc-900/40 border-zinc-800' :
                      'bg-zinc-950 border-zinc-800/60 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-white truncate max-w-[110px]">{node.name}</span>
                      {getStatusBadge(node.status)}
                    </div>
                    <p className="text-[11px] text-zinc-400 line-clamp-2 mb-1.5 font-sans">
                      {node.lastMessage}
                    </p>
                    {node.findingsCount !== undefined && (
                      <div className="text-[10px] font-mono text-zinc-500 border-t border-zinc-800 pt-1 flex justify-between">
                        <span>Findings:</span>
                        <span className="text-white font-bold">{node.findingsCount}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* STAGE 3: External Tools & API Invocations */}
            <div className="space-y-2">
              <div className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider font-mono">
                Security Tools & Detonation API Tier
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[nodes.safe_browsing_tool, nodes.threat_intel_tools, nodes.sandbox_agent].map((node) => (
                  <div 
                    key={node.id}
                    className={`p-3 rounded-md border transition ${
                      node.status === 'RUNNING' ? 'bg-zinc-900 border-zinc-600' :
                      node.status === 'COMPLETED' ? 'bg-zinc-900/40 border-zinc-800' :
                      'bg-zinc-950 border-zinc-800/60 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-white">{node.name}</span>
                      {getStatusBadge(node.status)}
                    </div>
                    <p className="text-[11px] text-zinc-400 leading-tight font-sans mb-1">
                      {node.lastMessage}
                    </p>
                    {node.activeTool && (
                      <div className="inline-flex items-center gap-1 bg-zinc-800 text-zinc-200 px-2 py-0.5 rounded text-[10px] font-mono">
                        Tool: {node.activeTool}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* STAGE 4: Fusion & Risk Verdict */}
            <div className="space-y-2">
              <div className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider font-mono">
                Phase 3: Correlation, Risk & Response
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {[nodes.evidence_fusion, nodes.threat_intelligence, nodes.risk_agent, nodes.response_agent].map((node) => (
                  <div 
                    key={node.id}
                    className={`p-3 rounded-md border transition ${
                      node.status === 'RUNNING' ? 'bg-zinc-900 border-zinc-600' :
                      node.status === 'COMPLETED' ? 'bg-zinc-900/40 border-zinc-800' :
                      'bg-zinc-950 border-zinc-800/60 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-white truncate max-w-[100px]">{node.name}</span>
                      {getStatusBadge(node.status)}
                    </div>
                    <p className="text-[11px] text-zinc-400 line-clamp-2 font-sans mb-1">
                      {node.lastMessage}
                    </p>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>

        {/* Right 4 Cols: Clean Telemetry Terminal */}
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-panel p-4 space-y-3 flex flex-col h-[650px]">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">
                <Terminal className="w-3.5 h-3.5 text-zinc-400" />
                <span>Execution Feed ({events.length})</span>
              </div>
              
              <select
                value={filterAgent}
                onChange={(e) => setFilterAgent(e.target.value)}
                className="bg-zinc-900 border border-zinc-800 rounded px-2 py-0.5 text-[10px] text-zinc-300 font-mono focus:outline-none"
              >
                <option value="all">All Agents</option>
                <option value="orchestrator">Orchestrator</option>
                <option value="url">URL Agent</option>
                <option value="safe_browsing">Safe Browsing</option>
                <option value="risk">Risk Agent</option>
              </select>
            </div>

            {/* Scrolling Feed */}
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 font-mono text-xs">
              {filteredEvents.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-zinc-500 text-center p-4">
                  <Cpu className="w-6 h-6 mb-2 opacity-40" />
                  <span>Waiting for execution events...</span>
                </div>
              ) : (
                filteredEvents.map((ev, idx) => (
                  <div 
                    key={idx}
                    className="p-2 rounded bg-zinc-900/60 border border-zinc-800/80 text-[11px] text-zinc-300"
                  >
                    <div className="flex items-center justify-between text-[10px] text-zinc-500 mb-0.5">
                      <span className="font-semibold text-zinc-300">
                        {ev.agent_name || ev.agent_id}
                      </span>
                      <span>{new Date(ev.timestamp || Date.now()).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-zinc-300 font-sans text-xs">{ev.message}</div>
                  </div>
                ))
              )}
              <div ref={terminalEndRef} />
            </div>

            <div className="border-t border-zinc-800 pt-2 flex items-center justify-between text-[10px] font-mono text-zinc-500">
              <span>Case: {selectedInvId ? selectedInvId.slice(0, 8) : 'None'}</span>
              <button 
                onClick={() => setEvents([])}
                className="hover:text-white transition text-zinc-400"
              >
                Clear
              </button>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
};
