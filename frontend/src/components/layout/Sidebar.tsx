import React from 'react';
import {
  LayoutDashboard,
  Layers,
  AlertOctagon,
  Activity,
  FolderTree,
  FileText,
  GitCompare,
  GitBranch,
  ChevronDown,
  Sparkles,
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
        { id: 'chat', label: 'CodeLens AI', icon: Sparkles, aliases: ['search', 'ask'] },
        { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
      ],
    },
    {
      title: 'Code Analysis & Navigation',
      items: [
        { id: 'architecture', label: 'Architecture', icon: Layers, aliases: ['graph'] },
        { id: 'explorer', label: 'Code Explorer', icon: FolderTree, aliases: ['flow'] },
        { id: 'health', label: 'Codebase Health', icon: Activity, aliases: ['quality', 'security'] },
        { id: 'impact', label: 'Impact Analysis', icon: AlertOctagon },
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
    {
      title: 'Showcase & Docs',
      items: [
        { id: 'landing', label: 'Landing Page Tour', icon: Sparkles },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-[#050505] border-r border-[#18181b] flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#18181b] flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center text-white font-bold shadow-sm">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-semibold text-[#f4f4f5] tracking-tight">Code Intelligence</h1>
          <p className="text-[10px] text-[#9ca3af] font-mono">v0.4.0 • Local AI Engine</p>
        </div>
      </div>

      {/* Active Repository Selector */}
      <div className="p-3 border-b border-[#18181b]">
        <label className="text-[10px] font-medium text-[#9ca3af] uppercase tracking-wider block mb-1 px-1">
          Active Repository
        </label>
        <div className="relative">
          <select
            value={selectedRepo}
            onChange={(e) => setSelectedRepo(e.target.value)}
            className="w-full bg-[#0a0a0c] border border-[#18181b] text-[#f4f4f5] text-xs rounded-md px-2.5 py-1.5 appearance-none focus:outline-none focus:border-sky-500 font-mono pr-8 cursor-pointer"
          >
            {repositories.length === 0 && <option value="">No repositories indexed</option>}
            {repositories.map((repo) => (
              <option key={repo.repository_id} value={repo.repository_id}>
                {repo.repository_name} ({repo.total_chunks} chunks)
              </option>
            ))}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-[#9ca3af] absolute right-2.5 top-2.5 pointer-events-none" />
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 p-2 space-y-4 overflow-y-auto">
        {navSections.map((sec) => (
          <div key={sec.title} className="space-y-0.5">
            <div className="text-[10px] font-semibold text-[#9ca3af]/70 uppercase tracking-wider px-2 py-1">
              {sec.title}
            </div>
            {sec.items.map((item) => {
              const Icon = item.icon;
              const isActive =
                currentTab === item.id || (item.aliases && item.aliases.includes(currentTab));
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`w-full flex items-center space-x-2.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                    isActive
                      ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                      : 'text-[#9ca3af] hover:text-[#f4f4f5] hover:bg-[#121215]'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-sky-400' : 'text-[#9ca3af]'}`} />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </nav>
    </aside>
  );
};
