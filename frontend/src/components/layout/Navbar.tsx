import React from 'react';
import { Search, ShieldCheck } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  selectedRepo: string;
  onQuickSearch: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, selectedRepo, onQuickSearch }) => {
  const titles: Record<string, string> = {
    dashboard: 'Repository Overview',
    search: 'Hybrid & Semantic Retrieval',
    ask: 'Evidence-Grounded Code Reasoning',
    architecture: 'Inferred Architecture & Structural Layers',
    impact: 'Potential Impact & Blast Radius Analysis',
    flow: 'Static Code Flow & Call Graph Tracer',
    quality: 'Code Quality & Smell Detection',
    security: 'Static Security Insights & Risk Patterns',
    explorer: 'Code Explorer & AST Inspector',
    graph: 'Dependency & Import Architecture',
    reports: 'Repository Analysis Reports',
    comparison: 'Repository Comparison Studio',
    repositories: 'Repository Ingestion & Storage',
    evaluation: 'IR Evaluation & Model Comparison',
  };

  return (
    <header className="h-14 bg-[#0d1117]/80 backdrop-blur border-b border-[#30363d] px-6 flex items-center justify-between sticky top-0 z-10 select-none">
      <div className="flex items-center space-x-3">
        <h2 className="text-sm font-semibold text-[#e6edf3]">
          {titles[currentTab] || currentTab}
        </h2>
        {selectedRepo && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-[#161b22] border border-[#30363d] text-[#8b949e]">
            repo: <strong className="text-[#e6edf3] ml-1">{selectedRepo}</strong>
          </span>
        )}
      </div>

      <div className="flex items-center space-x-3">
        {currentTab !== 'search' && (
          <button
            onClick={onQuickSearch}
            className="flex items-center space-x-2 bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-[#8b949e] hover:text-[#e6edf3] px-3 py-1.5 rounded-md text-xs transition-colors"
          >
            <Search className="w-3.5 h-3.5" />
            <span>Search codebase...</span>
            <kbd className="text-[10px] bg-[#0d1117] border border-[#30363d] px-1.5 py-0.5 rounded font-mono text-[#8b949e]">
              /
            </kbd>
          </button>
        )}

        <div className="flex items-center space-x-1.5 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-2.5 py-1 rounded-md">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="font-mono text-[11px]">Zero Cloud API</span>
        </div>
      </div>
    </header>
  );
};
