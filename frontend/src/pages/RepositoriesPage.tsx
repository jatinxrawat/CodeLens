import React, { useState, useEffect } from 'react';
import {
  GitBranch,
  FolderPlus,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Database,
  ArrowRight,
  GitCompare,
} from 'lucide-react';
import { RepositorySummary, RepositoryStatus } from '../types';
import {
  fetchRepositories,
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
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
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
        <h1 className="text-lg font-semibold text-[#e6edf3]">Repository Connection & Ingestion</h1>
        <p className="text-xs text-[#8b949e] mt-0.5">
          Ingest public GitHub repositories or local directory paths with 100% local AST parsing and FAISS indexing.
        </p>
      </div>

      {onNavigateToTab && repositories.length >= 2 && (
        <div className="bg-[#161b22] border border-[#30363d] hover:border-[#58a6ff]/50 rounded-xl p-4 flex items-center justify-between transition-colors shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center">
              <GitCompare className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-white">Repository Comparison Studio</h4>
              <p className="text-[11px] text-[#8b949e]">
                Compare architectural layers, code metrics, and AST structures across indexed codebases.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigateToTab('comparison')}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] text-white text-xs rounded-lg font-medium cursor-pointer border border-[#30363d] transition-colors"
          >
            <span>Open Comparison</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active Ingestion Job Progress Tracker */}
      {statusState && statusState.status === 'ingesting' && (
        <div className="bg-[#161b22] border border-[#1f6feb]/50 rounded-xl p-5 shadow-lg space-y-4 animate-in fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-5 h-5 text-[#58a6ff] animate-spin" />
              <div>
                <h3 className="text-sm font-semibold text-[#e6edf3] font-mono">
                  Ingesting: {statusState.repository_name}
                </h3>
                <p className="text-xs text-[#8b949e]">
                  Current stage: <strong className="text-[#58a6ff] uppercase">{statusState.current_step}</strong>
                </p>
              </div>
            </div>
            <span className="text-xs font-mono text-[#8b949e] bg-[#0d1117] px-2.5 py-1 rounded border border-[#30363d]">
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
                  className={`p-2 rounded border text-center text-[10px] font-mono capitalize transition-all ${
                    isDone
                      ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-400'
                      : isCurrent
                      ? 'bg-[#1f6feb]/20 border-[#58a6ff] text-[#58a6ff] font-bold ring-1 ring-[#58a6ff]'
                      : 'bg-[#0d1117] border-[#30363d] text-[#8b949e] opacity-60'
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
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-sm font-semibold text-[#e6edf3]">
            <GitBranch className="w-4 h-4 text-[#58a6ff]" />
            <span>Connect GitHub Repository</span>
          </div>
          <p className="text-xs text-[#8b949e]">
            Performs a shallow clone (`--depth 1`), scans multi-language files, and extracts AST chunks.
          </p>

          <form onSubmit={handleRemoteIngest} className="space-y-3">
            <div>
              <label className="text-[11px] font-mono text-[#8b949e] block mb-1">GitHub / Git URL</label>
              <input
                type="text"
                value={gitUrl}
                onChange={(e) => setGitUrl(e.target.value)}
                placeholder="https://github.com/pallets/click.git"
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-xs font-mono text-[#e6edf3] placeholder-[#8b949e] focus:outline-none focus:border-[#58a6ff]"
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="flex items-center space-x-1.5 text-xs text-[#8b949e] cursor-pointer">
                <input
                  type="checkbox"
                  checked={forceReclone}
                  onChange={(e) => setForceReclone(e.target.checked)}
                  className="rounded bg-[#0d1117] border-[#30363d] accent-[#1f6feb]"
                />
                <span>Force re-clone if directory exists</span>
              </label>
            </div>
            <button
              type="submit"
              disabled={submitting || !gitUrl.trim()}
              className="w-full py-2 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white rounded-md text-xs font-semibold transition-colors flex items-center justify-center space-x-2"
            >
              <span>Start Ingestion</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>

        {/* Local Directory Ingestion Form */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-sm font-semibold text-[#e6edf3]">
            <FolderPlus className="w-4 h-4 text-emerald-400" />
            <span>Index Local Directory</span>
          </div>
          <p className="text-xs text-[#8b949e]">
            Indexes an existing local codebase directory directly from the file system.
          </p>

          <form onSubmit={handleLocalIngest} className="space-y-3">
            <div>
              <label className="text-[11px] font-mono text-[#8b949e] block mb-1">Local Directory Path</label>
              <input
                type="text"
                value={localPath}
                onChange={(e) => setLocalPath(e.target.value)}
                placeholder="tests/fixtures/sample_repo"
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-xs font-mono text-[#e6edf3] placeholder-[#8b949e] focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="text-[11px] text-[#8b949e] pt-1">
              Prunes `.git`, `node_modules`, `.venv`, binaries automatically.
            </div>
            <button
              type="submit"
              disabled={submitting || !localPath.trim()}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-md text-xs font-semibold transition-colors flex items-center justify-center space-x-2"
            >
              <span>Index Local Codebase</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>

      {/* Persisted Repositories List */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-[#58a6ff]" />
            <h3 className="text-sm font-semibold text-[#e6edf3]">Available Persisted Indexes ({repositories.length})</h3>
          </div>
          <button
            onClick={onRefreshRepositories}
            className="text-xs text-[#8b949e] hover:text-[#e6edf3] flex items-center space-x-1"
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
                className={`p-4 rounded-lg border transition-all ${
                  isSelected
                    ? 'bg-[#1f6feb]/10 border-[#58a6ff]'
                    : 'bg-[#0d1117] border-[#30363d] hover:border-[#484f58]'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-sm font-bold text-[#e6edf3]">{repo.repository_name}</span>
                    {isSelected && (
                      <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-1.5 py-0.2 rounded font-mono">
                        Active
                      </span>
                    )}
                  </div>
                  {!isSelected && (
                    <button
                      onClick={() => onSelectRepo(repo.repository_id)}
                      className="px-2 py-1 bg-[#21262d] hover:bg-[#30363d] text-xs font-mono text-[#58a6ff] rounded transition-colors"
                    >
                      Select
                    </button>
                  )}
                </div>

                <div className="text-xs text-[#8b949e] font-mono truncate mb-2">{repo.source}</div>

                <div className="flex items-center space-x-4 text-xs font-mono text-[#8b949e] pt-2 border-t border-[#30363d]/60">
                  <span>Files: <strong className="text-[#e6edf3]">{repo.total_files}</strong></span>
                  <span>Chunks: <strong className="text-[#e6edf3]">{repo.total_chunks}</strong></span>
                  <span>Langs: <strong className="text-[#e6edf3]">{Object.keys(repo.languages).length}</strong></span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
