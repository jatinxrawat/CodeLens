import React, { useState, useEffect } from 'react';
import {
  GitBranch,
  FolderPlus,
  RefreshCw,
  AlertCircle,
  Database,
  ArrowRight,
  GitCompare,
} from 'lucide-react';
import { RepositorySummary, RepositoryStatus } from '../types';
import {
  fetchRepositoryStatus,
  ingestRemoteRepository,
  ingestLocalRepository,
} from '../services/api';

interface RepositoriesPageProps {
  repositories: RepositorySummary[];
  selectedRepo: string;
  onSelectRepo: (repo: string) => void;
  onRefreshRepositories: () => void;
  onNavigateToTab?: (tab: string) => void;
}

export const RepositoriesPage: React.FC<RepositoriesPageProps> = ({
  repositories,
  selectedRepo,
  onSelectRepo,
  onRefreshRepositories,
  onNavigateToTab,
}) => {
  const [gitUrl, setGitUrl] = useState('');
  const [localPath, setLocalPath] = useState('');
  const [forceReclone, setForceReclone] = useState(false);
  const [, setActiveJobId] = useState<string | null>(null);
  const [activeRepoName, setActiveRepoName] = useState<string | null>(null);
  const [statusState, setStatusState] = useState<RepositoryStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Poll active ingestion status
  useEffect(() => {
    if (!activeRepoName) return;

    const interval = setInterval(async () => {
      try {
        const s = await fetchRepositoryStatus(activeRepoName);
        setStatusState(s);
        if (s.status === 'ready' || s.status === 'failed') {
          clearInterval(interval);
          onRefreshRepositories();
          if (s.status === 'ready') {
            onSelectRepo(s.repository_name);
          }
        }
      } catch (err) {
        console.error('Polling error', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeRepoName]);

  const handleRemoteIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gitUrl.trim()) return;
    setError(null);
    setSubmitting(true);
    try {
      const resp = await ingestRemoteRepository(gitUrl.trim(), forceReclone);
      setActiveJobId(resp.job_id);
      setActiveRepoName(resp.repository_name);
      setGitUrl('');
    } catch (err: any) {
      setError(err.message || 'Failed to start remote ingestion');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLocalIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!localPath.trim()) return;
    setError(null);
    setSubmitting(true);
    try {
      const resp = await ingestLocalRepository(localPath.trim());
      setActiveJobId(resp.job_id);
      setActiveRepoName(resp.repository_name);
      setLocalPath('');
    } catch (err: any) {
      setError(err.message || 'Failed to start local ingestion');
    } finally {
      setSubmitting(false);
    }
  };

  const steps = ['cloning', 'discovering', 'parsing', 'embedding', 'indexing', 'ready'];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-8">
      {/* Top Header */}
      <div>
        <h1 className="text-lg font-semibold text-white">Repository Connection & Ingestion</h1>
        <p className="text-xs text-zinc-400 mt-0.5">
          Ingest public GitHub repositories or local directory paths with 100% local AST parsing and FAISS indexing.
        </p>
      </div>

      {onNavigateToTab && repositories.length >= 2 && (
        <div className="bg-[#08080a] border border-[#18181b] hover:border-zinc-700 rounded-2xl p-4 flex items-center justify-between transition-all shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-xl bg-zinc-900 border border-zinc-700 text-white flex items-center justify-center">
              <GitCompare className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-white">Repository Comparison Studio</h4>
              <p className="text-[11px] text-zinc-400">
                Compare architectural layers, code metrics, and AST structures across indexed codebases.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigateToTab('comparison')}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white text-xs rounded-xl font-medium cursor-pointer border border-zinc-700 transition-colors shadow-sm"
          >
            <span>Open Comparison</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-rose-400 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active Ingestion Job Progress Tracker */}
      {statusState && statusState.status === 'ingesting' && (
        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-5 shadow-2xl space-y-4 animate-in fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-5 h-5 text-white animate-spin" />
              <div>
                <h3 className="text-sm font-semibold text-white font-mono">
                  Ingesting: {statusState.repository_name}
                </h3>
                <p className="text-xs text-zinc-400">
                  Current stage: <strong className="text-white uppercase">{statusState.current_step}</strong>
                </p>
              </div>
            </div>
            <span className="text-xs font-mono text-zinc-400 bg-[#000000] px-2.5 py-1 rounded-full border border-[#18181b]">
              {statusState.ingestion_duration_sec}s elapsed
            </span>
          </div>

          {/* Step Breadcrumb Indicators */}
          <div className="grid grid-cols-6 gap-2 pt-2">
            {steps.map((step, idx) => {
              const currentStepIdx = steps.indexOf(statusState.current_step || 'cloning');
              const isDone = idx < currentStepIdx;
              const isCurrent = idx === currentStepIdx;
              return (
                <div
                  key={step}
                  className={`p-2 rounded-xl border text-center text-[10px] font-mono capitalize transition-all ${
                    isDone
                      ? 'bg-zinc-900 border-zinc-700 text-zinc-200'
                      : isCurrent
                      ? 'bg-white text-black font-bold'
                      : 'bg-[#000000] border-[#18181b] text-zinc-600'
                  }`}
                >
                  {step}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Ingestion Forms Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Remote GitHub Ingestion Form */}
        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-sm font-semibold text-white">
            <GitBranch className="w-4 h-4 text-zinc-300" />
            <span>Connect GitHub Repository</span>
          </div>
          <p className="text-xs text-zinc-400">
            Performs a shallow clone (`--depth 1`), scans multi-language files, and extracts AST chunks.
          </p>

          <form onSubmit={handleRemoteIngest} className="space-y-3">
            <div>
              <label className="text-[11px] font-mono text-zinc-400 block mb-1">GitHub / Git URL</label>
              <input
                type="text"
                value={gitUrl}
                onChange={(e) => setGitUrl(e.target.value)}
                placeholder="https://github.com/pallets/click.git"
                className="w-full bg-[#000000] border border-[#1c1c21] rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition-colors"
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="flex items-center space-x-1.5 text-xs text-zinc-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={forceReclone}
                  onChange={(e) => setForceReclone(e.target.checked)}
                  className="rounded bg-[#000000] border-[#1c1c21] accent-white"
                />
                <span>Force re-clone if directory exists</span>
              </label>
            </div>
            <button
              type="submit"
              disabled={submitting || !gitUrl.trim()}
              className="w-full py-2 bg-white hover:bg-zinc-200 disabled:opacity-50 text-black rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center justify-center space-x-2 shadow-sm"
            >
              <span>Start Ingestion</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>

        {/* Local Directory Ingestion Form */}
        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-sm font-semibold text-white">
            <FolderPlus className="w-4 h-4 text-zinc-300" />
            <span>Index Local Directory</span>
          </div>
          <p className="text-xs text-zinc-400">
            Indexes an existing local codebase directory directly from the file system.
          </p>

          <form onSubmit={handleLocalIngest} className="space-y-3">
            <div>
              <label className="text-[11px] font-mono text-zinc-400 block mb-1">Local Directory Path</label>
              <input
                type="text"
                value={localPath}
                onChange={(e) => setLocalPath(e.target.value)}
                placeholder="tests/fixtures/sample_repo"
                className="w-full bg-[#000000] border border-[#1c1c21] rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition-colors"
              />
            </div>
            <div className="text-[11px] text-zinc-500 pt-1">
              Prunes `.git`, `node_modules`, `.venv`, binaries automatically.
            </div>
            <button
              type="submit"
              disabled={submitting || !localPath.trim()}
              className="w-full py-2 bg-white hover:bg-zinc-200 disabled:opacity-50 text-black rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center justify-center space-x-2 shadow-sm"
            >
              <span>Index Local Codebase</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>

      {/* Persisted Repositories List */}
      <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-zinc-300" />
            <h3 className="text-sm font-semibold text-white">Available Persisted Indexes ({repositories.length})</h3>
          </div>
          <button
            onClick={onRefreshRepositories}
            className="text-xs text-zinc-400 hover:text-white flex items-center space-x-1 cursor-pointer"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {repositories.map((repo) => {
            const isSelected = selectedRepo === repo.repository_id;
            return (
              <div
                key={repo.repository_id}
                className={`p-4 rounded-xl border transition-all ${
                  isSelected
                    ? 'bg-zinc-900 border-zinc-600'
                    : 'bg-[#000000] border-[#1c1c21] hover:border-zinc-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-sm font-bold text-white">{repo.repository_name}</span>
                    {isSelected && (
                      <span className="text-[10px] bg-white text-black font-semibold px-2 py-0.5 rounded-full font-mono">
                        Active
                      </span>
                    )}
                  </div>
                  {!isSelected && (
                    <button
                      onClick={() => onSelectRepo(repo.repository_id)}
                      className="px-2.5 py-1 bg-white hover:bg-zinc-200 text-xs font-mono text-black font-semibold rounded-lg transition-colors cursor-pointer"
                    >
                      Select
                    </button>
                  )}
                </div>

                <div className="text-xs text-zinc-400 font-mono truncate mb-2">{repo.source}</div>

                <div className="flex items-center space-x-4 text-xs font-mono text-zinc-500 pt-2 border-t border-[#18181b]">
                  <span>Files: <strong className="text-white">{repo.total_files}</strong></span>
                  <span>Chunks: <strong className="text-white">{repo.total_chunks}</strong></span>
                  <span>Langs: <strong className="text-white">{Object.keys(repo.languages).length}</strong></span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
