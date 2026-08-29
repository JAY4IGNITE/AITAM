import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Globe, Mail, MessageSquare, QrCode, Monitor, Share2, 
  Upload, CheckCircle, RefreshCw, Terminal, Shield, ArrowRight, Play
} from 'lucide-react';

export const Analyze = () => {
  const [inputType, setInputType] = useState('URL');
  const [content, setContent] = useState('https://suspicious-bank-login.top/auth/verify');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const tabs = [
    { id: 'URL', icon: Globe, label: 'URL / Link', placeholder: 'https://secure-login.suspicious-domain.top/auth', sample: 'https://suspicious-bank-login.top/auth/verify' },
    { id: 'EMAIL', icon: Mail, label: 'Email (.eml / raw)', placeholder: 'From: security@fake-bank.com\nSubject: Urgent Account Verification\n\nPlease confirm your login: https://bank-verify.top/login', sample: 'From: support@paypal-notification.top\nSubject: Account Access Suspended\n\nDear Customer, we detected unauthorized login activity. Re-verify your credentials immediately: https://paypal-security-auth.top/recovery' },
    { id: 'SMS', icon: MessageSquare, label: 'SMS / Text', placeholder: 'URGENT: Your parcel delivery is on hold. Pay fee: http://tracking-fee.top', sample: 'USPS ALERT: Package #9400111 cannot be delivered due to incorrect address. Update details within 24h at http://usps-address-update.top/fee or item will be returned.' },
    { id: 'QR', icon: QrCode, label: 'QR Image / Code', placeholder: 'https://malicious-qr-redirect.top/login', sample: 'https://malicious-qr-redirect.top/login' },
    { id: 'WEBPAGE', icon: Monitor, label: 'Web Page', placeholder: 'https://evil-portal.top/index.html', sample: 'https://evil-credential-portal.top/login.php' },
    { id: 'SOCIAL', icon: Share2, label: 'Social Message', placeholder: 'Hey! You won $5,000 crypto giveaway! Claim: https://gift-claim.top', sample: 'Instagram Security: Your account is scheduled for copyright suspension. Appeal within 24 hours at https://instagram-help-verify.top/appeal' },
  ];

  const currentTab = tabs.find(t => t.id === inputType) || tabs[0];

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setFilePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const loadSample = (sampleText: string) => {
    setContent(sampleText);
  };

  const startAnalysis = async () => {
    if (inputType === 'QR' && selectedFile) {
      setLoading(true);
      try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        const res = await fetch('/api/investigations/upload-qr', {
          method: 'POST',
          body: formData
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'QR upload failed');
        }
        const data = await res.json();
        navigate(`/agent-control/${data.investigation_id}`);
      } catch (e: any) {
        alert(`Failed to analyze QR image: ${e.message}`);
        setLoading(false);
      }
      return;
    }

    if (!content.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/investigations/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_type: inputType, content: content.trim() })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Analysis request failed');
      }
      const data = await res.json();
      navigate(`/agent-control/${data.investigation_id}`);
    } catch (e: any) {
      alert(`Failed to start analysis: ${e.message}`);
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Analyze Threat Vector</h1>
          <p className="text-xs text-zinc-400 mt-1">
            Submit an artifact for autonomous multi-agent triage, Safe Browsing lookup, and threat correlation.
          </p>
        </div>

        <Link
          to="/agent-control"
          className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-md transition text-xs font-medium flex items-center gap-2 self-start md:self-auto"
        >
          <span>Live Swarm Feed</span>
          <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
        </Link>
      </div>

      {/* Main Vector Box */}
      <div className="glass-panel overflow-hidden">
        
        {/* Tabs Bar */}
        <div className="flex border-b border-zinc-800/80 bg-zinc-950 overflow-x-auto p-1 gap-1">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = inputType === tab.id;
            return (
              <button 
                key={tab.id}
                className={`flex items-center gap-2 px-4 py-2.5 font-medium text-xs transition rounded-md whitespace-nowrap ${
                  isActive 
                    ? 'bg-zinc-800 text-white font-semibold' 
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                }`}
                onClick={() => {
                  setInputType(tab.id);
                  setContent(tab.sample);
                  setSelectedFile(null);
                  setFilePreview(null);
                }}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-zinc-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
        
        {/* Input Area */}
        <div className="p-6 space-y-4 bg-zinc-950/40">
          
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">
              Payload ({inputType}):
            </span>
            <button
              onClick={() => loadSample(currentTab.sample)}
              className="text-[11px] text-zinc-400 hover:text-white flex items-center gap-1 transition"
            >
              <RefreshCw className="w-3 h-3" /> Load Sample
            </button>
          </div>

          {inputType === 'QR' ? (
            <div className="space-y-4">
              <div 
                className={`border border-dashed rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition ${
                  dragOver ? 'border-zinc-500 bg-zinc-900' : filePreview ? 'border-zinc-700 bg-zinc-900' : 'border-zinc-800 hover:border-zinc-700 bg-zinc-900/30'
                }`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  if (e.dataTransfer.files?.[0]) {
                    handleFileChange(e.dataTransfer.files[0]);
                  }
                }}
                onClick={() => fileInputRef.current?.click()}
              >
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  className="hidden" 
                  accept="image/png, image/jpeg, image/webp"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      handleFileChange(e.target.files[0]);
                    }
                  }}
                />
                {filePreview ? (
                  <div className="space-y-2 text-center">
                    <img src={filePreview} alt="QR Code Preview" className="max-h-40 rounded mx-auto border border-zinc-700" />
                    <div className="flex items-center justify-center gap-1.5 text-xs text-zinc-300 font-mono">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> {selectedFile?.name}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1.5 text-center">
                    <Upload className="w-5 h-5 text-zinc-500 mx-auto" />
                    <div className="text-xs font-medium text-zinc-300">Click or Drag & Drop QR Image</div>
                    <div className="text-[10px] text-zinc-500 font-mono">PNG, JPG, WEBP</div>
                  </div>
                )}
              </div>

              <input
                type="text"
                value={content}
                onChange={e => setContent(e.target.value)}
                placeholder="Or paste QR decoded URL..."
                className="w-full bg-zinc-900 border border-zinc-800 rounded-md px-3.5 py-2.5 text-white font-mono text-xs focus:outline-none focus:border-zinc-600 transition"
              />
            </div>
          ) : (
            <div>
              {inputType === 'EMAIL' ? (
                <textarea
                  rows={7}
                  value={content}
                  onChange={e => setContent(e.target.value)}
                  placeholder={currentTab.placeholder}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-md p-3.5 text-white font-mono text-xs focus:outline-none focus:border-zinc-600 transition leading-relaxed"
                />
              ) : (
                <input
                  type="text"
                  value={content}
                  onChange={e => setContent(e.target.value)}
                  placeholder={currentTab.placeholder}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-md px-3.5 py-2.5 text-white font-mono text-xs focus:outline-none focus:border-zinc-600 transition"
                />
              )}
            </div>
          )}

          {/* Action Button */}
          <div className="flex items-center justify-between pt-3 border-t border-zinc-800/80">
            <span className="text-xs text-zinc-400 font-mono">
              Multi-agent triage + Safe Browsing enabled
            </span>

            <button
              onClick={startAnalysis}
              disabled={loading || (!content.trim() && !selectedFile)}
              className="bg-white hover:bg-zinc-200 text-zinc-950 font-semibold px-6 py-2 rounded-md transition text-xs flex items-center gap-2 disabled:opacity-40 shadow-sm"
            >
              {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>{loading ? 'Starting...' : 'Start Investigation'}</span>
            </button>
          </div>

        </div>

      </div>

    </div>
  );
};
