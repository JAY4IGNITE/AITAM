import React from 'react';
import { Search, Bell, User } from 'lucide-react';

export const TopNav = () => {
  return (
    <header className="h-16 border-b border-white/10 bg-background/80 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-30">
      
      {/* Global Search */}
      <div className="flex-1 max-w-xl">
        <div className="relative group">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2 group-focus-within:text-primary transition" />
          <input 
            type="text" 
            placeholder="Search investigations, incidents, IoCs..." 
            className="w-full bg-black/40 border border-white/10 rounded-full py-1.5 pl-10 pr-4 text-sm text-gray-200 focus:outline-none focus:border-primary/50 focus:bg-black/60 transition placeholder:text-gray-600"
          />
        </div>
      </div>
      
      {/* Right Actions */}
      <div className="flex items-center gap-6">
        
        {/* System Health */}
        <div className="hidden lg:flex items-center gap-4 text-xs font-mono border-r border-white/10 pr-6">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            <span className="text-gray-400">Agents: <span className="text-gray-200">Online</span></span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            <span className="text-gray-400">Sandbox: <span className="text-gray-200">Idle</span></span>
          </div>
        </div>

        {/* User Actions */}
        <div className="flex items-center gap-4">
          <button className="relative text-gray-400 hover:text-white transition">
            <Bell className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 rounded-full border-2 border-background flex items-center justify-center text-[8px] font-bold text-white">3</span>
          </button>
          
          <div className="flex items-center gap-3 pl-2">
            <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-primary">
              <User className="w-4 h-4" />
            </div>
            <div className="hidden sm:block">
              <div className="text-sm font-semibold leading-none">Analyst</div>
              <div className="text-xs text-gray-500 mt-1">L2 Responder</div>
            </div>
          </div>
        </div>
        
      </div>
    </header>
  );
};
