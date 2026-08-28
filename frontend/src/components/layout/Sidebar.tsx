import React from 'react';
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
  LineChart
} from 'lucide-react';

export const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Analyze Threat', path: '/analyze', icon: Search },
    { name: 'Active Cases', path: '/investigations', icon: Activity },
    { name: 'SOC Incidents', path: '/incidents', icon: AlertTriangle, highlight: true },
    { name: 'Threat Intel', path: '/threat-intel', icon: GlobeLock },
    { name: 'Reports', path: '/reports', icon: FileWarning },
    { name: 'Analytics', path: '/analytics', icon: LineChart },
  ];

  return (
    <aside className="w-64 border-r border-white/10 flex flex-col bg-background h-screen sticky top-0 hidden md:flex z-40">
      <div className="p-6 flex items-center gap-3 border-b border-white/5">
        <Shield className="w-8 h-8 text-primary" />
        <div>
          <span className="text-xl font-bold tracking-tight block">ThreatLens</span>
          <span className="text-[10px] text-gray-500 uppercase tracking-widest">Autonomous SOC</span>
        </div>
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4 px-2">Investigations</div>
        
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          const Icon = item.icon;
          
          return (
            <Link 
              key={item.name}
              to={item.path} 
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition text-sm font-medium ${
                isActive 
                  ? item.highlight 
                    ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' 
                    : 'bg-primary/20 text-primary border border-primary/20' 
                  : item.highlight
                    ? 'text-orange-400/70 hover:bg-white/5'
                    : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-white/5">
        <Link to="/settings" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 text-gray-400 transition text-sm font-medium">
          <Settings className="w-4 h-4" />
          Settings
        </Link>
        <div className="mt-4 px-3 text-xs text-gray-600">
          Agent Platform v2.0
        </div>
      </div>
    </aside>
  );
};
