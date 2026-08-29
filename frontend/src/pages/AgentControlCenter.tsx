import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Activity, Shield, Play, Terminal, Zap, CheckCircle2, 
  AlertTriangle, RefreshCw, Cpu, Layers, GlobeLock, 
  Sparkles, Radio, ArrowRight, Server, Flame, Eye,
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
  triage_agent: { id: 'triage_agent', name: 'Autonomous Triage Agent', category: 'core', status: 'IDLE', lastMessage: 'Standby for priority classification.' },
  investigation_planner: { id: 'investigation_planner', name: 'Investigation Planner', category: 'core', status: 'IDLE', lastMessage: 'Ready to formulate execution route.' },
  
  email_agent: { id: 'email_agent', name: 'Email Intelligence Agent', category: 'vector', status: 'IDLE', lastMessage: 'SPF/DKIM, Header & Spoofing analyzer.' },
  url_intelligence: { id: 'url_intelligence', name: 'URL Intelligence Agent', category: 'vector', status: 'IDLE', lastMessage: 'Decomposition, Punycode & TLD analyzer.' },
  brand_impersonation: { id: 'brand_impersonation', name: 'Brand Spoofing Agent', category: 'vector', status: 'IDLE', lastMessage: 'Visual & lexical brand lookalike checks.' },
  phishing_detection: { id: 'phishing_detection', name: 'Phishing NLP Agent', category: 'vector', status: 'IDLE', lastMessage: 'Lexical urgency & lure classification.' },

  safe_browsing_tool: { id: 'safe_browsing_tool', name: 'Google Safe Browsing API v4', category: 'tool', status: 'IDLE', lastMessage: 'Direct Safe Browsing threat match index.' },
  threat_intel_tools: { id: 'threat_intel_tools', name: 'URLhaus & VirusTotal API', category: 'tool', status: 'IDLE', lastMessage: 'Multi-vendor global threat telemetry.' },
  sandbox_agent: { id: 'sandbox_agent', name: 'Playwright Sandbox Agent', category: 'tool', status: 'IDLE', lastMessage: 'Zero-trust browser detonation container.' },

  threat_intelligence: { id: 'threat_intelligence', name: 'Threat Intel Correlation', category: 'correlation', status: 'IDLE', lastMessage: 'Fusing vendor verdicts & reputations.' },
  evidence_fusion: { id: 'evidence_fusion', name: 'Evidence Fusion Agent', category: 'correlation', status: 'IDLE', lastMessage: 'Correlating cross-agent facts & IoCs.' },
  risk_agent: { id: 'risk_agent', name: 'Risk Evaluation Agent', category: 'verdict', status: 'IDLE', lastMessage: '0-100 deterministic scoring engine.' },
  response_agent: { id: 'response_agent', name: 'SOC Response Agent', category: 'verdict', status: 'IDLE', lastMessage: 'Automated containment & approval playbook.' },
  report_agent: { id: 'report_agent', name: 'Forensic Report Agent', category: 'verdict', status: 'IDLE', lastMessage: 'Synthesizing incident threat dossier.' },
};

export const AgentControlCenter: React.FC = () => {
  const { id: paramId } = useParams();
  const navigate = useNavigate();

  // Selected investigation ID
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

  // Fetch recent investigations for quick switcher
  const { data: recentInvs, refetch: refetchInvs } = useQuery({
    queryKey: ['recent-investigations-list'],
    queryFn: () => fetch('/api/investigations/?limit=10').then(r => r.json()),
    refetchInterval: 5000
  });

  // Default to the newest investigation if none in URL
  useEffect(() => {
    if (!selectedInvId && recentInvs?.items?.length > 0) {
      setSelectedInvId(recentInvs.items[0].id);
    }
  }, [recentInvs, selectedInvId]);

  // Load historical events from database on selection/refresh
  useEffect(() => {
    if (!selectedInvId) return;

    // Reset nodes state
    setNodes(INITIAL_NODES);
    setEvents([]);
    setLiveRiskScore(null);
    setLiveRiskLevel(null);

    // Fetch existing stored events from PostgreSQL
    fetch(`/api/investigations/${selectedInvId}/events`)
      .then(r => r.json())
      .then((history: AgentEventPayload[]) => {
        if (Array.isArray(history) && history.length > 0) {
          setEvents(history);
          // Replay events into nodes state
          history.forEach(ev => applyEventToNodes(ev));
        }
      })
      .catch(err => console.debug("Events history fetch:", err));

    // Connect real-time WebSocket with fallback to SSE
    connectRealtimeStream(selectedInvId);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (sseRef.current) sseRef.current.close();
    };
  }, [selectedInvId]);

  // Auto-scroll terminal feed
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

      // Also handle specialized tool nodes
      if (ev.agent_id === 'safe_browsing_tool' && next.safe_browsing_tool) {
        next.safe_browsing_tool.status = ev.event_type === 'tool_started' ? 'RUNNING' : 'COMPLETED';
        next.safe_browsing_tool.lastMessage = ev.message;
      }

      return next;
    });

    // Handle inter-agent communication pulses
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

    // Handle progressive risk updates
    if (ev.event_type === 'risk_updated' && ev.data?.score !== undefined) {
      setLiveRiskScore(ev.data.score);
      setLiveRiskLevel(ev.data.level);
    }
  };

  const connectRealtimeStream = (invId: string) => {
    // 1. Try WebSocket
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/investigations/${invId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
        // Start ping heartbeat
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

      ws.onerror = () => {
        // Fallback to Server-Sent Events (SSE)
        connectSSEFallback(invId);
      };

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
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
            RUNNING
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase bg-green-500/10 text-green-400 border border-green-500/30">
            <Check className="w-3 h-3 text-green-400" />
            DONE
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase bg-red-500/20 text-red-400 border border-red-500/30">
            <AlertTriangle className="w-3 h-3 text-red-400" />
            FAILED
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <Clock className="w-3 h-3" />
            QUEUED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono text-gray-500 bg-white/5 border border-white/5">
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
    <div className="p-6 max-w-[1700px] mx-auto space-y-6 animate-in fade-in duration-500">
      
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20 text-primary">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Multi-Agent Investigation Control Center
                <span className="text-xs px-2.5 py-0.5 rounded bg-primary/20 text-primary border border-primary/30 font-mono font-bold">
                  SOC v2.0
                </span>
              </h1>
              <p className="text-xs text-gray-400 font-mono mt-0.5">
                Real-time visual telemetry, parallel execution graphs, and inter-agent communication streaming.
              </p>
            </div>
          </div>
        </div>

        {/* Live Telemetry Pills */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="bg-black/50 border border-white/10 px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
            <span className="text-gray-400">Stream:</span>
            <span className={wsConnected ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
              {wsConnected ? 'LIVE WEBSOCKET' : 'RECONNECTING'}
            </span>
          </div>

          <div className="bg-black/50 border border-white/10 px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs font-mono">
            <Radio className="w-3.5 h-3.5 text-primary animate-pulse" />
            <span className="text-gray-400">Running:</span>
            <span className="text-white font-bold">{activeAgentsCount}</span>
            <span className="text-gray-500">|</span>
            <span className="text-gray-400">Done:</span>
            <span className="text-emerald-400 font-bold">{completedAgentsCount}</span>
          </div>

          {liveRiskScore !== null && (
            <div className={`px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs font-mono font-bold border ${
              liveRiskScore >= 80 ? 'bg-red-500/20 text-red-400 border-red-500/40' :
              liveRiskScore >= 60 ? 'bg-orange-500/20 text-orange-400 border-orange-500/40' :
              liveRiskScore >= 40 ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' :
              'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
            }`}>
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>LIVE RISK: {liveRiskScore}/100 ({liveRiskLevel})</span>
            </div>
          )}

          {selectedInvId && (
            <Link
              to={`/investigations/${selectedInvId}`}
              className="bg-white/5 border border-white/10 hover:bg-white/10 text-gray-300 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <Eye className="w-3.5 h-3.5" /> View Case Report
            </Link>
          )}
        </div>
      </div>

      {/* Target Launch & Investigation Switcher */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Quick Launch Form */}
        <form onSubmit={launchNewInvestigation} className="lg:col-span-8 glass-panel p-3.5 flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400 whitespace-nowrap pl-2 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-primary" /> Target:
          </span>
          <input
            type="text"
            value={customTarget}
            onChange={(e) => setCustomTarget(e.target.value)}
            placeholder="Enter suspicious URL or target..."
            className="flex-1 bg-black/60 border border-white/10 rounded px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-primary"
          />
          <button
            type="submit"
            disabled={submitting}
            className="bg-primary text-primary-foreground font-bold text-xs px-4 py-1.5 rounded hover:bg-primary/90 flex items-center gap-1.5 transition disabled:opacity-50"
          >
            {submitting ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
            <span>Detonate Multi-Agent Swarm</span>
          </button>
        </form>

        {/* Case Switcher Dropdown */}
        <div className="lg:col-span-4 glass-panel p-3.5 flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400 whitespace-nowrap pl-1">Active Case:</span>
          <select
            value={selectedInvId}
            onChange={(e) => {
              setSelectedInvId(e.target.value);
              navigate(`/agent-control/${e.target.value}`);
            }}
            className="flex-1 bg-black/60 border border-white/10 rounded px-2.5 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-primary"
          >
            {recentInvs?.items?.map((inv: any) => (
              <option key={inv.id} value={inv.id}>
                {inv.display_id} — {inv.input_type} ({inv.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Inter-Agent Communication Notification Strip */}
      {activeComm && (
        <div className="bg-primary/15 border border-primary/40 rounded-lg p-3 flex items-center justify-between animate-in fade-in slide-in-from-top-2 text-xs font-mono">
          <div className="flex items-center gap-2 text-primary font-bold">
            <MessageSquare className="w-4 h-4 animate-bounce" />
            <span>INTER-AGENT MESSAGE:</span>
            <span className="text-white bg-black/60 px-2 py-0.5 rounded border border-white/10">{activeComm.sender}</span>
            <ArrowRight className="w-3 h-3 text-gray-400" />
            <span className="text-white bg-black/60 px-2 py-0.5 rounded border border-white/10">{activeComm.recipient}</span>
          </div>
          <span className="text-gray-300 truncate max-w-xl">{activeComm.message}</span>
        </div>
      )}

      {/* Main Grid: Visual Graph (Left 8 Cols) + Live Terminal & Communications (Right 4 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left 8 Cols: Real Live Agent Topology Graph */}
        <div className="lg:col-span-8 space-y-6">
          <div className="glass-panel p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div className="flex items-center gap-2 text-white font-bold text-base">
                <Layers className="w-5 h-5 text-primary" />
                <span>Live Multi-Agent Orchestration Swarm</span>
              </div>
              <div className="flex items-center gap-3 text-[11px] font-mono text-gray-400">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400"></span> Active</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span> Complete</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-600"></span> Idle</span>
              </div>
            </div>

            {/* STAGE 1: Orchestrator & Triage Planner Tier */}
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase font-mono tracking-widest mb-3">
                Phase 1: Ingestion & Strategic Planning Tier
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[nodes.orchestrator, nodes.triage_agent, nodes.investigation_planner].map((node) => (
                  <div 
                    key={node.id}
                    className={`p-3.5 rounded-lg border transition-all duration-300 relative ${
                      node.status === 'RUNNING' ? 'bg-primary/10 border-primary shadow-lg shadow-primary/10 ring-1 ring-primary/40' :
                      node.status === 'COMPLETED' ? 'bg-black/40 border-green-500/30' :
                      'bg-black/20 border-white/5 opacity-70'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-bold text-xs text-white flex items-center gap-1.5">
                        <Cpu className="w-3.5 h-3.5 text-primary" />
                        {node.name}
                      </span>
                      {getStatusBadge(node.status)}
                    </div>
                    <p className="text-[11px] text-gray-300 leading-tight line-clamp-2 font-sans mb-2">
                      {node.lastMessage}
                    </p>
                    {node.duration && (
                      <div className="text-[10px] font-mono text-gray-400 border-t border-white/5 pt-1.5 flex justify-between">
                        <span>Duration:</span>
                        <span className="text-emerald-400 font-bold">{node.duration}s</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* STAGE 2: Specialized Parallel Vector Agents */}
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase font-mono tracking-widest mb-3 flex items-center justify-between">
                <span>Phase 2: Parallel Specialized Intelligence Agents</span>
                <span className="text-primary text-[10px]">Concurrent Dispatch</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {[nodes.url_intelligence, nodes.email_agent, nodes.brand_impersonation, nodes.phishing_detection].map((node) => (
                  <div 
                    key={node.id}
                    className={`p-3 rounded-lg border transition-all duration-300 ${
                      node.status === 'RUNNING' ? 'bg-emerald-500/10 border-emerald-500 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500/40' :
                      node.status === 'COMPLETED' ? 'bg-black/40 border-green-500/30' :
                      'bg-black/20 border-white/5 opacity-70'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-white truncate max-w-[120px]">{node.name}</span>
                      {getStatusBadge(node.status)}
                    </div>
                    <p className="text-[11px] text-gray-300 leading-tight line-clamp-2 font-sans mb-2">
                      {node.lastMessage}
                    </p>
                    {node.findingsCount !== undefined && (
                      <div className="text-[10px] font-mono text-gray-400 border-t border-white/5 pt-1 flex justify-between">
                        <span>Findings:</span>
                        <span className="text-primary font-bold">{node.findingsCount}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* STAGE 3: External Tools & API Invocations */}
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase font-mono tracking-widest mb-3 flex items-center gap-1.5">
                <Server className="w-3 h-3 text-amber-400" />
                <span>Deterministic Security Tools & Detonation API Tier</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[nodes.safe_browsing_tool, nodes.threat_intel_tools, nodes.sandbox_agent].map((node) => (
                  <div 
                    key={node.id}
                    className={`p-3.5 rounded-lg border transition-all duration-300 ${
                      node.status === 'RUNNING' ? 'bg-amber-500/10 border-amber-500 shadow-lg shadow-amber-500/10' :
                      node.status === 'COMPLETED' ? 'bg-black/40 border-green-500/30' :
                      'bg-black/20 border-white/5 opacity-70'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-bold text-xs text-white flex items-center gap-1.5">
                        {node.id === 'sandbox_agent' ? <MonitorPlay className="w-3.5 h-3.5 text-amber-400" /> : <GlobeLock className="w-3.5 h-3.5 text-amber-400" />}
                        {node.name}
                      </span>
                      {getStatusBadge(node.status)}
                    </div>
                    <p className="text-[11px] text-gray-300 leading-tight font-sans mb-1.5">
                      {node.lastMessage}
                    </p>
                    {node.activeTool && (
                      <div className="inline-flex items-center gap-1 bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded text-[10px] font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
                        Tool Call: {node.activeTool}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* STAGE 4: Correlation, Fusion & Risk Verdict */}
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase font-mono tracking-widest mb-3">
                Phase 3: Evidence Fusion, Risk Calculation & Mitigation Playbook
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {[nodes.evidence_fusion, nodes.threat_intelligence, nodes.risk_agent, nodes.response_agent].map((node) => (
                  <div 
                    key={node.id}
                    className={`p-3 rounded-lg border transition-all duration-300 ${
                      node.status === 'RUNNING' ? 'bg-purple-500/10 border-purple-500 shadow-lg shadow-purple-500/10 ring-1 ring-purple-500/40' :
                      node.status === 'COMPLETED' ? 'bg-black/40 border-green-500/30' :
                      'bg-black/20 border-white/5 opacity-70'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-white truncate max-w-[110px]">{node.name}</span>
                      {getStatusBadge(node.status)}
                    </div>
                    <p className="text-[11px] text-gray-300 leading-tight line-clamp-2 font-sans mb-1.5">
                      {node.lastMessage}
                    </p>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>

        {/* Right 4 Cols: Live Activity Feed & Event Stream */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Live Activity Terminal */}
          <div className="glass-panel p-5 space-y-4 flex flex-col h-[700px]">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2 text-white font-bold text-sm uppercase tracking-wide">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span>Live Agent Execution Feed ({events.length})</span>
              </div>
              
              <select
                value={filterAgent}
                onChange={(e) => setFilterAgent(e.target.value)}
                className="bg-black/60 border border-white/10 rounded px-2 py-0.5 text-[10px] text-gray-300 font-mono focus:outline-none"
              >
                <option value="all">All Agents</option>
                <option value="orchestrator">Orchestrator</option>
                <option value="url">URL Agent</option>
                <option value="safe_browsing">Safe Browsing</option>
                <option value="risk">Risk Agent</option>
              </select>
            </div>

            {/* Scrolling Feed Window */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
              {filteredEvents.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-500 text-center p-4">
                  <Cpu className="w-8 h-8 mb-2 opacity-30 animate-pulse" />
                  <span>Waiting for agent event stream...</span>
                  <span className="text-[10px] text-gray-600 mt-1">Select or launch an investigation to observe live telemetry.</span>
                </div>
              ) : (
                filteredEvents.map((ev, idx) => {
                  const isError = ev.event_type === 'agent_failed' || ev.status === 'FAILED';
                  const isRisk = ev.event_type === 'risk_updated';
                  const isTool = ev.event_type === 'tool_started' || ev.event_type === 'tool_completed';

                  return (
                    <div 
                      key={idx}
                      className={`p-2.5 rounded border text-[11px] leading-relaxed transition-all ${
                        isError ? 'bg-red-500/10 border-red-500/30 text-red-300' :
                        isRisk ? 'bg-amber-500/10 border-amber-500/30 text-amber-200' :
                        isTool ? 'bg-blue-500/10 border-blue-500/30 text-blue-200' :
                        'bg-black/40 border-white/5 text-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] text-gray-400 mb-1">
                        <span className="text-primary font-bold flex items-center gap-1">
                          <span className="text-gray-500">{new Date(ev.timestamp || Date.now()).toLocaleTimeString()}</span>
                          <span>•</span>
                          <span>{ev.agent_name || ev.agent_id}</span>
                        </span>
                        <span className="uppercase text-[9px] px-1.5 py-0.2 rounded bg-white/5">
                          {ev.event_type.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-gray-200 font-sans">{ev.message}</div>
                    </div>
                  );
                })
              )}
              <div ref={terminalEndRef} />
            </div>

            {/* Clear / Status Footer */}
            <div className="border-t border-white/10 pt-2 flex items-center justify-between text-[11px] font-mono text-gray-500">
              <span>Investigation: <strong className="text-gray-300">{selectedInvId ? selectedInvId.slice(0, 8) : 'None'}</strong></span>
              <button 
                onClick={() => setEvents([])}
                className="hover:text-white transition text-[10px] text-gray-400"
              >
                Clear Terminal
              </button>
            </div>

          </div>

        </div>

      </div>

    </div>
  );
};
