import React, { useState, useEffect } from 'react';
import {
  Gauge,
  Sliders,
  AlertTriangle,
  FileCode,
  Sparkles,
  ExternalLink,
  Code2,
} from 'lucide-react';
import type { RepositoryQualityMetrics, CodeSmellReport, FunctionComplexity, CodeSmellFinding } from '../types';
import { fetchQualityMetrics, fetchCodeSmells } from '../services/api';

interface CodeQualityPageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
}

export const CodeQualityPage: React.FC<CodeQualityPageProps> = ({
  selectedRepo,
  onOpenFileInExplorer,
}) => {
  const [metrics, setMetrics] = useState<RepositoryQualityMetrics | null>(null);
  const [smells, setSmells] = useState<CodeSmellReport | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoading(true);
    Promise.all([fetchQualityMetrics(selectedRepo), fetchCodeSmells(selectedRepo)])
      .then(([m, s]) => {
        setMetrics(m);
        setSmells(s);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedRepo]);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[#e6edf3]">Static Code Quality & Smell Detection</h1>
        <p className="text-xs text-[#8b949e] mt-0.5">
          Calculates McCabe Cyclomatic Complexity, nesting depth, and rule-based maintainability code smells.
        </p>
      </div>

      {metrics && (
        <div className="space-y-6">
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <div className="text-xs text-[#8b949e] mb-1">Maintainability</div>
              <div className="text-2xl font-bold font-mono text-emerald-400">
                {metrics.overall_maintainability}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Based on CC & nesting</p>
            </div>

            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <div className="text-xs text-[#8b949e] mb-1">Avg Cyclomatic Complexity</div>
              <div className="text-2xl font-bold font-mono text-[#58a6ff]">
                {metrics.avg_cyclomatic_complexity}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Decision points per chunk</p>
            </div>

            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <div className="text-xs text-[#8b949e] mb-1">Coupling Level</div>
              <div className="text-2xl font-bold font-mono text-[#e6edf3]">
                {metrics.coupling_level}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Inter-module fan-out</p>
            </div>

            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <div className="text-xs text-[#8b949e] mb-1">Code Smells</div>
              <div className="text-2xl font-bold font-mono text-amber-400">
                {smells?.total_findings || 0}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">
                {smells?.critical_count || 0} critical, {smells?.warning_count || 0} warning
              </p>
            </div>
          </div>

          {/* Top Complex Functions Table */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[#e6edf3]">
                Cyclomatic Complexity Hotspots
              </h3>
              <span className="text-xs text-[#8b949e] font-mono">McCabe Complexity &gt; 1</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left font-mono">
                <thead className="bg-[#0d1117] text-[#8b949e] uppercase text-[10px] tracking-wider border-b border-[#30363d]">
                  <tr>
                    <th className="px-4 py-3">Symbol</th>
                    <th className="px-4 py-3">File Location</th>
                    <th className="px-4 py-3">LOC</th>
                    <th className="px-4 py-3">McCabe CC</th>
                    <th className="px-4 py-3">Max Nesting</th>
                    <th className="px-4 py-3">Rating</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#30363d]/60">
                  {metrics.top_complex_functions.map((fn: FunctionComplexity, idx: number) => (
                    <tr key={idx} className="hover:bg-[#21262d]/50 transition-colors">
                      <td className="px-4 py-3 font-semibold text-[#58a6ff]">
                        {fn.symbol}()
                      </td>
                      <td
                        onClick={() => onOpenFileInExplorer(fn.file_path)}
                        className="px-4 py-3 text-[#e6edf3] hover:underline cursor-pointer"
                      >
                        {fn.file_path}:{fn.start_line}
                      </td>
                      <td className="px-4 py-3 text-[#8b949e]">{fn.lines_of_code}</td>
                      <td className="px-4 py-3 font-bold text-[#e6edf3]">
                        {fn.cyclomatic_complexity}
                      </td>
                      <td className="px-4 py-3 text-[#8b949e]">{fn.nesting_depth} levels</td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] ${
                            fn.rating === 'VERY_HIGH'
                              ? 'bg-red-950 text-red-400'
                              : fn.rating === 'HIGH'
                              ? 'bg-amber-950 text-amber-400'
                              : fn.rating === 'MEDIUM'
                              ? 'bg-blue-950 text-blue-400'
                              : 'bg-emerald-950 text-emerald-400'
                          }`}
                        >
                          {fn.rating}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Code Smell Findings */}
          {smells && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="text-sm font-semibold text-[#e6edf3]">
                Detected Code Smells ({smells.total_findings})
              </h3>

              <div className="space-y-3">
                {smells.findings.length === 0 ? (
                  <div className="p-4 text-center text-xs text-[#8b949e]">
                    No critical code smells detected. Codebase conforms to clean complexity thresholds.
                  </div>
                ) : (
                  smells.findings.map((smell: CodeSmellFinding) => (
                    <div
                      key={smell.id}
                      className="p-4 rounded-lg bg-[#0d1117] border border-[#30363d] text-xs font-mono space-y-1.5 hover:border-[#484f58] transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              smell.severity === 'CRITICAL'
                                ? 'bg-red-950 text-red-400 border border-red-800'
                                : smell.severity === 'WARNING'
                                ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                : 'bg-blue-950 text-blue-400 border border-blue-800'
                            }`}
                          >
                            {smell.severity}
                          </span>
                          <span className="font-bold text-[#e6edf3]">{smell.issue_title}</span>
                        </div>
                        <span
                          onClick={() => onOpenFileInExplorer(smell.file_path)}
                          className="text-[#58a6ff] hover:underline cursor-pointer"
                        >
                          {smell.file_path}:{smell.start_line}
                        </span>
                      </div>

                      <div className="text-[11px] text-[#8b949e]">
                        Observed: <strong className="text-[#e6edf3]">{smell.metric_value}</strong> (threshold: {smell.threshold})
                      </div>

                      <div className="text-[11px] text-emerald-400/90 font-sans pt-1">
                        💡 <strong>Recommendation:</strong> {smell.recommendation}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
