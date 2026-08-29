import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, Globe, Mail, MessageSquare, QrCode, Monitor, Share2, 
  Upload, CheckCircle, Image as ImageIcon, Sparkles
} from 'lucide-react';

export const Analyze = () => {
  const [inputType, setInputType] = useState('URL');
  const [content, setContent] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const tabs = [
    { id: 'URL', icon: Globe, label: 'URL / Link' },
    { id: 'EMAIL', icon: Mail, label: 'Email (.eml / raw)' },
    { id: 'SMS', icon: MessageSquare, label: 'SMS / Text' },
    { id: 'QR', icon: QrCode, label: 'QR Image / Code' },
    { id: 'WEBPAGE', icon: Monitor, label: 'Web Page' },
    { id: 'SOCIAL', icon: Share2, label: 'Social Message' },
  ];

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setFilePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const startAnalysis = async () => {
    if (inputType === 'QR' && selectedFile) {
      // Multipart upload
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
        navigate(`/investigations/${data.investigation_id}`);
      } catch (e: any) {
        alert(`Failed to analyze QR image: ${e.message}`);
        setLoading(false);
      }
      return;
    }

    if (!content) return;
    setLoading(true);
    try {
      const res = await fetch('/api/investigations/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_type: inputType, content })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Analysis request failed');
      }
      const data = await res.json();
      navigate(`/investigations/${data.investigation_id}`);
    } catch (e: any) {
      alert(`Failed to start analysis: ${e.message}`);
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Analyze Threat Vector</h1>
          <p className="text-gray-400">Submit an artifact for autonomous multi-agent triage, threat intelligence correlation, and sandbox detonation.</p>
        </div>
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
                onClick={() => {
                  setInputType(tab.id);
                  setSelectedFile(null);
                  setFilePreview(null);
                }}
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
          {inputType === 'QR' ? (
            <div className="space-y-6">
              <div 
                className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer transition ${
                  dragOver ? 'border-primary bg-primary/10' : filePreview ? 'border-emerald-500/50 bg-black/40' : 'border-white/10 hover:border-white/20 bg-black/20'
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
                  accept="image/png,image/jpeg,image/jpg,image/webp,image/bmp" 
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      handleFileChange(e.target.files[0]);
                    }
                  }}
                />

                {filePreview ? (
                  <div className="flex flex-col items-center gap-4">
                    <img src={filePreview} alt="QR Preview" className="max-h-48 rounded-lg border border-white/10 shadow-lg object-contain" />
                    <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                      <CheckCircle className="w-4 h-4" /> Ready for decoding ({selectedFile?.name})
                    </div>
                    <span className="text-xs text-gray-500">Click or drop another image to replace</span>
                  </div>
                ) : (
                  <div className="text-center space-y-3">
                    <div className="p-4 rounded-full bg-primary/10 text-primary w-fit mx-auto">
                      <Upload className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-white font-semibold text-base">Drop QR code image here or click to browse</p>
                      <p className="text-gray-500 text-xs mt-1">Supports PNG, JPEG, WebP (Max 10MB)</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3">
                <div className="h-[1px] bg-white/10 flex-1"></div>
                <span className="text-xs text-gray-500 uppercase tracking-widest">or paste payload</span>
                <div className="h-[1px] bg-white/10 flex-1"></div>
              </div>

              <textarea
                className="w-full h-24 bg-[#050505] border border-white/10 rounded-lg p-4 focus:outline-none focus:border-primary/50 text-white font-mono text-sm resize-none"
                placeholder="Or paste QR payload text / Base64 data URI here..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
            </div>
          ) : (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-300">Raw Artifact Data</span>
                </div>
                <span className="text-xs text-gray-500 font-mono">Format: {inputType}</span>
              </div>
              
              <textarea
                className="w-full h-56 bg-[#050505] border border-white/10 rounded-lg p-5 mb-6 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 text-white font-mono text-sm leading-relaxed resize-none shadow-inner placeholder:text-gray-700"
                placeholder={`Paste raw ${tabLabel(inputType)} data here...\n\nThe Universal Input Processor will automatically normalize the content, extract IoCs, and trigger the appropriate intelligence agents.`}
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
            </div>
          )}
          
          <div className="flex justify-end gap-4 mt-6">
            <button 
              className="text-gray-400 font-semibold px-6 py-2.5 rounded-md hover:text-white transition text-sm"
              onClick={() => {
                setContent('');
                setSelectedFile(null);
                setFilePreview(null);
              }}
              disabled={loading || (!content && !selectedFile)}
            >
              Clear
            </button>
            <button 
              className="bg-primary text-primary-foreground font-bold px-8 py-2.5 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] disabled:opacity-50 flex items-center gap-2 text-sm"
              onClick={startAnalysis}
              disabled={loading || (!content && !selectedFile)}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin"></span>
                  Processing Pipeline...
                </>
              ) : (
                'Start Investigation'
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Workflow Explanation Banner */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 flex gap-3 text-sm text-blue-300">
        <div className="mt-0.5"><Sparkles className="w-5 h-5 text-blue-400" /></div>
        <div>
          <p className="font-semibold mb-1">Autonomous Investigation Workflow</p>
          <p className="opacity-80 leading-relaxed text-xs">
            1. Universal Preprocessor normalizes artifact & extracts IoCs (URLs, Domains, IPs, Emails).<br />
            2. Triage & Planner dynamic agents assign priority level and spawn specialized workers.<br />
            3. Real-time Threat Intelligence queries URLhaus, VirusTotal, Google Safe Browsing, and local DB.<br />
            4. Adaptive Sandbox detonates suspicious destinations in isolated headless Chromium.<br />
            5. Evidence Fusion & Explainable Risk engine synthesizes final attack narrative.
          </p>
        </div>
      </div>
      
    </div>
  );
};

function tabLabel(id: string) {
  const map: Record<string, string> = {
    URL: 'URL or Link (e.g. http://suspicious-domain.com/login)',
    EMAIL: 'Raw Email headers and body (.eml or pasted RFC822 text)',
    SMS: 'SMS text message containing links or OTP lures',
    QR: 'QR Code payload / base64',
    WEBPAGE: 'Web Page URL or raw HTML',
    SOCIAL: 'Social Media direct message or post content',
  };
  return map[id] || id;
}
