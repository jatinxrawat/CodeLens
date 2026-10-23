import React, { useState, useEffect } from 'react';
import {
  FileCode,
  Layers,
  Cpu,
  Clock,
  Search,
  Sparkles,
  ArrowRight,
  FolderGit2,
  Code2,
} from 'lucide-react';
import { RepositoryStats } from '../types';
import { fetchRepositoryStats } from '../services/api';

interface DashboardPageProps {
  selectedRepo: string;
  onNavigateToSearch: (query?: string) => void;
  onNavigateToRepositories: () => void;
  onNavigateToExplorer: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  selectedRepo,
  onNavigateToSearch,
  onNavigateToRepositories,
  onNavigateToExplorer,
}) => {
  const [stats, setStats] = useState<RepositoryStats | null>(null);
  const [, setLoading] = useState(false);
  const [quickQuery, setQuickQuery] = useState('');

  useEffect(() => {
    if (!selectedRepo) return;
    setLoading(true);
    fetchRepositoryStats(selectedRepo)
      .then(setStats)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedRepo]);

  const recentSearches = [
    'Where is user login and password authentication handled?',
    'How are credit card payments and refunds processed?',
    'Where is LRU cache key eviction implemented?',
    'Where is memory pool allocation buffer?',
  ];

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickQuery.trim()) {
      onNavigateToSearch(quickQuery.trim());
    }
  };

  if (!selectedRepo) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center py-20">
        <FolderGit2 className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-white">No Repository Selected</h2>
        <p className="text-sm text-zinc-400 mt-1 max-w-md mx-auto">
          Please connect a GitHub repository or select an existing local codebase index to view intelligence stats.
        </p>
        <button
          onClick={onNavigateToRepositories}
          className="mt-6 px-4 py-2 bg-white hover:bg-zinc-200 text-black rounded-xl text-xs font-semibold shadow-sm transition-all inline-flex items-center space-x-2 cursor-pointer"
        >
          <span>Connect Repository</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Search Hero Section */}
      <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-lg font-semibold text-white">Code Intelligence Engine</h1>
            <p className="text-xs text-zinc-400 mt-0.5 font-mono">
              Target Codebase: <span className="text-white font-semibold">{selectedRepo}</span>
            </p>
          </div>
          <span className="text-xs font-mono bg-[#000000] border border-[#1c1c21] px-2.5 py-1 rounded-full text-zinc-300">
            Hybrid BM25 + Dense FAISS Active
          </span>
        </div>

        <form onSubmit={handleSearchSubmit} className="relative">
          <Search className="w-4 h-4 text-zinc-500 absolute left-3.5 top-3.5" />
          <input
            type="text"
            value={quickQuery}
            onChange={(e) => setQuickQuery(e.target.value)}
            placeholder="Search functions, classes, architectural intent, or symbols (e.g. 'auth token verification')..."
            className="w-full bg-[#000000] border border-[#1c1c21] rounded-xl pl-10 pr-24 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 font-mono shadow-inner transition-colors"
          />
          <button
            type="submit"
            className="absolute right-2 top-2 px-3.5 py-1 bg-white hover:bg-zinc-200 text-black rounded-lg text-xs font-semibold transition-all cursor-pointer shadow-sm"
          >
            Search
          </button>
        </form>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-4">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-xs font-medium">Source Files</span>
            <FileCode className="w-4 h-4 text-zinc-300" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {stats ? stats.total_files.toLocaleString() : '...'}
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Filtered and AST parsed</p>
        </div>

        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-4">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-xs font-medium">AST Code Chunks</span>
            <Layers className="w-4 h-4 text-zinc-300" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {stats ? stats.total_chunks.toLocaleString() : '...'}
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Functions, classes & methods</p>
        </div>

        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-4">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-xs font-medium">Embedding Dims</span>
            <Cpu className="w-4 h-4 text-zinc-300" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {stats ? `${stats.embedding_dimension}d` : '...'}
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">all-MiniLM-L6-v2 (Local)</p>
        </div>

        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-4">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-xs font-medium">Search Latency</span>
            <Clock className="w-4 h-4 text-zinc-300" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {stats?.avg_search_latency_ms ? `${stats.avg_search_latency_ms} ms` : '< 25 ms'}
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Sub-second local retrieval</p>
        </div>
      </div>

      {/* Secondary Detailed Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Languages & AST Distribution */}
        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-5">
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-4 flex items-center space-x-2">
            <Code2 className="w-4 h-4 text-zinc-300" />
            <span>Language & AST Breakdown</span>
          </h3>

          <div className="space-y-3">
            {stats?.languages &&
              Object.entries(stats.languages).map(([lang, count]) => {
                const pct = Math.round((count / (stats.total_chunks || 1)) * 100);
                return (
                  <div key={lang}>
                    <div className="flex justify-between text-xs font-mono text-white mb-1">
                      <span className="capitalize">{lang}</span>
                      <span className="text-zinc-500">{count} chunks ({pct}%)</span>
                    </div>
                    <div className="w-full bg-[#000000] rounded-full h-1.5 overflow-hidden border border-[#18181b]">
                      <div
                        className="bg-white h-1.5 rounded-full"
                        style={{ width: `${Math.max(5, pct)}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
          </div>

          <div className="mt-6 pt-4 border-t border-[#18181b] flex flex-wrap gap-2">
            {stats?.chunk_types &&
              Object.entries(stats.chunk_types).map(([type, count]) => (
                <span
                  key={type}
                  className="text-[11px] font-mono px-2 py-0.5 rounded-lg bg-[#000000] border border-[#1c1c21] text-zinc-400"
                >
                  {type}: <strong className="text-white">{count}</strong>
                </span>
              ))}
          </div>
        </div>

        {/* Quick Example Searches */}
        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-zinc-300" />
              <span>Suggested Semantic Queries</span>
            </h3>
            <p className="text-xs text-zinc-500 mb-4">
              Click any query below to evaluate hybrid semantic retrieval against this codebase:
            </p>

            <div className="space-y-2">
              {recentSearches.map((query, idx) => (
                <button
                  key={idx}
                  onClick={() => onNavigateToSearch(query)}
                  className="w-full text-left px-3.5 py-2.5 rounded-xl bg-[#000000] hover:bg-zinc-900 border border-[#1c1c21] hover:border-zinc-700 text-xs font-mono text-zinc-300 hover:text-white transition-all flex items-center justify-between group cursor-pointer"
                >
                  <span className="truncate pr-2">"{query}"</span>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-white shrink-0" />
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-[#18181b] flex justify-between items-center text-xs">
            <span className="text-zinc-500">Want to explore file structure?</span>
            <button
              onClick={onNavigateToExplorer}
              className="text-zinc-300 hover:text-white hover:underline font-medium flex items-center space-x-1 cursor-pointer"
            >
              <span>Open Code Explorer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
