import React from 'react';
import { Search, Bell, User } from 'lucide-react';

export const TopNav = () => {
  return (
    <header className="h-14 border-b border-zinc-800/80 bg-zinc-950/90 backdrop-blur-sm flex items-center justify-between px-6 sticky top-0 z-30 select-none">
      
      {/* Global Search */}
      <div className="flex-1 max-w-md">
        <div className="relative group">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2 group-focus-within:text-white transition" />
          <input 
            type="text" 
            placeholder="Search investigations, artifacts, IoCs (Press ⌘K)..." 
            className="w-full bg-zinc-900 border border-zinc-800 rounded-md py-1.5 pl-9 pr-3 text-xs text-zinc-200 focus:outline-none focus:border-zinc-600 transition placeholder:text-zinc-500"
          />
        </div>
      </div>
      
      {/* Right Actions */}
      <div className="flex items-center gap-5">
        
        {/* System Health */}
        <div className="hidden lg:flex items-center gap-4 text-xs font-mono border-r border-zinc-800 pr-5">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span className="text-zinc-400">Engine: <span className="text-zinc-200 font-semibold">Active</span></span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-zinc-500"></span>
            <span className="text-zinc-400">Sandbox: <span className="text-zinc-200">Idle</span></span>
          </div>
        </div>

        {/* User Actions */}
        <div className="flex items-center gap-3">
          <button className="relative text-zinc-400 hover:text-white p-1 rounded transition">
            <Bell className="w-4 h-4" />
            <span className="absolute top-0 right-0 w-1.5 h-1.5 bg-white rounded-full"></span>
          </button>
          
          <div className="flex items-center gap-2 pl-2">
            <div className="w-6 h-6 rounded-md bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300 text-xs font-bold font-mono">
              A
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-xs font-semibold leading-none text-zinc-200">Analyst</div>
            </div>
          </div>
        </div>
        
      </div>
    </header>
  );
};
