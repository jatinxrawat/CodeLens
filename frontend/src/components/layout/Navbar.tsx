import React from 'react';
import { Search, ShieldCheck, Sparkles } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  selectedRepo: string;
  onQuickSearch: () => void;
  onSelectTab?: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, selectedRepo, onQuickSearch, onSelectTab }) => {
  const titles: Record<string, string> = {
    chat: 'CodeLens AI Search & Reasoning',
    dashboard: 'Repository Overview',
    health: 'Codebase Health & Security Audit',
    architecture: 'Architecture & Dependency Graph',
    explorer: 'Code Explorer & Flow Tracer',
    impact: 'Potential Impact & Blast Radius Analysis',
    reports: 'Repository Analysis Reports',
    comparison: 'Repository Comparison Studio',
    repositories: 'Repository Ingestion & Storage',
    landing: 'Public Landing Page & Showcase',
    // Legacy / Aliases:
    search: 'CodeLens AI Search & Reasoning',
    ask: 'CodeLens AI Search & Reasoning',
    quality: 'Codebase Health & Security Audit',
    security: 'Codebase Health & Security Audit',
    graph: 'Architecture & Dependency Graph',
    flow: 'Code Explorer & Flow Tracer',
  };

  return (
    <header className="h-14 bg-[#050505]/90 backdrop-blur border-b border-[#18181b] px-6 flex items-center justify-between sticky top-0 z-10 select-none">
      <div className="flex items-center space-x-3">
        <h2 className="text-sm font-semibold text-[#f4f4f5]">
          {titles[currentTab] || currentTab}
        </h2>
        {selectedRepo && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-[#0d0d10] border border-[#18181b] text-[#9ca3af]">
            repo: <strong className="text-[#f4f4f5] ml-1">{selectedRepo}</strong>
          </span>
        )}
      </div>

      <div className="flex items-center space-x-3">
        {currentTab !== 'search' && (
          <button
            onClick={onQuickSearch}
            className="flex items-center space-x-2 bg-[#0d0d10] hover:bg-[#141418] border border-[#18181b] text-[#9ca3af] hover:text-[#f4f4f5] px-3 py-1.5 rounded-md text-xs transition-colors"
          >
            <Search className="w-3.5 h-3.5" />
            <span>Search codebase...</span>
            <kbd className="text-[10px] bg-[#050505] border border-[#18181b] px-1.5 py-0.5 rounded font-mono text-[#9ca3af]">
              /
            </kbd>
          </button>
        )}

        <button
          onClick={() => onSelectTab ? onSelectTab('landing') : (window.location.href = '/?tab=landing')}
          className="flex items-center space-x-1.5 text-xs text-sky-400 bg-sky-950/30 hover:bg-sky-900/50 border border-sky-800/40 px-2.5 py-1 rounded-md transition-colors"
          title="Open Landing Page"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Landing Page</span>
        </button>

        <div className="flex items-center space-x-1.5 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-2.5 py-1 rounded-md">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="font-mono text-[11px]">Zero Cloud API</span>
        </div>
      </div>
    </header>
  );
};
