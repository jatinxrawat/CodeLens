import React, { useState, useEffect } from 'react';
import {
  Gauge,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Lock,
  FileCode,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import type {
  RepositoryQualityMetrics,
  CodeSmellReport,
  SecurityScanReport,
  SecurityFinding,
  CodeSmellFinding,
  FunctionComplexity,
} from '../types';
import { fetchQualityMetrics, fetchCodeSmells, fetchSecurityScan } from '../services/api';

interface HealthPageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
  defaultTab?: 'quality' | 'security';
}

export const HealthPage: React.FC<HealthPageProps> = ({
  selectedRepo,
  onOpenFileInExplorer,
  defaultTab = 'quality',
}) => {
  const [activeTab, setActiveTab] = useState<'quality' | 'security'>(defaultTab);

  // Quality State
  const [metrics, setMetrics] = useState<RepositoryQualityMetrics | null>(null);
  const [smells, setSmells] = useState<CodeSmellReport | null>(null);
  const [loadingQuality, setLoadingQuality] = useState(false);

  // Security State
  const [scan, setScan] = useState<SecurityScanReport | null>(null);
  const [loadingSecurity, setLoadingSecurity] = useState(false);

  useEffect(() => {
    if (defaultTab) {
      setActiveTab(defaultTab);
    }
  }, [defaultTab]);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoadingQuality(true);
    Promise.all([fetchQualityMetrics(selectedRepo), fetchCodeSmells(selectedRepo)])
      .then(([m, s]) => {
        setMetrics(m);
        setSmells(s);
      })
      .catch((err) => console.error('Failed to load quality metrics:', err))
      .finally(() => setLoadingQuality(false));

    setLoadingSecurity(true);
    fetchSecurityScan(selectedRepo)
      .then(setScan)
      .catch((err) => console.error('Failed to load security scan:', err))
      .finally(() => setLoadingSecurity(false));
  }, [selectedRepo]);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Top Header & View Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#252535] pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-sky-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">Codebase Health & Security Audit</h1>
          </div>
          <p className="text-xs text-[#a1a1aa] mt-1">
            Unified code quality metrics, cyclomatic complexity, maintainability smells, and static AST security scanning.
          </p>
        </div>

        {/* Tab Switcher Pills */}
        <div className="flex items-center bg-[#15151e] p-1 rounded-xl border border-[#272738] shrink-0 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('quality')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'quality'
                ? 'bg-sky-500 text-white shadow-md'
                : 'text-[#a1a1aa] hover:text-white hover:bg-[#20202d]'
            }`}
          >
            <Gauge className="w-3.5 h-3.5" />
            <span>Quality & Smells</span>
            {smells && (
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                  activeTab === 'quality' ? 'bg-sky-700 text-white' : 'bg-[#252538] text-[#a1a1aa]'
                }`}
              >
                {smells.total_findings}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('security')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'security'
                ? 'bg-rose-500 text-white shadow-md'
                : 'text-[#a1a1aa] hover:text-white hover:bg-[#20202d]'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Security Insights</span>
            {scan && (
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                  activeTab === 'security' ? 'bg-rose-700 text-white' : 'bg-[#252538] text-[#a1a1aa]'
                }`}
              >
                {scan.total_findings}
              </span>
            )}
          </button>
        </div>
      </div>

      {!selectedRepo && (
        <div className="p-8 text-center bg-[#15151e] border border-[#272738] rounded-2xl text-xs text-[#a1a1aa]">
          Please select or attach a repository in the sidebar to inspect codebase health.
        </div>
      )}

      {/* ================= TAB 1: QUALITY & SMELLS ================= */}
      {activeTab === 'quality' && selectedRepo && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {loadingQuality && (
            <div className="p-12 text-center text-xs text-[#a1a1aa]">Computing quality metrics and code smells...</div>
          )}

          {metrics && (
            <div className="space-y-6">
              {/* Top Metrics Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-[#15151e] border border-[#272738] rounded-2xl p-4.5 shadow-sm">
                  <div className="text-xs text-[#a1a1aa] mb-1 font-medium">Maintainability</div>
                  <div className="flex items-center space-x-2.5">
                    <span
                      className={`text-2xl font-bold font-mono ${
                        metrics.overall_maintainability === 'HIGH'
                          ? 'text-emerald-400'
                          : metrics.overall_maintainability === 'MEDIUM'
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {metrics.overall_maintainability}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#71717a] mt-1.5">Based on CC, length & nesting</div>
                </div>

                <div className="bg-[#15151e] border border-[#272738] rounded-2xl p-4.5 shadow-sm">
                  <div className="text-xs text-[#a1a1aa] mb-1 font-medium">Avg Cyclomatic Complexity</div>
                  <div className="text-2xl font-bold font-mono text-sky-400">
                    {metrics.avg_cyclomatic_complexity.toFixed(2)}
                  </div>
                  <div className="text-[11px] text-[#71717a] mt-1.5">Target &lt; 5.0 for clean branches</div>
                </div>

                <div className="bg-[#15151e] border border-[#272738] rounded-2xl p-4.5 shadow-sm">
                  <div className="text-xs text-[#a1a1aa] mb-1 font-medium">Coupling Level</div>
                  <div className="text-2xl font-bold font-mono text-white">
                    {metrics.coupling_level}
                  </div>
                  <div className="text-[11px] text-[#71717a] mt-1.5">Inter-module dependencies</div>
                </div>

                <div className="bg-[#15151e] border border-[#272738] rounded-2xl p-4.5 shadow-sm">
                  <div className="text-xs text-[#a1a1aa] mb-1 font-medium">Total Code Smells</div>
                  <div className="text-2xl font-bold font-mono text-amber-400">
                    {smells ? smells.total_findings : 0}
                  </div>
                  <div className="text-[11px] text-[#71717a] mt-1.5">
                    {smells ? `${smells.critical_count} critical, ${smells.warning_count} warning` : 'None detected'}
                  </div>
                </div>
              </div>

              {/* Cyclomatic Complexity Hotspots Table */}
              {metrics.top_complex_functions && metrics.top_complex_functions.length > 0 && (
                <div className="bg-[#15151e] border border-[#272738] rounded-2xl overflow-hidden shadow-sm">
                  <div className="px-5 py-4 border-b border-[#272738] flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-white">Cyclomatic Complexity Hotspots</h3>
                      <p className="text-xs text-[#a1a1aa] mt-0.5">
                        Functions with the highest branch paths and nesting depth
                      </p>
                    </div>
                    <span className="text-xs text-[#a1a1aa] font-mono">
                      {metrics.top_complex_functions.length} functions flagged
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left font-mono">
                      <thead className="bg-[#101017] text-[#a1a1aa] uppercase text-[10px] tracking-wider border-b border-[#272738]">
                        <tr>
                          <th className="px-4 py-3">Function Symbol</th>
                          <th className="px-4 py-3">File Location</th>
                          <th className="px-4 py-3">LOC</th>
                          <th className="px-4 py-3">McCabe CC</th>
                          <th className="px-4 py-3">Nesting</th>
                          <th className="px-4 py-3">Risk Rating</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#272738]/60">
                        {metrics.top_complex_functions.map((fn: FunctionComplexity, idx: number) => (
                          <tr key={idx} className="hover:bg-[#1a1a26]/60 transition-colors">
                            <td className="px-4 py-3 font-semibold text-sky-400">
                              {fn.symbol}()
                            </td>
                            <td
                              onClick={() => onOpenFileInExplorer(fn.file_path)}
                              className="px-4 py-3 text-white hover:underline cursor-pointer"
                            >
                              {fn.file_path}:{fn.start_line}
                            </td>
                            <td className="px-4 py-3 text-[#a1a1aa]">{fn.lines_of_code}</td>
                            <td className="px-4 py-3 font-bold text-amber-400">
                              {fn.cyclomatic_complexity}
                            </td>
                            <td className="px-4 py-3 text-[#a1a1aa]">{fn.nesting_depth} levels</td>
                            <td className="px-4 py-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  fn.rating === 'VERY_HIGH'
                                    ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                    : fn.rating === 'HIGH'
                                    ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                    : fn.rating === 'MEDIUM'
                                    ? 'bg-blue-950 text-blue-400 border border-blue-800'
                                    : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
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
              )}

              {/* Code Smell Findings */}
              {smells && (
                <div className="bg-[#15151e] border border-[#272738] rounded-2xl p-5 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-white">
                        Detected Code Smells ({smells.total_findings})
                      </h3>
                      <p className="text-xs text-[#a1a1aa] mt-0.5">
                        Rule violations including brain methods, god files, deep inheritance, and parameter bloat
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {smells.findings.length === 0 ? (
                      <div className="p-6 text-center text-xs text-[#a1a1aa] bg-[#101017] border border-[#272738] rounded-xl">
                        No critical code smells detected. Codebase conforms to clean complexity thresholds!
                      </div>
                    ) : (
                      smells.findings.map((smell: CodeSmellFinding) => (
                        <div
                          key={smell.id}
                          className="p-4 rounded-xl bg-[#101017] border border-[#272738] text-xs font-mono space-y-2 hover:border-[#383850] transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  smell.severity === 'CRITICAL'
                                    ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                    : smell.severity === 'WARNING'
                                    ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                    : 'bg-blue-950 text-blue-400 border border-blue-800'
                                }`}
                              >
                                {smell.severity}
                              </span>
                              <span className="font-bold text-white">{smell.issue_title}</span>
                            </div>

                            <span
                              onClick={() => onOpenFileInExplorer(smell.file_path)}
                              className="text-sky-400 hover:underline cursor-pointer flex items-center space-x-1"
                            >
                              <span>
                                {smell.file_path.split('/').pop()}:{smell.start_line}
                              </span>
                              <ExternalLink className="w-3 h-3" />
                            </span>
                          </div>

                          <div className="text-[#a1a1aa] flex items-center space-x-4 text-[11px]">
                            <span>Rule: <strong className="text-white">{smell.rule_name}</strong></span>
                            <span>Measured: <strong className="text-amber-400">{smell.metric_value}</strong></span>
                            <span>Threshold: {smell.threshold}</span>
                          </div>

                          <p className="text-xs text-[#71717a] font-sans">
                            {smell.recommendation}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ================= TAB 2: SECURITY INSIGHTS ================= */}
      {activeTab === 'security' && selectedRepo && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {loadingSecurity && (
            <div className="p-12 text-center text-xs text-[#a1a1aa]">Scanning AST for security vulnerabilities...</div>
          )}

          {scan && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-[#15151e] border border-[#272738] rounded-2xl p-4.5 shadow-sm">
                  <div className="text-xs text-[#a1a1aa] mb-1 font-medium">Total Security Findings</div>
                  <div className="text-2xl font-bold font-mono text-white">
                    {scan.total_findings}
                  </div>
                  <div className="text-[11px] text-[#71717a] mt-1.5">Static risk patterns</div>
                </div>

                <div className="bg-[#15151e] border border-rose-900/40 rounded-2xl p-4.5 shadow-sm bg-rose-950/10">
                  <div className="text-xs text-rose-400 mb-1 font-medium">Critical Severity</div>
                  <div className="text-2xl font-bold font-mono text-rose-400">
                    {scan.critical_count}
                  </div>
                  <div className="text-[11px] text-[#71717a] mt-1.5">Hardcoded secrets & unsafe exec</div>
                </div>

                <div className="bg-[#15151e] border border-amber-900/40 rounded-2xl p-4.5 shadow-sm bg-amber-950/10">
                  <div className="text-xs text-amber-400 mb-1 font-medium">High Severity</div>
                  <div className="text-2xl font-bold font-mono text-amber-400">
                    {scan.high_count}
                  </div>
                  <div className="text-[11px] text-[#71717a] mt-1.5">Injection & deserialization risks</div>
                </div>

                <div className="bg-[#15151e] border border-blue-900/40 rounded-2xl p-4.5 shadow-sm bg-blue-950/10">
                  <div className="text-xs text-blue-400 mb-1 font-medium">Medium & Low Severity</div>
                  <div className="text-2xl font-bold font-mono text-blue-400">
                    {scan.medium_count + scan.low_count}
                  </div>
                  <div className="text-[11px] text-[#71717a] mt-1.5">TLS, debug & config flags</div>
                </div>
              </div>

              {/* Security Findings List */}
              <div className="bg-[#15151e] border border-[#272738] rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white">
                      Security Findings ({scan.total_findings})
                    </h3>
                    <p className="text-xs text-[#a1a1aa] mt-0.5">
                      Non-destructive static AST scanner detecting security risks without running untrusted code
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  {scan.findings.length === 0 ? (
                    <div className="p-8 text-center text-xs text-[#a1a1aa] flex flex-col items-center space-y-2 bg-[#101017] border border-[#272738] rounded-xl">
                      <ShieldCheck className="w-8 h-8 text-emerald-400" />
                      <span className="text-sm font-semibold text-white">
                        No Static Security Vulnerabilities Detected
                      </span>
                      <span className="text-xs text-[#71717a] max-w-md">
                        Zero hardcoded secrets, SQL injection patterns, or unsafe subprocess calls found in indexed source files.
                      </span>
                    </div>
                  ) : (
                    scan.findings.map((finding: SecurityFinding) => (
                      <div
                        key={finding.id}
                        className="p-4 rounded-xl bg-[#101017] border border-[#272738] text-xs font-mono space-y-2 hover:border-[#383850] transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                finding.severity === 'CRITICAL'
                                  ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                  : finding.severity === 'HIGH'
                                  ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                  : 'bg-blue-950 text-blue-400 border border-blue-800'
                              }`}
                            >
                              {finding.severity}
                            </span>
                            <span className="font-bold text-white">{finding.rule_name}</span>
                          </div>

                          <span
                            onClick={() => onOpenFileInExplorer(finding.file_path)}
                            className="text-sky-400 hover:underline cursor-pointer flex items-center space-x-1"
                          >
                            <span>
                              {finding.file_path.split('/').pop()}:{finding.start_line}
                            </span>
                            <ExternalLink className="w-3 h-3" />
                          </span>
                        </div>

                        <p className="text-xs text-[#a1a1aa] font-sans leading-relaxed">
                          {finding.explanation}
                        </p>

                        {finding.matched_snippet && (
                          <pre className="p-2.5 rounded-lg bg-[#0a0a0f] text-[#ececec] overflow-x-auto text-[11px] border border-[#242436]">
                            <code>{finding.matched_snippet}</code>
                          </pre>
                        )}

                        <div className="text-[11px] text-emerald-400 font-sans flex items-center space-x-1.5 pt-1">
                          <span className="font-semibold">Recommendation:</span>
                          <span>{finding.recommendation}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
