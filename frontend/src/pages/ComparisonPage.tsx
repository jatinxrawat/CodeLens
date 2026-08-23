import React, { useState } from 'react';
import {
  GitCompare,
  ArrowRight,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import type { RepositorySummary, RepoComparisonResult } from '../types';
import { compareRepositories } from '../services/api';

interface ComparisonPageProps {
  repositories: RepositorySummary[];
}

export const ComparisonPage: React.FC<ComparisonPageProps> = ({ repositories }) => {
  const [repoA, setRepoA] = useState<string>(repositories[0]?.repository_id || '');
  const [repoB, setRepoB] = useState<string>(repositories[1]?.repository_id || repositories[0]?.repository_id || '');
  const [result, setResult] = useState<RepoComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!repoA || !repoB) return;
    setLoading(true);
    setError(null);
    try {
      const res = await compareRepositories(repoA, repoB);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Comparison failed');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[#e6edf3]">Repository Comparison Studio</h1>
        <p className="text-xs text-[#8b949e] mt-0.5">
          Empirically compare two repositories across architecture, complexity, maintainability, smells, and security findings.
        </p>
      </div>

      {/* Selectors Card */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-mono text-[#8b949e] block mb-1.5">Repository A</label>
            <select
              value={repoA}
              onChange={(e) => setRepoA(e.target.value)}
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-xs font-mono text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]"
            >
              {repositories.map((r) => (
                <option key={r.repository_id} value={r.repository_id}>
                  {r.repository_name} ({r.total_chunks} chunks)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-mono text-[#8b949e] block mb-1.5">Repository B</label>
            <select
              value={repoB}
              onChange={(e) => setRepoB(e.target.value)}
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-xs font-mono text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]"
            >
              {repositories.map((r) => (
                <option key={r.repository_id} value={r.repository_id}>
                  {r.repository_name} ({r.total_chunks} chunks)
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading || !repoA || !repoB}
          className="w-full py-2 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white rounded-md text-xs font-semibold font-mono transition-colors flex items-center justify-center space-x-2 shadow-sm"
        >
          <GitCompare className="w-3.5 h-3.5" />
          <span>{loading ? 'Comparing Codebases...' : 'Run Side-by-Side Comparison'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden shadow-sm">
          <div className="px-5 py-4 border-b border-[#30363d]">
            <h3 className="text-sm font-semibold text-[#e6edf3]">
              Side-by-Side Empirical Metrics: <span className="text-[#58a6ff]">{result.repo_a_id}</span> vs <span className="text-emerald-400">{result.repo_b_id}</span>
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left font-mono">
              <thead className="bg-[#0d1117] text-[#8b949e] uppercase text-[10px] tracking-wider border-b border-[#30363d]">
                <tr>
                  <th className="px-4 py-3">Metric</th>
                  <th className="px-4 py-3 text-[#58a6ff]">{result.repo_a_id}</th>
                  <th className="px-4 py-3 text-emerald-400">{result.repo_b_id}</th>
                  <th className="px-4 py-3">Comparison</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#30363d]/60">
                <tr className="hover:bg-[#21262d]/50">
                  <td className="px-4 py-3 font-semibold text-[#e6edf3]">Source Files</td>
                  <td className="px-4 py-3">{result.repo_a.total_files}</td>
                  <td className="px-4 py-3">{result.repo_b.total_files}</td>
                  <td className="px-4 py-3 text-[#8b949e]">
                    {result.repo_a.total_files > result.repo_b.total_files ? 'Repo A larger' : result.repo_b.total_files > result.repo_a.total_files ? 'Repo B larger' : 'Equal'}
                  </td>
                </tr>
                <tr className="hover:bg-[#21262d]/50">
                  <td className="px-4 py-3 font-semibold text-[#e6edf3]">AST Code Chunks</td>
                  <td className="px-4 py-3">{result.repo_a.total_chunks}</td>
                  <td className="px-4 py-3">{result.repo_b.total_chunks}</td>
                  <td className="px-4 py-3 text-[#8b949e]">
                    {result.repo_a.total_chunks > result.repo_b.total_chunks ? 'Repo A (+ chunks)' : 'Repo B (+ chunks)'}
                  </td>
                </tr>
                <tr className="hover:bg-[#21262d]/50">
                  <td className="px-4 py-3 font-semibold text-[#e6edf3]">Lines of Code (LOC)</td>
                  <td className="px-4 py-3">{result.repo_a.total_loc.toLocaleString()}</td>
                  <td className="px-4 py-3">{result.repo_b.total_loc.toLocaleString()}</td>
                  <td className="px-4 py-3 text-[#8b949e]">
                    Δ {Math.abs(result.repo_a.total_loc - result.repo_b.total_loc)} LOC
                  </td>
                </tr>
                <tr className="hover:bg-[#21262d]/50">
                  <td className="px-4 py-3 font-semibold text-[#e6edf3]">Avg Cyclomatic Complexity</td>
                  <td className="px-4 py-3">{result.repo_a.avg_complexity}</td>
                  <td className="px-4 py-3">{result.repo_b.avg_complexity}</td>
                  <td className="px-4 py-3 text-[#8b949e]">
                    {result.repo_a.avg_complexity < result.repo_b.avg_complexity ? 'Repo A cleaner' : 'Repo B cleaner'}
                  </td>
                </tr>
                <tr className="hover:bg-[#21262d]/50">
                  <td className="px-4 py-3 font-semibold text-[#e6edf3]">Maintainability Rating</td>
                  <td className="px-4 py-3 text-emerald-400">{result.repo_a.maintainability}</td>
                  <td className="px-4 py-3 text-emerald-400">{result.repo_b.maintainability}</td>
                  <td className="px-4 py-3 text-[#8b949e]">-</td>
                </tr>
                <tr className="hover:bg-[#21262d]/50">
                  <td className="px-4 py-3 font-semibold text-[#e6edf3]">Code Smells Detected</td>
                  <td className="px-4 py-3 text-amber-400">{result.repo_a.smells_count}</td>
                  <td className="px-4 py-3 text-amber-400">{result.repo_b.smells_count}</td>
                  <td className="px-4 py-3 text-[#8b949e]">
                    {result.repo_a.smells_count < result.repo_b.smells_count ? 'Repo A fewer smells' : 'Repo B fewer smells'}
                  </td>
                </tr>
                <tr className="hover:bg-[#21262d]/50">
                  <td className="px-4 py-3 font-semibold text-[#e6edf3]">Security Pattern Findings</td>
                  <td className="px-4 py-3 text-red-400">{result.repo_a.security_findings}</td>
                  <td className="px-4 py-3 text-red-400">{result.repo_b.security_findings}</td>
                  <td className="px-4 py-3 text-[#8b949e]">
                    {result.repo_a.security_findings === 0 && result.repo_b.security_findings === 0 ? 'Both zero findings' : '-'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
