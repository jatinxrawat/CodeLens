import React, { useState, useEffect } from 'react';
import {
  AlertOctagon,
  Search,
  ExternalLink,
  ShieldAlert,
  ArrowRight,
  HelpCircle,
  FileCode,
} from 'lucide-react';
import type { ImpactAnalysisResult, ImpactItem, FileItem } from '../types';
import { fetchImpactAnalysis, fetchRepositoryFiles } from '../services/api';

interface ImpactAnalysisPageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
}

export const ImpactAnalysisPage: React.FC<ImpactAnalysisPageProps> = ({
  selectedRepo,
  onOpenFileInExplorer,
}) => {
  const [target, setTarget] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [result, setResult] = useState<ImpactAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedRepo) return;
    fetchRepositoryFiles(selectedRepo)
      .then((fList) => {
        setFiles(fList);
        if (fList.length > 0 && !target) {
          setTarget(fList[0].path);
        }
      })
      .catch((err) => console.error(err));
  }, [selectedRepo]);

  const handleAnalyze = async (tgt: string) => {
    if (!tgt.trim() || !selectedRepo) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchImpactAnalysis(selectedRepo, tgt.trim());
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compute impact analysis');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleAnalyze(target);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[#e6edf3]">Potential Impact & Blast Radius Analysis</h1>
        <p className="text-xs text-[#8b949e] mt-0.5">
          Estimate upstream callers, direct importers, and affected modules before refactoring or modifying a file or symbol.
        </p>
      </div>

      {/* Target Selector Form */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-3">
        <form onSubmit={handleSubmit} className="flex flex-wrap md:flex-nowrap gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="Enter file path (e.g. 'python/auth.py') or function name..."
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-4 py-2.5 text-xs text-[#e6edf3] placeholder-[#8b949e] focus:outline-none focus:border-[#58a6ff] font-mono shadow-inner"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !target.trim() || !selectedRepo}
            className="px-5 py-2.5 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors flex items-center space-x-2 shrink-0 shadow-sm"
          >
            <span>{loading ? 'Analyzing...' : 'Analyze Impact'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Quick File Selectors */}
        {files.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] text-[#8b949e] mr-1">Quick Select:</span>
            {files.slice(0, 5).map((f) => (
              <button
                key={f.path}
                type="button"
                onClick={() => {
                  setTarget(f.path);
                  handleAnalyze(f.path);
                }}
                className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#0d1117] hover:bg-[#21262d] text-[#58a6ff] border border-[#30363d] transition-colors"
              >
                {f.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <div className="text-xs text-[#8b949e] mb-1">Total Blast Radius</div>
              <div className="text-2xl font-bold font-mono text-[#e6edf3]">
                {result.total_affected_files} files
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Potentially affected</p>
            </div>

            <div className="bg-[#161b22] border border-red-900/40 rounded-lg p-4 bg-red-950/10">
              <div className="text-xs text-red-400 mb-1 font-semibold">High Impact</div>
              <div className="text-2xl font-bold font-mono text-red-400">
                {result.high_impact_count}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Direct static imports</p>
            </div>

            <div className="bg-[#161b22] border border-amber-900/40 rounded-lg p-4 bg-amber-950/10">
              <div className="text-xs text-amber-400 mb-1 font-semibold">Medium Impact</div>
              <div className="text-2xl font-bold font-mono text-amber-400">
                {result.medium_impact_count}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Transitive co-dependencies</p>
            </div>

            <div className="bg-[#161b22] border border-blue-900/40 rounded-lg p-4 bg-blue-950/10">
              <div className="text-xs text-blue-400 mb-1 font-semibold">Low Impact</div>
              <div className="text-2xl font-bold font-mono text-blue-400">
                {result.low_impact_count}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Co-located modules</p>
            </div>
          </div>

          {/* Impacted Files List */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[#e6edf3]">
                Ranked Impact List for <span className="text-[#58a6ff] font-mono">"{result.target}"</span>
              </h3>
            </div>

            <div className="divide-y divide-[#30363d]/60">
              {result.impacted_files.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#8b949e]">
                  No direct or transitive dependents detected for this target.
                </div>
              ) : (
                result.impacted_files.map((item: ImpactItem, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 hover:bg-[#21262d]/50 transition-colors flex flex-wrap items-center justify-between gap-3 text-xs font-mono"
                  >
                    <div className="space-y-1 max-w-xl">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.impact_level === 'HIGH'
                              ? 'bg-red-950 text-red-400 border border-red-800'
                              : item.impact_level === 'MEDIUM'
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-blue-950 text-blue-400 border border-blue-800'
                          }`}
                        >
                          {item.impact_level} IMPACT
                        </span>
                        <span className="text-sm font-bold text-[#e6edf3]">{item.file_path}</span>
                      </div>
                      <div className="text-[11px] text-[#8b949e] font-sans">{item.reason}</div>
                      {item.affected_symbols.length > 0 && (
                        <div className="text-[11px] text-emerald-400 font-mono">
                          Affected symbols: {item.affected_symbols.join(', ')}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center space-x-3 shrink-0">
                      <span className="text-[11px] text-[#8b949e]">
                        Conf: {(item.confidence_score * 100).toFixed(0)}%
                      </span>
                      <button
                        onClick={() => onOpenFileInExplorer(item.file_path)}
                        className="px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] rounded text-xs transition-colors flex items-center space-x-1"
                      >
                        <span>View</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="p-3 bg-[#0d1117] border border-[#30363d] rounded-lg text-[11px] text-[#8b949e]">
            {result.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
