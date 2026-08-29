import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { 
  Mail, Inbox, RefreshCw, Copy, Check, AlertTriangle, ShieldAlert,
  ShieldCheck, GlobeLock, MonitorPlay, ArrowRight, Clock, Plus,
  Trash2, ExternalLink, Sparkles, Terminal, FileText, CheckCircle2
} from 'lucide-react';

export const EmailScanner = () => {
  const queryClient = useQueryClient();
  const [selectedInboxId, setSelectedInboxId] = useState<string | null>(null);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [autoPoll, setAutoPoll] = useState(true);
  const [customPrefix, setCustomPrefix] = useState('');
  const [isCreating, setIsCreating] = useState(false);

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
    refetchInterval: autoPoll ? 4000 : false
  });

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
        return <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded text-xs font-bold">CRITICAL ({score ?? 85})</span>;
      case 'HIGH':
        return <span className="bg-orange-500/20 text-orange-400 border border-orange-500/30 px-2 py-0.5 rounded text-xs font-bold">HIGH ({score ?? 65})</span>;
      case 'MEDIUM':
      case 'SUSPICIOUS':
        return <span className="bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2 py-0.5 rounded text-xs font-bold">MEDIUM ({score ?? 45})</span>;
      case 'LOW':
        return <span className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded text-xs font-bold">LOW ({score ?? 20})</span>;
      case 'SAFE':
        return <span className="bg-green-500/20 text-green-400 border border-green-500/30 px-2 py-0.5 rounded text-xs font-bold">SAFE ({score ?? 5})</span>;
      default:
        return <span className="bg-gray-500/20 text-gray-400 border border-gray-500/30 px-2 py-0.5 rounded text-xs font-bold">ANALYZING...</span>;
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
              Live Email Threat Ingestion
            </h1>
            <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1.5 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> TempMail.so
            </span>
          </div>
          <p className="text-gray-400 mt-1">Receive live incoming emails, automatically normalize headers/attachments, and execute autonomous multi-agent phishing investigations.</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsCreating(true)}
            className="bg-primary text-primary-foreground font-bold px-5 py-2.5 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" /> Create New Inbox
          </button>
        </div>
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
                Auto-Sync: {autoPoll ? 'ON (4s)' : 'PAUSED'}
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

        {/* Right Column: Live Analysis & Forensics */}
        <div className="lg:col-span-7 space-y-6">
          {activeMessage ? (
            <div className="space-y-6 animate-in fade-in">
              
              {/* Message Header Card */}
              <div className="glass-panel p-6 border border-white/10 space-y-4">
                <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white">{activeMessage.subject}</h3>
                    <div className="text-xs text-gray-400 font-mono mt-1 space-y-0.5">
                      <div>From: <span className="text-gray-200">{activeMessage.sender}</span></div>
                      <div>To: <span className="text-gray-200">{activeMessage.recipient}</span></div>
                    </div>
                  </div>

                  {invDetail && (
                    <div className="text-right">
                      <div className="text-[10px] text-gray-400 uppercase font-mono">Autonomous Triage</div>
                      <div className="text-lg font-bold font-mono text-primary">{invDetail.risk_score}/100</div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        invDetail.risk_level === 'CRITICAL' ? 'bg-red-500/20 text-red-400' :
                        invDetail.risk_level === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                        invDetail.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {invDetail.risk_level}
                      </span>
                    </div>
                  )}
                </div>

                {/* Email Body Preview */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Normalized Email Content</div>
                  <div className="bg-black/60 border border-white/5 rounded-lg p-4 font-mono text-xs text-gray-300 max-h-48 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    {activeMessage.text_body || activeMessage.raw_eml || 'No plain text content available.'}
                  </div>
                </div>

                {/* Extracted URLs */}
                {activeMessage.extracted_urls?.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                      <GlobeLock className="w-3.5 h-3.5 text-primary" /> Extracted URLs Forwarded to Deep Analysis
                    </div>
                    <div className="space-y-1 font-mono text-xs">
                      {activeMessage.extracted_urls.map((url: string, idx: number) => (
                        <div key={idx} className="bg-black/40 border border-white/5 p-2 rounded truncate text-gray-300 flex items-center justify-between">
                          <span className="truncate">{url}</span>
                          <span className="text-[10px] text-primary font-bold ml-2">ROUTED TO AGENTS</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Synthesized Forensic Threat Report */}
              {reportData && (
                <div className="glass-panel p-6 border border-white/10 space-y-6">
                  <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-primary" /> Autonomous Forensic Assessment
                    </h3>
                    <Link 
                      to={`/investigations/${activeMessage.investigation_id}`} 
                      className="text-xs text-primary hover:underline font-semibold flex items-center gap-1"
                    >
                      View Investigation Graph <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>

                  {/* Executive Summary */}
                  <div className="bg-black/40 border border-white/5 p-4 rounded-lg space-y-2">
                    <h4 className="text-xs font-bold text-primary uppercase tracking-wider">Executive Summary</h4>
                    <p className="text-xs text-gray-300 leading-relaxed font-medium">
                      {reportData.executive_summary?.summary}
                    </p>
                  </div>

                  {/* Agent Findings */}
                  {reportData.agent_findings?.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Multi-Agent Intelligence Findings</h4>
                      <div className="space-y-2">
                        {reportData.agent_findings.map((f: any, idx: number) => (
                          <div key={idx} className="bg-black/40 border border-white/5 p-3 rounded-lg flex items-start gap-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 mt-0.5 ${
                              f.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                              f.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                              'bg-yellow-500/20 text-yellow-400'
                            }`}>
                              +{f.risk_contribution} pts
                            </span>
                            <div>
                              <div className="text-xs font-semibold text-white">{f.title}</div>
                              <div className="text-[11px] text-gray-400 mt-0.5">{f.description}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* MITRE Threat Matrix */}
                  {reportData.mitre_attack_matrix?.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider">MITRE ATT&CK Matrix</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
                        {reportData.mitre_attack_matrix.map((m: any, idx: number) => (
                          <div key={idx} className="bg-black/50 border border-white/5 p-2.5 rounded">
                            <span className="text-purple-300 font-bold block">{m.technique_id} - {m.technique}</span>
                            <span className="text-gray-400 text-[10px] font-sans">{m.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tactical Containment Playbook */}
                  {reportData.containment_playbook?.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                        <Terminal className="w-4 h-4" /> Recommended Containment Actions
                      </h4>
                      <div className="space-y-2 font-sans text-xs">
                        {reportData.containment_playbook.map((pb: any, idx: number) => (
                          <div key={idx} className="bg-black/60 border border-white/10 p-3 rounded-lg space-y-1">
                            <div className="flex justify-between font-bold text-white">
                              <span>{pb.step}</span>
                              <span className="text-[10px] font-mono text-amber-400">{pb.priority}</span>
                            </div>
                            <p className="text-gray-300 text-[11px]">{pb.action}</p>
                            <div className="bg-black/80 text-emerald-400 font-mono text-[11px] p-2 rounded">
                              $ {pb.command}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                </div>
              )}

            </div>
          ) : (
            <div className="glass-panel p-12 text-center space-y-3 border border-white/10">
              <Mail className="w-12 h-12 text-gray-600 mx-auto opacity-40" />
              <h3 className="text-base font-bold text-white">Select an Email Message</h3>
              <p className="text-xs text-gray-400 max-w-sm mx-auto">Choose a message from the incoming list on the left to inspect multi-agent findings, live threat intelligence lookups, and sandbox detonation.</p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
};
