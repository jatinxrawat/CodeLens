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
    <header className="h-14 bg-[#000000]/90 backdrop-blur border-b border-[#18181b] px-6 flex items-center justify-between sticky top-0 z-10 select-none">
      <div className="flex items-center space-x-3">
        <h2 className="text-sm font-semibold text-[#f4f4f5]">
          {titles[currentTab] || currentTab}
        </h2>
        {selectedRepo && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-mono bg-[#09090b] border border-[#1c1c21] text-[#a1a1aa]">
            repo: <strong className="text-[#f4f4f5] ml-1">{selectedRepo}</strong>
          </span>
        )}
      </div>

      <div className="flex items-center space-x-3">
        {currentTab !== 'chat' && currentTab !== 'search' && (
          <button
            onClick={onQuickSearch}
            className="flex items-center space-x-2 bg-[#09090b] hover:bg-[#111114] border border-[#1c1c21] text-[#a1a1aa] hover:text-[#f4f4f5] px-3 py-1.5 rounded-lg text-xs transition-colors cursor-pointer"
          >
            <Search className="w-3.5 h-3.5 text-[#71717a]" />
            <span>Search codebase...</span>
            <kbd className="text-[10px] bg-[#000000] border border-[#1c1c21] px-1.5 py-0.5 rounded font-mono text-[#71717a]">
              /
            </kbd>
          </button>
        )}

        <button
          onClick={() => onSelectTab ? onSelectTab('landing') : (window.location.href = '/?tab=landing')}
          className="flex items-center space-x-1.5 text-xs text-zinc-200 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700/80 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
          title="Open Landing Page"
        >
          <Sparkles className="w-3.5 h-3.5 text-zinc-300" />
          <span>Landing Page</span>
        </button>

        {/* Provider Indicator */}
        <div className="flex items-center space-x-1.5 text-xs text-zinc-300 bg-zinc-950 border border-zinc-800 px-2.5 py-1 rounded-lg">
          {isGemini ? (
            <Sparkles className="w-3.5 h-3.5 text-zinc-400" />
          ) : (
            <Cpu className="w-3.5 h-3.5 text-zinc-400" />
          )}
          <span className="font-mono text-[11px] text-zinc-400">
            AI: <span className="text-zinc-200 font-medium">{isGemini ? 'Gemini' : 'Local'}</span>
          </span>
        </div>
      </div>
    </header>
  );
};
