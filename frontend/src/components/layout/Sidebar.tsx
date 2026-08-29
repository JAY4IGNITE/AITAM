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
  Mail
} from 'lucide-react';

export const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Analyze Threat', path: '/analyze', icon: Search },
    { name: 'Email Threat Ingestion', path: '/email-scanner', icon: Mail, highlight: true },
    { name: 'Investigation Cases', path: '/investigations', icon: Activity },
    { name: 'Threat Intel Center', path: '/threat-intel', icon: GlobeLock },
    { name: 'SOC Incidents', path: '/incidents', icon: AlertTriangle },
    { name: 'Threat Reports', path: '/reports', icon: FileWarning },
    { name: 'Awareness & Training', path: '/education', icon: GraduationCap },
    { name: 'Benchmark Datasets', path: '/datasets', icon: Database },
  ];

  return (
    <aside className="w-64 border-r border-white/10 flex flex-col bg-background h-screen sticky top-0 hidden md:flex z-40">
      <div className="p-6 flex items-center gap-3 border-b border-white/5">
        <div className="p-2 rounded-lg bg-primary/10 border border-primary/20 text-primary">
          <Shield className="w-6 h-6" />
        </div>
        <div>
          <span className="text-lg font-bold tracking-tight block text-white">ThreatLens</span>
          <span className="text-[10px] text-primary uppercase tracking-widest font-mono flex items-center gap-1">
            <Sparkles className="w-2.5 h-2.5" /> Autonomous SOC
          </span>
        </div>
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-3 px-2">Navigation</div>
        
        {navItems.map((item) => {
          const isActive = item.path === '/' 
            ? location.pathname === '/' 
            : location.pathname.startsWith(item.path);
          const Icon = item.icon;
          
          return (
            <Link 
              key={item.name}
              to={item.path} 
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition text-xs font-semibold ${
                isActive 
                  ? item.highlight 
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                    : 'bg-primary/20 text-primary border border-primary/30 shadow-[0_0_10px_rgba(59,130,246,0.15)]' 
                  : item.highlight
                    ? 'text-emerald-400/90 hover:bg-white/5'
                    : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-white/5 space-y-2">
        <Link 
          to="/settings" 
          className={`flex items-center gap-3 px-3 py-2 rounded-lg transition text-xs font-semibold ${
            location.pathname === '/settings' ? 'bg-white/10 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-white'
          }`}
        >
          <Settings className="w-4 h-4" />
          Settings & Health
        </Link>
        <div className="px-3 text-[10px] font-mono text-gray-600">
          Engine v2.0 • Zero-Trust Mode
        </div>
      </div>
    </aside>
  );
};
