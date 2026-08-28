import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Shield, LayoutDashboard, Activity, FileWarning, Search, SearchCheck } from 'lucide-react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// We'll create these components next
const Dashboard = () => <div className="p-8"><h1 className="text-3xl font-bold mb-6">Dashboard</h1><div className="glass-panel p-6 h-64 flex items-center justify-center">Analytics coming soon</div></div>;

const Investigate = () => {
  const [url, setUrl] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const navigate = import('react-router-dom').then(m => m.useNavigate);
  // Note: we can't easily use hooks dynamically inside this simplified component structure if they aren't imported properly, 
  // so let's just use window.location for MVP.
  
  const submit = async () => {
    if (!url) return;
    setLoading(true);
    try {
      const res = await fetch('/api/investigations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_type: 'URL', target: url })
      });
      const data = await res.json();
      window.location.href = `/investigations/${data.id}`;
    } catch (e) {
      console.error(e);
      alert('Failed to submit');
    }
    setLoading(false);
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Start Investigation</h1>
      <div className="glass-panel p-6 flex flex-col items-center justify-center h-64">
        <input 
          type="text" 
          placeholder="Enter URL to analyze..." 
          className="w-full max-w-lg bg-black/50 border border-white/10 rounded-md p-3 mb-4 focus:outline-none focus:border-primary text-white" 
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button 
          className="bg-primary text-primary-foreground px-6 py-2 rounded-md font-semibold hover:opacity-90 transition disabled:opacity-50"
          onClick={submit}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </div>
  );
};

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-background text-foreground flex">
          {/* Sidebar */}
          <aside className="w-64 border-r border-white/10 flex flex-col glass-panel !border-l-0 !border-t-0 !border-b-0 !rounded-none">
            <div className="p-6 flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary" />
              <span className="text-xl font-bold tracking-tight">ThreatLens</span>
            </div>
            <nav className="flex-1 px-4 space-y-2 mt-4">
              <Link to="/" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition text-sm font-medium">
                <LayoutDashboard className="w-4 h-4 text-gray-400" />
                Dashboard
              </Link>
              <Link to="/investigate" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition text-sm font-medium">
                <Search className="w-4 h-4 text-gray-400" />
                Investigate
              </Link>
              <Link to="/investigations" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition text-sm font-medium">
                <Activity className="w-4 h-4 text-gray-400" />
                Active Cases
              </Link>
              <Link to="/threat-reports" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition text-sm font-medium">
                <FileWarning className="w-4 h-4 text-gray-400" />
                Threat Reports
              </Link>
            </nav>
            <div className="p-6 text-xs text-gray-500">
              Risk-Adaptive Analysis Engine v1.0
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/investigate" element={<Investigate />} />
              <Route path="/investigations" element={<div className="p-8">Active Investigations List</div>} />
              <Route path="/investigations/:id" element={<div className="p-8">Investigation Details</div>} />
              <Route path="/threat-reports" element={<div className="p-8">Threat Reports</div>} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
