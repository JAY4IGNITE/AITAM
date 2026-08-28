import React from 'react';
import { Sidebar } from './Sidebar';
import { TopNav } from './TopNav';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell = ({ children }: AppShellProps) => {
  return (
    <div className="min-h-screen bg-background text-foreground flex overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <TopNav />
        <main className="flex-1 overflow-y-auto bg-[#0a0a0b] relative">
          {/* Subtle background glow */}
          <div className="absolute top-0 left-0 w-full h-96 bg-primary/5 blur-[120px] pointer-events-none -z-10 rounded-full transform -translate-y-1/2"></div>
          {children}
        </main>
      </div>
    </div>
  );
};
