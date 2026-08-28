import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Globe, Mail, MessageSquare, QrCode, Monitor, Share2, Sparkles } from 'lucide-react';

export const Analyze = () => {
  const [inputType, setInputType] = useState('URL');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const tabs = [
    { id: 'URL', icon: Globe, label: 'URL / Link' },
    { id: 'EMAIL', icon: Mail, label: 'Email Source' },
    { id: 'SMS', icon: MessageSquare, label: 'SMS / Text' },
    { id: 'QR', icon: QrCode, label: 'QR Payload' },
    { id: 'WEBPAGE', icon: Monitor, label: 'Web Page' },
    { id: 'SOCIAL', icon: Share2, label: 'Social Post' },
  ];

  const loadDemo = () => {
    setInputType('SMS');
    setContent('URGENT: Verify your crypto wallet at http://malicious.test/login before it is locked.');
  };

  const startAnalysis = async () => {
    if (!content) return;
    setLoading(true);
    try {
      const res = await fetch('/api/investigations/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_type: inputType, content })
      });
      const data = await res.json();
      navigate(`/investigations/${data.investigation_id}`);
    } catch (e) {
      alert('Failed to start analysis');
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Analyze Threat</h1>
          <p className="text-gray-400">Submit an artifact for automated multi-agent triage and investigation.</p>
        </div>
        <button 
          onClick={loadDemo}
          className="flex items-center gap-2 text-xs font-bold text-orange-400 bg-orange-500/10 hover:bg-orange-500/20 px-3 py-1.5 rounded transition border border-orange-500/20"
        >
          <Sparkles className="w-3 h-3" />
          LOAD DEMO PAYLOAD
        </button>
      </div>

      <div className="glass-panel overflow-hidden border border-white/10 shadow-2xl">
        
        {/* Tabs */}
        <div className="flex border-b border-white/10 overflow-x-auto bg-black/40">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = inputType === tab.id;
            return (
              <button 
                key={tab.id}
                className={`flex items-center gap-2 px-6 py-4 font-semibold text-sm transition relative whitespace-nowrap ${
                  isActive ? 'text-primary bg-white/5' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`}
                onClick={() => setInputType(tab.id)}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-primary' : 'text-gray-500'}`} />
                {tab.label}
                {isActive && (
                  <div className="absolute bottom-0 left-0 w-full h-0.5 bg-primary shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
                )}
              </button>
            );
          })}
        </div>
        
        {/* Input Area */}
        <div className="p-8 bg-background/50">
          <div className="mb-4 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-300">Raw Artifact Data</span>
          </div>
          
          <textarea
            className="w-full h-56 bg-[#050505] border border-white/10 rounded-lg p-5 mb-6 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 text-white font-mono text-sm leading-relaxed resize-none shadow-inner placeholder:text-gray-700"
            placeholder={`Paste raw ${tabLabel(inputType)} data here...\n\nThe Universal Input Processor will automatically normalize the content, extract IoCs, and trigger the appropriate intelligence agents.`}
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          
          <div className="flex justify-end gap-4">
            <button 
              className="text-gray-400 font-semibold px-6 py-2.5 rounded-md hover:text-white transition"
              onClick={() => setContent('')}
              disabled={loading || !content}
            >
              Clear
            </button>
            <button 
              className="bg-primary text-primary-foreground font-bold px-8 py-2.5 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] disabled:opacity-50 flex items-center gap-2"
              onClick={startAnalysis}
              disabled={loading || !content}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin"></span>
                  Processing...
                </>
              ) : (
                'Start Analysis'
              )}
            </button>
          </div>
        </div>
      </div>
      
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 flex gap-3 text-sm text-blue-300">
        <div className="mt-0.5">ℹ️</div>
        <div>
          <p className="font-semibold mb-1">How it works</p>
          <p className="opacity-80 leading-relaxed">
            Upon submission, the <strong>Triage Agent</strong> will calculate priority. High-priority items will be sent to the <strong>Investigation Planner</strong>, which dynamically builds a multi-agent execution pipeline involving URL, Brand, Content, Threat Intelligence, and Sandbox agents.
          </p>
        </div>
      </div>
      
    </div>
  );
};

function tabLabel(id: string) {
  const map: Record<string, string> = {
    URL: 'URL or Link',
    EMAIL: 'Email EML source',
    SMS: 'SMS text message',
    QR: 'QR Code payload',
    WEBPAGE: 'Web Page HTML',
    SOCIAL: 'Social Media post',
  };
  return map[id] || id;
}
