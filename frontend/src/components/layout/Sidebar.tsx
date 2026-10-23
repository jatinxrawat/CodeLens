import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  LayoutDashboard,
  Layers,
  AlertOctagon,
  FolderTree,
  Activity,
  Compass,
  GitPullRequest,
  FileText,
  GitBranch,
  ChevronDown,
  Sparkles,
  Cpu,
  RefreshCw,
  Settings,
} from 'lucide-react';
import type { RepositorySummary, LLMProviderStatus } from '../../types';
import { fetchProviderStatus, setLLMProvider } from '../../services/api';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  repositories: RepositorySummary[];
  selectedRepo: string;
  setSelectedRepo: (repo: string) => void;
  activeProvider?: 'gemini' | 'local';
  onProviderChange?: (provider: 'gemini' | 'local') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  repositories,
  selectedRepo,
  setSelectedRepo,
  activeProvider = 'gemini',
  onProviderChange,
}) => {
  const [providerStatus, setProviderStatus] = useState<LLMProviderStatus | null>(null);
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [switchingProvider, setSwitchingProvider] = useState(false);

  const loadProvider = async () => {
    try {
      const status = await fetchProviderStatus();
      setProviderStatus(status);
    } catch {
      // fallback
    }
  };

  useEffect(() => {
    loadProvider();
  }, []);

  const handleSwitchProvider = async (target: 'gemini' | 'local') => {
    try {
      setSwitchingProvider(true);
      await setLLMProvider(target);
      await loadProvider();
      if (onProviderChange) {
        onProviderChange(target);
      }
      setShowProviderModal(false);
    } catch (err: any) {
      alert(err.message || 'Failed to switch provider');
    } finally {
      setSwitchingProvider(false);
    }
  };

  // Exactly 10 sidebar items as requested:
  // Chat, Overview, Architecture, Impact Analysis, Explorer, Health, Explore, Contribute, Reports, Repositories
  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageSquare, aliases: ['search', 'ask'] },
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'architecture', label: 'Architecture', icon: Layers, aliases: ['graph'] },
    { id: 'impact', label: 'Impact Analysis', icon: AlertOctagon },
    { id: 'explorer', label: 'Explorer', icon: FolderTree, aliases: ['flow'] },
    { id: 'health', label: 'Health', icon: Activity, aliases: ['quality', 'security'] },
    { id: 'explore', label: 'Explore', icon: Compass },
    { id: 'contribute', label: 'Contribute', icon: GitPullRequest },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'repositories', label: 'Repositories', icon: GitBranch },
  ];

  const currentProvider = providerStatus?.active_provider || activeProvider || 'gemini';

  return (
    <aside className="w-64 bg-[#050505] border-r border-[#18181b] flex flex-col h-screen select-none shrink-0 font-sans">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#18181b] flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-md">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-[#f4f4f5] tracking-tight">CodeLens</h1>
            <p className="text-[10px] text-[#9ca3af] font-mono">Student Code Intelligence</p>
          </div>
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
            {repositories.length === 0 && <option value="">No repositories attached</option>}
            {repositories.map((repo) => (
              <option key={repo.repository_id} value={repo.repository_id}>
                {repo.repository_name} ({repo.total_chunks} chunks)
              </option>
            ))}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-[#9ca3af] absolute right-2.5 top-2.5 pointer-events-none" />
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            currentTab === item.id || (item.aliases && item.aliases.includes(currentTab));

          return (
            <button
              key={item.id}
              onClick={() => setCurrentTab(item.id)}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-colors cursor-pointer ${
                isActive
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                  : 'text-[#9ca3af] hover:text-[#f4f4f5] hover:bg-[#121215]'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-sky-400' : 'text-[#9ca3af]'}`} />
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Provider Indicator */}
      <div className="p-3 border-t border-[#18181b] bg-[#07070a]">
        <button
          onClick={() => setShowProviderModal(true)}
          className="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-[#0f0f15] hover:bg-[#171722] border border-[#20202c] transition-all cursor-pointer group"
          title="Click to view or switch AI provider settings"
        >
          <div className="flex items-center space-x-2">
            {currentProvider === 'gemini' ? (
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center text-white shrink-0">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
            ) : (
              <div className="w-6 h-6 rounded-lg bg-emerald-950/80 border border-emerald-600/50 flex items-center justify-center text-emerald-400 shrink-0">
                <Cpu className="w-3.5 h-3.5" />
              </div>
            )}
            <div className="text-left">
              <span className="text-[10px] text-[#71717a] uppercase font-mono block">AI Provider</span>
              <span className="text-xs font-semibold text-white">
                {currentProvider === 'gemini' ? 'Gemini (Cloud)' : 'Local (Offline)'}
              </span>
            </div>
          </div>
          <Settings className="w-3.5 h-3.5 text-[#71717a] group-hover:text-white transition-colors" />
        </button>
      </div>

      {/* Provider Settings Modal */}
      {showProviderModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#121218] border border-[#2e2e42] rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4 animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-[#242436] pb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-sky-400" />
                <h3 className="text-base font-bold text-white">Select AI Provider</h3>
              </div>
              <button
                onClick={() => setShowProviderModal(false)}
                className="text-[#71717a] hover:text-white"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[#9ca3af]">
              Choose between cloud-accelerated Google Gemini AI or 100% offline local ML inference.
            </p>

            <div className="space-y-3">
              {/* Gemini Option */}
              <button
                onClick={() => handleSwitchProvider('gemini')}
                disabled={switchingProvider}
                className={`w-full text-left p-4 rounded-2xl border transition-all cursor-pointer ${
                  currentProvider === 'gemini'
                    ? 'bg-sky-950/40 border-sky-500/60 ring-1 ring-sky-500/50'
                    : 'bg-[#181824] hover:bg-[#202030] border-[#2a2a3e]'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-sky-400" />
                    <span className="text-sm font-semibold text-white">Google Gemini (Default)</span>
                  </div>
                  {currentProvider === 'gemini' && (
                    <span className="text-[10px] bg-sky-500 text-white px-2 py-0.5 rounded-full font-mono">
                      Active
                    </span>
                  )}
                </div>
                <p className="text-xs text-[#a1a1aa] leading-relaxed">
                  Fast Flash-tier for instant Q&A and Pro-tier for deep code explain. Official Google GenAI SDK with semantic caching.
                </p>
                <div className="mt-2 text-[10px] font-mono text-sky-300">
                  Models: {providerStatus?.gemini_flash_model || 'gemini-2.5-flash'} • {providerStatus?.gemini_embedding_model || 'text-embedding-004'}
                </div>
              </button>

              {/* Local Option */}
              <button
                onClick={() => handleSwitchProvider('local')}
                disabled={switchingProvider}
                className={`w-full text-left p-4 rounded-2xl border transition-all cursor-pointer ${
                  currentProvider === 'local'
                    ? 'bg-emerald-950/40 border-emerald-500/60 ring-1 ring-emerald-500/50'
                    : 'bg-[#181824] hover:bg-[#202030] border-[#2a2a3e]'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm font-semibold text-white">Local ML (100% Offline)</span>
                  </div>
                  {currentProvider === 'local' && (
                    <span className="text-[10px] bg-emerald-500 text-white px-2 py-0.5 rounded-full font-mono">
                      Active
                    </span>
                  )}
                </div>
                <p className="text-xs text-[#a1a1aa] leading-relaxed">
                  100% offline air-gapped reasoning using local SentenceTransformers & AST rule synthesizers. No external API keys required.
                </p>
                <div className="mt-2 text-[10px] font-mono text-emerald-300">
                  Model: {providerStatus?.local_model || 'Local Reasoner'} • {providerStatus?.local_embedding_model || 'all-MiniLM-L6-v2'}
                </div>
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
