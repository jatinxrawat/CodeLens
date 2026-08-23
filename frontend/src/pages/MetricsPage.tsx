import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Play,
  CheckCircle2,
  Clock,
  Sparkles,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import { EvaluationResponse } from '../types';
import { runEvaluationBenchmark } from '../services/api';

interface MetricsPageProps {
  selectedRepo: string;
}

export const MetricsPage: React.FC<MetricsPageProps> = ({ selectedRepo }) => {
  const [evalData, setEvalData] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunEvaluation = async () => {
    if (!selectedRepo) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runEvaluationBenchmark(selectedRepo, 5);
      setEvalData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to run evaluation');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedRepo) {
      handleRunEvaluation();
    }
  }, [selectedRepo]);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-[#e6edf3]">Retrieval Evaluation Studio</h1>
          <p className="text-xs text-[#8b949e] mt-0.5">
            Empirically compare BM25 Lexical Keyword, FAISS Dense Vector, and Hybrid Fusion retrieval metrics.
          </p>
        </div>
        <button
          onClick={handleRunEvaluation}
          disabled={loading || !selectedRepo}
          className="px-4 py-2 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white rounded-md text-xs font-semibold flex items-center space-x-2 transition-colors shadow-sm"
        >
          <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Evaluating...' : 'Run Benchmark'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Model Comparative Table */}
      {evalData && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden shadow-sm">
          <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#e6edf3]">
              Retrieval Model Comparison ({evalData.total_queries} Benchmark Queries)
            </h3>
            <span className="text-xs font-mono text-[#8b949e]">Top-K = 5</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left font-mono">
              <thead className="bg-[#0d1117] text-[#8b949e] uppercase text-[10px] tracking-wider border-b border-[#30363d]">
                <tr>
                  <th className="px-4 py-3">Retrieval Mode</th>
                  <th className="px-4 py-3">Dense Alpha (α)</th>
                  <th className="px-4 py-3">Recall@1</th>
                  <th className="px-4 py-3">Recall@3</th>
                  <th className="px-4 py-3">Recall@5</th>
                  <th className="px-4 py-3">Mean Reciprocal Rank (MRR)</th>
                  <th className="px-4 py-3">Avg Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#30363d]/60">
                {evalData.comparisons.map((c) => {
                  const isTopMRR = c.mean_reciprocal_rank >= 0.8;
                  return (
                    <tr key={c.mode} className="hover:bg-[#21262d]/50 transition-colors">
                      <td className="px-4 py-3 font-semibold text-[#e6edf3] flex items-center space-x-2">
                        {isTopMRR && <span className="w-2 h-2 rounded-full bg-emerald-400"></span>}
                        <span>{c.mode}</span>
                      </td>
                      <td className="px-4 py-3 text-[#8b949e]">{c.alpha.toFixed(2)}</td>
                      <td className="px-4 py-3 text-emerald-400 font-bold">{(c.recall_at_1 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-emerald-400">{(c.recall_at_3 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-emerald-400">{(c.recall_at_5 * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3 text-[#58a6ff] font-bold">{c.mean_reciprocal_rank.toFixed(4)}</td>
                      <td className="px-4 py-3 text-[#8b949e]">{c.avg_latency_ms} ms</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Query Breakdown Table */}
      {evalData && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-3">
          <h3 className="text-sm font-semibold text-[#e6edf3]">
            Individual Query Retrieval Breakdown (Hybrid Mode α=0.7)
          </h3>
          <div className="space-y-2">
            {evalData.query_breakdown.map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-[#0d1117] border border-[#30363d] text-xs font-mono flex items-center justify-between"
              >
                <div className="space-y-0.5 max-w-xl truncate">
                  <div className="text-[#e6edf3] font-sans font-medium truncate">"{item.query}"</div>
                  <div className="text-[11px] text-[#8b949e]">
                    Expected: <span className="text-[#58a6ff]">{item.expected_file}</span> ({item.expected_symbol || 'N/A'})
                  </div>
                </div>
                <div className="flex items-center space-x-3 shrink-0">
                  <span
                    className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                      item.found_rank === 1
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : item.found_rank
                        ? 'bg-blue-950 text-blue-400 border border-blue-800'
                        : 'bg-red-950 text-red-400 border border-red-800'
                    }`}
                  >
                    {item.found_rank ? `Rank #${item.found_rank}` : 'Not in Top 5'}
                  </span>
                  <span className="text-[#8b949e] text-[11px]">{item.latency_ms} ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
