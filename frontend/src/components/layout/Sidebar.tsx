import React from 'react';
import {
  LayoutDashboard,
  Search,
  MessageSquareCode,
  Layers,
  AlertOctagon,
  Workflow,
  Gauge,
  ShieldAlert,
  FolderTree,
  Network,
  FileText,
  GitCompare,
  GitBranch,
  BarChart3,
  Brain,
  ChevronDown,
} from 'lucide-react';
import type { RepositorySummary } from '../../types';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  repositories: RepositorySummary[];
  selectedRepo: string;
  setSelectedRepo: (repo: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  repositories,
  selectedRepo,
  setSelectedRepo,
}) => {
  const navSections = [
    {
      title: 'Intelligence & Search',
      items: [
        { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
        { id: 'search', label: 'Hybrid Search', icon: Search },
        { id: 'ask', label: 'Ask Codebase (RAG)', icon: MessageSquareCode },
      ],
    },
    {
      title: 'Code Analysis',
      items: [
        { id: 'architecture', label: 'Architecture Layers', icon: Layers },
        { id: 'impact', label: 'Impact Analysis', icon: AlertOctagon },
        { id: 'flow', label: 'Code Flow Tracer', icon: Workflow },
        { id: 'quality', label: 'Quality & Smells', icon: Gauge },
        { id: 'security', label: 'Security Insights', icon: ShieldAlert },
      ],
    },
    {
      title: 'Navigation & Graph',
      items: [
        { id: 'explorer', label: 'Code Explorer', icon: FolderTree },
        { id: 'graph', label: 'Dependency Graph', icon: Network },
      ],
    },
    {
      title: 'Machine Learning',
      items: [
        { id: 'mlstudio', label: 'ML Training Studio', icon: Brain },
        { id: 'evaluation', label: 'IR Benchmark', icon: BarChart3 },
      ],
    },
    {
      title: 'Analytics & Management',
      items: [
        { id: 'reports', label: 'Analysis Reports', icon: FileText },
        { id: 'comparison', label: 'Repo Comparison', icon: GitCompare },
        { id: 'repositories', label: 'Repositories', icon: GitBranch },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-[#0d1117] border-r border-[#30363d] flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#30363d] flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center text-white font-bold shadow-sm">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-semibold text-[#e6edf3] tracking-tight">Code Intelligence</h1>
          <p className="text-[10px] text-[#8b949e] font-mono">v0.4.0 • Local AI Engine</p>
        </div>
      </div>

      {/* Active Repository Selector */}
      <div className="p-3 border-b border-[#30363d]">
        <label className="text-[10px] font-medium text-[#8b949e] uppercase tracking-wider block mb-1 px-1">
          Active Repository
        </label>
        <div className="relative">
          <select
            value={selectedRepo}
            onChange={(e) => setSelectedRepo(e.target.value)}
            className="w-full bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-xs rounded-md px-2.5 py-1.5 appearance-none focus:outline-none focus:border-[#58a6ff] font-mono pr-8 cursor-pointer"
          >
            {repositories.length === 0 && <option value="">No repositories indexed</option>}
            {repositories.map((repo) => (
              <option key={repo.repository_id} value={repo.repository_id}>
                {repo.repository_name} ({repo.total_chunks} chunks)
              </option>
            ))}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-[#8b949e] absolute right-2.5 top-2.5 pointer-events-none" />
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 p-2 space-y-4 overflow-y-auto">
        {navSections.map((sec) => (
          <div key={sec.title} className="space-y-0.5">
            <div className="text-[10px] font-semibold text-[#8b949e]/70 uppercase tracking-wider px-2 py-1">
              {sec.title}
            </div>
            {sec.items.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`w-full flex items-center space-x-2.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-[#1f6feb]/15 text-[#58a6ff] border border-[#1f6feb]/30'
                      : 'text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#161b22]'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#58a6ff]' : 'text-[#8b949e]'}`} />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer Info */}
      <div className="p-3 border-t border-[#30363d] text-[10px] text-[#8b949e] flex items-center justify-between">
        <span className="flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>100% Local ML Engine</span>
        </span>
        <span className="font-mono text-[9px] bg-[#161b22] px-1.5 py-0.5 rounded border border-[#30363d]">
          MPS/CPU
        </span>
      </div>
    </aside>
  );
};
