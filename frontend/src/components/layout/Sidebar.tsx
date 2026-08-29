import { Link, useLocation } from 'react-router-dom';
import { 
  Shield, 
  LayoutDashboard, 
  Activity, 
  FileWarning, 
  Search, 
  Settings,
  AlertTriangle,
  GlobeLock,
  Database,
  GraduationCap,
  Sparkles,
  Mail,
  Cpu
} from 'lucide-react';

export const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Analyze Threat', path: '/analyze', icon: Search },
    { name: 'Agent Control Center', path: '/agent-control', icon: Cpu },
    { name: 'Email Threat Ingestion', path: '/email-scanner', icon: Mail },
    { name: 'Investigation Cases', path: '/investigations', icon: Activity },
    { name: 'Threat Intel Center', path: '/threat-intel', icon: GlobeLock },
    { name: 'SOC Incidents', path: '/incidents', icon: AlertTriangle },
    { name: 'Threat Reports', path: '/reports', icon: FileWarning },
    { name: 'Awareness & Training', path: '/education', icon: GraduationCap },
    { name: 'Benchmark Datasets', path: '/datasets', icon: Database },
  ];

  return (
    <aside className="w-64 border-r border-zinc-800/80 flex flex-col bg-zinc-950 h-screen sticky top-0 hidden md:flex z-40 select-none">
      {/* Brand Header */}
      <div className="px-5 py-5 flex items-center gap-3 border-b border-zinc-800/60">
        <div className="w-8 h-8 rounded-md bg-white text-zinc-950 flex items-center justify-center font-bold text-sm">
          TL
        </div>
        <div>
          <span className="text-sm font-semibold tracking-tight block text-zinc-100">ThreatLens</span>
          <span className="text-[10px] text-zinc-400 font-mono">Autonomous SOC</span>
        </div>
      </div>
      
      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <div className="text-[10px] font-medium text-zinc-400 uppercase tracking-wider mb-2 px-3">
          Platform
        </div>
        
        {navItems.map((item) => {
          const isActive = item.path === '/' 
            ? location.pathname === '/' 
            : location.pathname.startsWith(item.path);
          const Icon = item.icon;
          
          return (
            <Link 
              key={item.name}
              to={item.path} 
              className={`flex items-center gap-2.5 px-3 py-2 rounded-md transition text-xs font-medium ${
                isActive 
                  ? 'bg-zinc-800/90 text-white font-semibold' 
                  : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-zinc-400'}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
      
      {/* Footer */}
      <div className="p-3 border-t border-zinc-800/60 space-y-1">
        <Link 
          to="/settings" 
          className={`flex items-center gap-2.5 px-3 py-2 rounded-md transition text-xs font-medium ${
            location.pathname === '/settings' ? 'bg-zinc-800 text-white font-semibold' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
          }`}
        >
          <Settings className="w-4 h-4 text-zinc-400" />
          <span>Settings</span>
        </Link>
        <div className="px-3 pt-1 text-[10px] font-mono text-zinc-400">
          v2.0 • Online
        </div>
      </div>
    </aside>
  );
};
