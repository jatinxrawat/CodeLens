import React, { useState, useEffect } from 'react';
import { Search, ShieldCheck, Sparkles, Cpu, ExternalLink } from 'lucide-react';
import { fetchProviderStatus } from '../../services/api';
import type { LLMProviderStatus } from '../../types';

interface NavbarProps {
  currentTab: string;
  selectedRepo: string;
  onQuickSearch: () => void;
  onSelectTab?: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, selectedRepo, onQuickSearch, onSelectTab }) => {
  const [providerStatus, setProviderStatus] = useState<LLMProviderStatus | null>(null);

  useEffect(() => {
    fetchProviderStatus()
      .then(setProviderStatus)
      .catch(() => {});
  }, [currentTab]);

  const titles: Record<string, string> = {
    chat: 'CodeLens AI Search & Reasoning',
    dashboard: 'Repository Overview',
    architecture: 'Architecture Layers & Dependency Graph',
    impact: 'Potential Impact & Blast Radius Analysis',
    explorer: 'Code Explorer & Function Flow Tracer',
    health: 'Codebase Health & Security Audit',
    explore: 'Explore Top Repositories',
    contribute: 'Open-Source Contribution Hub',
    reports: 'Repository Analysis Reports',
    repositories: 'Repository Ingestion & Storage',
    comparison: 'Repository Comparison Studio',
    admin: 'ML Studio & IR Benchmark (Admin)',
    landing: 'Public Landing Page & Showcase',
    // Aliases
    search: 'CodeLens AI Search & Reasoning',
    ask: 'CodeLens AI Search & Reasoning',
    quality: 'Codebase Health & Security Audit',
    security: 'Codebase Health & Security Audit',
    graph: 'Architecture Layers & Dependency Graph',
    flow: 'Code Explorer & Function Flow Tracer',
  };

  const isGemini = providerStatus?.active_provider === 'gemini';

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
        {currentTab !== 'chat' && currentTab !== 'search' && (
          <button
            onClick={onQuickSearch}
            className="flex items-center space-x-2 bg-[#0d0d10] hover:bg-[#141418] border border-[#18181b] text-[#9ca3af] hover:text-[#f4f4f5] px-3 py-1.5 rounded-md text-xs transition-colors cursor-pointer"
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
          className="flex items-center space-x-1.5 text-xs text-sky-400 bg-sky-950/30 hover:bg-sky-900/50 border border-sky-800/40 px-2.5 py-1 rounded-md transition-colors cursor-pointer"
          title="Open Landing Page"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Landing Page</span>
        </button>

        {/* Provider Indicator */}
        {isGemini ? (
          <div className="flex items-center space-x-1.5 text-xs text-sky-300 bg-sky-950/40 border border-sky-800/50 px-2.5 py-1 rounded-md">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-mono text-[11px]">Provider: Gemini</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-2.5 py-1 rounded-md">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-mono text-[11px]">Provider: Local ML</span>
          </div>
        )}
      </div>
    </header>
  );
};
