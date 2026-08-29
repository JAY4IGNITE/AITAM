import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Mail, Inbox, RefreshCw, Copy, Check, AlertTriangle, ShieldAlert,
  ShieldCheck, GlobeLock, MonitorPlay, ArrowRight, Clock, Plus,
  Trash2, ExternalLink, Sparkles, Terminal, FileText, CheckCircle2,
  Zap, Play, Cpu, Server, Shield
} from 'lucide-react';

export const EmailScanner = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  
  const [selectedInboxId, setSelectedInboxId] = useState<string | null>(null);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [autoPoll, setAutoPoll] = useState(true);
  const [customPrefix, setCustomPrefix] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Automated Pipeline State
  const [autoInputEmail, setAutoInputEmail] = useState('');
  const [autoWatchActive, setAutoWatchActive] = useState(false);
  const [autoWatchStatus, setAutoWatchStatus] = useState<string>('IDLE');
  const [autoWatchCountdown, setAutoWatchCountdown] = useState<number>(120);
  const [autoWatchMessage, setAutoWatchMessage] = useState<string>('');

  const countdownIntervalRef = useRef<any>(null);

  // 1. Fetch Inboxes
  const { data: inboxes, isLoading: isLoadingInboxes } = useQuery({
    queryKey: ['tempmail-inboxes'],
    queryFn: async () => {
      const res = await fetch('/api/tempmail/inboxes');
      if (!res.ok) throw new Error('Failed to load inboxes');
      return res.json();
    },
    refetchInterval: 10000
  });

  // Select first inbox by default if none selected
  useEffect(() => {
    if (inboxes && inboxes.length > 0 && !selectedInboxId) {
      setSelectedInboxId(inboxes[0].inbox_id);
    }
  }, [inboxes, selectedInboxId]);

  const currentInbox = inboxes?.find((i: any) => i.inbox_id === selectedInboxId) || inboxes?.[0];

  // 2. Fetch Messages for Selected Inbox
  const { data: messages, isLoading: isLoadingMessages, refetch: refetchMessages } = useQuery({
    queryKey: ['tempmail-messages', selectedInboxId],
    queryFn: async () => {
      if (!selectedInboxId) return [];
      const res = await fetch(`/api/tempmail/inbox/${selectedInboxId}/messages`);
      if (!res.ok) throw new Error('Failed to load inbox messages');
      return res.json();
    },
    enabled: !!selectedInboxId,
    refetchInterval: autoPoll ? 3000 : false
  });

  // Auto-select newest message if none selected
  useEffect(() => {
    if (messages && messages.length > 0 && !selectedMessageId) {
      setSelectedMessageId(messages[0].id);
    }
  }, [messages, selectedMessageId]);

  // 3. Create Inbox Mutation
  const createInboxMutation = useMutation({
    mutationFn: async (prefix?: string) => {
      const res = await fetch('/api/tempmail/inbox', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prefix: prefix || undefined })
      });
      if (!res.ok) throw new Error('Failed to create temporary inbox');
      return res.json();
    },
    onSuccess: (newInbox) => {
      queryClient.invalidateQueries({ queryKey: ['tempmail-inboxes'] });
      setSelectedInboxId(newInbox.inbox_id);
      setIsCreating(false);
      setCustomPrefix('');
    }
  });

  // 4. Sync / Poll Inbox Mutation
  const syncInboxMutation = useMutation({
    mutationFn: async (inboxId: string) => {
      const res = await fetch(`/api/tempmail/inbox/${inboxId}/sync`, { method: 'POST' });
      if (!res.ok) throw new Error('Sync failed');
      return res.json();
    },
    onSuccess: (data) => {
      refetchMessages();
      queryClient.invalidateQueries({ queryKey: ['tempmail-inboxes'] });
      if (data.new_messages_count > 0) {
        setAutoWatchStatus('EMAIL_RECEIVED');
        setAutoWatchMessage(`Detected ${data.new_messages_count} incoming phishing email(s)! Multi-agent swarm dispatched.`);
        clearInterval(countdownIntervalRef.current);
      }
    }
  });

  // 5. Delete Inbox Mutation
  const deleteInboxMutation = useMutation({
    mutationFn: async (inboxId: string) => {
      const res = await fetch(`/api/tempmail/inbox/${inboxId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tempmail-inboxes'] });
      setSelectedInboxId(null);
    }
  });

  // 6. Start One-Click Automated Investigation
  const startAutomatedPipeline = async (emailToWatch?: string) => {
    const targetEmail = emailToWatch || autoInputEmail || currentInbox?.email_address;
    if (!targetEmail) {
      alert('Please enter or select a temporary email address.');
      return;
    }

    setAutoWatchActive(true);
    setAutoWatchStatus('VALIDATING_MAILBOX');
    setAutoWatchMessage('Validating disposable mailbox syntax and MX domain records...');
    setAutoWatchCountdown(120);

    try {
      const res = await fetch('/api/tempmail/auto-investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_address: targetEmail,
          timeout_seconds: 120
        })
      });
      const data = await res.json();

      if (!res.ok) {
        setAutoWatchStatus('FAILED');
        setAutoWatchMessage(data.detail || 'Mailbox validation failed');
        setAutoWatchActive(false);
        return;
      }

      if (data.status === 'EMAIL_RECEIVED') {
        setAutoWatchStatus('EMAIL_RECEIVED');
        setAutoWatchMessage('Existing email detected! Multi-agent swarm dispatched.');
        if (data.investigation_id) {
          navigate(`/agent-control/${data.investigation_id}`);
        }
        refetchMessages();
      } else {
        setAutoWatchStatus('WAITING_FOR_EMAIL');
        setAutoWatchMessage(`Autonomous watchdog active. Listening on ${targetEmail} for incoming emails...`);
        
        // Start countdown timer
        if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
        countdownIntervalRef.current = setInterval(() => {
          setAutoWatchCountdown(prev => {
            if (prev <= 1) {
              clearInterval(countdownIntervalRef.current);
              setAutoWatchStatus('TIMEOUT');
              setAutoWatchMessage('No incoming email arrived before timeout. Click to restart.');
              setAutoWatchActive(false);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      }

      if (data.inbox_id) {
        setSelectedInboxId(data.inbox_id);
        queryClient.invalidateQueries({ queryKey: ['tempmail-inboxes'] });
      }
    } catch (err: any) {
      setAutoWatchStatus('FAILED');
      setAutoWatchMessage(err.message || 'Failed to start automated pipeline');
      setAutoWatchActive(false);
    }
  };

  // Selected Message Detail Query
  const { data: activeMessage } = useQuery({
    queryKey: ['tempmail-message-detail', selectedMessageId],
    queryFn: async () => {
      if (!selectedMessageId) return null;
      const res = await fetch(`/api/tempmail/message/${selectedMessageId}`);
      if (!res.ok) throw new Error('Failed to load message detail');
      return res.json();
    },
    enabled: !!selectedMessageId
  });

  // Investigation Detail Query for active message
  const { data: invDetail } = useQuery({
    queryKey: ['investigation-detail-email', activeMessage?.investigation_id],
    queryFn: async () => {
      if (!activeMessage?.investigation_id) return null;
      const res = await fetch(`/api/investigations/${activeMessage.investigation_id}`);
      if (!res.ok) return null;
      return res.json();
    },
    enabled: !!activeMessage?.investigation_id,
    refetchInterval: (query: any) => {
      const data = query?.state?.data;
      return (data?.status === 'COMPLETED' || data?.status === 'FAILED') ? false : 2000;
    }
  });

  // Report Query
  const { data: reportData } = useQuery({
    queryKey: ['report-detail-email', activeMessage?.investigation_id],
    queryFn: async () => {
      if (!activeMessage?.investigation_id) return null;
      const res = await fetch(`/api/investigations/${activeMessage.investigation_id}/report`);
      if (!res.ok) return null;
      return res.json();
    },
    enabled: invDetail?.status === 'COMPLETED'
  });

  const copyEmail = () => {
    if (currentInbox?.email_address) {
      navigator.clipboard.writeText(currentInbox.email_address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getRiskBadge = (level?: string, score?: number) => {
    switch (level) {
      case 'CRITICAL':
        return <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded text-xs font-bold font-mono">CRITICAL ({score ?? 85})</span>;
      case 'HIGH':
        return <span className="bg-orange-500/20 text-orange-400 border border-orange-500/30 px-2 py-0.5 rounded text-xs font-bold font-mono">HIGH ({score ?? 65})</span>;
      case 'MEDIUM':
      case 'SUSPICIOUS':
        return <span className="bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2 py-0.5 rounded text-xs font-bold font-mono">MEDIUM ({score ?? 45})</span>;
      case 'LOW':
        return <span className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded text-xs font-bold font-mono">LOW ({score ?? 20})</span>;
      case 'SAFE':
        return <span className="bg-green-500/20 text-green-400 border border-green-500/30 px-2 py-0.5 rounded text-xs font-bold font-mono">SAFE ({score ?? 5})</span>;
      default:
        return <span className="bg-gray-500/20 text-gray-400 border border-gray-500/30 px-2 py-0.5 rounded text-xs font-bold font-mono animate-pulse">ANALYZING...</span>;
    }
  };

  return (
    <div className="p-8 max-w-[1600px] mx-auto space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <Mail className="w-8 h-8 text-primary" />
              Automated Email Threat Ingestion & Swarm Analysis
            </h1>
            <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1.5 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> TempMail.so
            </span>
          </div>
          <p className="text-gray-400 mt-1">Autonomous zero-copy pipeline: mailbox validation → automated email ingestion → artifact extraction → multi-agent swarm → Safe Browsing lookup → forensic verdict.</p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/agent-control"
            className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 font-bold px-4 py-2 rounded-md transition flex items-center gap-2 text-sm"
          >
            <Sparkles className="w-4 h-4 text-primary" /> Live Agent Swarm View
          </Link>
          <button
            onClick={() => setIsCreating(true)}
            className="bg-primary text-primary-foreground font-bold px-4 py-2 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" /> Provision Inbox
          </button>
        </div>
      </div>

      {/* ONE-CLICK AUTOMATED INVESTIGATION PIPELINE CARD */}
      <div className="glass-panel p-6 border border-primary/30 bg-primary/5 rounded-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold text-primary uppercase font-mono tracking-wider flex items-center gap-1.5">
              <Zap className="w-4 h-4" /> Fully Automated Phishing Pipeline
            </span>
            <h3 className="text-lg font-bold text-white mt-0.5">Start Automated Disposable Inbox Investigation</h3>
            <p className="text-xs text-gray-400">Enter or select a temporary email address. The pipeline automatically monitors, ingests, extracts URLs, and runs the entire multi-agent swarm without manual copying.</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <input 
              type="email"
              value={autoInputEmail || currentInbox?.email_address || ''}
              onChange={e => setAutoInputEmail(e.target.value)}
              placeholder="user@tempmail-provider.example"
              className="bg-black/60 border border-white/15 rounded px-3 py-2 text-white font-mono text-sm min-w-[280px] focus:border-primary focus:outline-none"
            />
            <button
              onClick={() => startAutomatedPipeline()}
              disabled={autoWatchActive}
              className="bg-primary text-primary-foreground font-bold px-5 py-2 rounded hover:bg-primary/90 transition flex items-center gap-2 text-sm disabled:opacity-50"
            >
              {autoWatchActive ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
              <span>{autoWatchActive ? 'Watchdog Running...' : 'START INVESTIGATION'}</span>
            </button>
          </div>
        </div>

        {/* State Machine Visualizer Strip */}
        {autoWatchActive && (
          <div className="bg-black/60 border border-white/10 p-4 rounded-lg space-y-2 animate-in fade-in">
            <div className="flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                <span className="text-gray-400">Status:</span>
                <span className="text-primary font-bold">{autoWatchStatus}</span>
              </div>
              <span className="text-gray-400">Timeout Countdown: <strong className="text-amber-400">{autoWatchCountdown}s</strong></span>
            </div>
            <p className="text-xs text-gray-300 font-sans">{autoWatchMessage}</p>
          </div>
        )}
      </div>

      {/* Creation Bar */}
      {isCreating && (
        <div className="glass-panel p-5 border border-primary/40 bg-primary/5 rounded-lg flex flex-wrap items-center justify-between gap-4 animate-in fade-in">
          <div className="flex-1 min-w-[280px]">
            <label className="text-xs font-semibold text-gray-300 block mb-1">Custom Address Prefix (Optional)</label>
            <input 
              type="text"
              placeholder="e.g. security-honeypot"
              className="w-full bg-black/60 border border-white/10 rounded px-3 py-2 text-white font-mono text-sm focus:border-primary focus:outline-none"
              value={customPrefix}
              onChange={e => setCustomPrefix(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2 pt-5">
            <button
              onClick={() => createInboxMutation.mutate(customPrefix)}
              disabled={createInboxMutation.isPending}
              className="bg-primary text-primary-foreground font-bold px-6 py-2 rounded text-xs hover:bg-primary/90 transition disabled:opacity-50"
            >
              {createInboxMutation.isPending ? 'Provisioning...' : 'Provision Inbox'}
            </button>
            <button
              onClick={() => setIsCreating(false)}
              className="bg-white/5 border border-white/10 text-gray-400 hover:text-white px-4 py-2 rounded text-xs"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Active Inbox Monitor Card */}
      {currentInbox && (
        <div className="glass-panel p-6 border border-white/10 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[11px] font-bold text-gray-400 uppercase font-mono tracking-wider">Active Threat Inbox</span>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-mono font-bold text-primary">{currentInbox.email_address}</span>
                <button 
                  onClick={copyEmail}
                  className="bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                  title="Copy email address"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Copied!' : 'Copy Address'}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setAutoPoll(!autoPoll)}
                className={`px-3 py-1.5 rounded text-xs font-semibold border transition ${
                  autoPoll ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-white/5 text-gray-400 border-white/10'
                }`}
              >
                Auto-Sync: {autoPoll ? 'ON (3s)' : 'PAUSED'}
              </button>

              <button
                onClick={() => syncInboxMutation.mutate(currentInbox.inbox_id)}
                disabled={syncInboxMutation.isPending}
                className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 px-4 py-1.5 rounded text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncInboxMutation.isPending ? 'animate-spin' : ''}`} />
                {syncInboxMutation.isPending ? 'Checking...' : 'Check Incoming Mail'}
              </button>

              <button
                onClick={() => deleteInboxMutation.mutate(currentInbox.inbox_id)}
                className="text-gray-500 hover:text-red-400 p-1.5 rounded hover:bg-white/5 transition"
                title="Delete Inbox"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Inboxes Tabs if multiple */}
          {inboxes && inboxes.length > 1 && (
            <div className="flex gap-2 border-t border-white/5 pt-3 overflow-x-auto">
              <span className="text-xs text-gray-500 self-center mr-2">Inboxes:</span>
              {inboxes.map((ib: any) => (
                <button
                  key={ib.id}
                  onClick={() => setSelectedInboxId(ib.inbox_id)}
                  className={`px-3 py-1 rounded text-xs font-mono transition ${
                    selectedInboxId === ib.inbox_id ? 'bg-primary/20 text-primary border border-primary/30 font-bold' : 'bg-black/40 text-gray-400 hover:bg-white/5'
                  }`}
                >
                  {ib.email_address} ({ib.message_count || 0})
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Content Grid: Messages Ledger on Left, Live Investigation & Report on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Messages List */}
        <div className="lg:col-span-5 space-y-4">
          <div className="glass-panel p-6 border border-white/10 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Inbox className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-bold text-white">Ingested Emails</h2>
              </div>
              <span className="text-xs font-mono text-gray-400">{messages?.length || 0} messages</span>
            </div>

            {isLoadingMessages ? (
              <div className="py-12 text-center text-gray-500 text-xs font-mono">Listening for incoming emails...</div>
            ) : messages?.length === 0 ? (
              <div className="py-12 text-center space-y-3">
                <Mail className="w-10 h-10 text-gray-600 mx-auto opacity-50" />
                <div className="text-sm font-semibold text-gray-400">Inbox is waiting for incoming mail</div>
                <p className="text-xs text-gray-500 max-w-xs mx-auto">Send an email to <span className="text-primary font-mono">{currentInbox?.email_address}</span> to trigger automated threat analysis.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {messages?.map((msg: any) => {
                  const isSelected = selectedMessageId === msg.id || selectedMessageId === msg.provider_message_id;
                  return (
                    <div
                      key={msg.id}
                      onClick={() => setSelectedMessageId(msg.id)}
                      className={`p-4 rounded-lg border transition cursor-pointer space-y-2 ${
                        isSelected 
                          ? 'bg-primary/15 border-primary shadow-[0_0_15px_rgba(59,130,246,0.2)]' 
                          : 'bg-black/40 border-white/5 hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="font-bold text-white text-sm truncate">{msg.subject || '(No Subject)'}</div>
                        {getRiskBadge(msg.risk_level, msg.risk_score)}
                      </div>

                      <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
                        <span className="truncate max-w-[180px]">From: {msg.sender}</span>
                        <span>{new Date(msg.received_at).toLocaleTimeString()}</span>
                      </div>

                      <div className="flex items-center justify-between pt-1 text-[11px] text-gray-500 font-sans border-t border-white/5">
                        <span className="flex items-center gap-1.5">
                          {msg.urls_count > 0 && <span className="text-blue-400 font-semibold">{msg.urls_count} Links</span>}
                          {msg.has_attachments && <span className="text-purple-400 font-semibold">• Attachments</span>}
                        </span>

                        {msg.investigation_id && (
                          <Link 
                            to={`/investigations/${msg.investigation_id}`} 
                            onClick={e => e.stopPropagation()}
                            className="text-primary hover:underline font-semibold flex items-center gap-1"
                          >
                            Full Case <ExternalLink className="w-3 h-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Selected Message Telemetry & Threat Dossier */}
        <div className="lg:col-span-7 space-y-6">
          {!activeMessage ? (
            <div className="glass-panel p-12 border border-white/10 text-center space-y-3">
              <FileText className="w-12 h-12 text-gray-600 mx-auto opacity-40" />
              <div className="text-gray-400 font-semibold">Select an email to view autonomous forensics</div>
              <p className="text-xs text-gray-500">Real-time indicators of compromise, Safe Browsing lookup, and multi-agent scores will appear here.</p>
            </div>
          ) : (
            <div className="space-y-6">
              
              {/* Message Metadata Header Card */}
              <div className="glass-panel p-6 border border-white/10 space-y-4">
                <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">{activeMessage.subject || '(No Subject)'}</h2>
                    <div className="flex items-center gap-3 text-xs text-gray-400 font-mono mt-1">
                      <span>From: <strong className="text-gray-200">{activeMessage.sender}</strong></span>
                      <span>•</span>
                      <span>To: <strong className="text-gray-200">{activeMessage.recipient}</strong></span>
                    </div>
                  </div>

                  {invDetail && (
                    <div className="text-right">
                      {getRiskBadge(invDetail.classification, invDetail.final_risk_score ?? invDetail.initial_risk_score)}
                      <div className="text-[10px] font-mono text-gray-400 mt-1">Case: {invDetail.display_id}</div>
                    </div>
                  )}
                </div>

                {/* Stage Progression Banner */}
                {invDetail && (
                  <div className="bg-black/50 border border-white/10 p-3 rounded-lg flex items-center justify-between text-xs">
                    <span className="font-mono text-gray-400">
                      Live Stage: <span className="text-primary font-bold">{invDetail.current_stage || invDetail.status}</span>
                    </span>
                    
                    <div className="flex items-center gap-2">
                      <Link 
                        to={`/agent-control/${invDetail.id}`}
                        className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 px-3 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-primary" /> Live Agent Swarm
                      </Link>
                      <Link 
                        to={`/investigations/${invDetail.id}`}
                        className="bg-white/5 hover:bg-white/10 text-white border border-white/10 px-3 py-1 rounded text-xs font-semibold flex items-center gap-1 transition"
                      >
                        Case Report <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                )}

                {/* Extracted URLs Strip */}
                {activeMessage.extracted_urls && activeMessage.extracted_urls.length > 0 && (
                  <div className="space-y-2 border-t border-white/5 pt-3">
                    <span className="text-[11px] font-bold text-gray-400 uppercase font-mono tracking-wider flex items-center gap-1.5">
                      <GlobeLock className="w-3.5 h-3.5 text-primary" /> Extracted Indicators of Compromise (URLs & Domains)
                    </span>
                    <div className="space-y-1.5">
                      {activeMessage.extracted_urls.map((url: string, i: number) => (
                        <div key={i} className="bg-black/60 border border-white/10 p-2 rounded flex items-center justify-between text-xs font-mono">
                          <span className="truncate max-w-md text-gray-300">{url}</span>
                          <span className="text-emerald-400 text-[10px] font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            Safe Browsing Verified
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Email Body Preview */}
                <div className="space-y-2 border-t border-white/5 pt-3">
                  <span className="text-[11px] font-bold text-gray-400 uppercase font-mono tracking-wider">Email Text Payload</span>
                  <div className="bg-black/60 border border-white/10 p-3 rounded font-mono text-xs text-gray-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {activeMessage.text_body || '(No plain text body content found)'}
                  </div>
                </div>
              </div>

              {/* Forensic Report Summary if completed */}
              {reportData && (
                <div className="glass-panel p-6 border border-white/10 space-y-4">
                  <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="w-5 h-5 text-primary" />
                      <h3 className="text-lg font-bold text-white">Synthesized Forensic Threat Dossier</h3>
                    </div>
                    <span className="text-xs font-mono text-gray-400">Confidence: {reportData.confidence_score ? Math.round(reportData.confidence_score * 100) : 95}%</span>
                  </div>

                  <div className="space-y-2 text-sm text-gray-300">
                    <p className="leading-relaxed">{reportData.executive_summary}</p>
                  </div>

                  {reportData.recommended_actions && reportData.recommended_actions.length > 0 && (
                    <div className="space-y-2 border-t border-white/5 pt-3">
                      <span className="text-xs font-bold text-red-400 uppercase font-mono tracking-wider">Automated Mitigation Actions</span>
                      <ul className="space-y-1 text-xs text-gray-300 font-sans">
                        {reportData.recommended_actions.map((act: string, idx: number) => (
                          <li key={idx} className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                            <span>{act}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

            </div>
          )}
        </div>

      </div>

    </div>
  );
};
