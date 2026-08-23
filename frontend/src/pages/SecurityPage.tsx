import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Lock,
  FileCode,
} from 'lucide-react';
import type { SecurityScanReport, SecurityFinding } from '../types';
import { fetchSecurityScan } from '../services/api';

interface SecurityPageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
}

export const SecurityPage: React.FC<SecurityPageProps> = ({
  selectedRepo,
  onOpenFileInExplorer,
}) => {
  const [scan, setScan] = useState<SecurityScanReport | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoading(true);
    fetchSecurityScan(selectedRepo)
      .then(setScan)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedRepo]);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[#e6edf3]">Static Security Insights & Risk Patterns</h1>
        <p className="text-xs text-[#8b949e] mt-0.5">
          Non-destructive static AST and pattern scanner detecting hardcoded secrets, SQL injection risks, and unsafe execution without running untrusted code.
        </p>
      </div>

      {scan && (
        <div className="space-y-6">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <div className="text-xs text-[#8b949e] mb-1">Total Security Findings</div>
              <div className="text-2xl font-bold font-mono text-[#e6edf3]">
                {scan.total_findings}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Static risk patterns</p>
            </div>

            <div className="bg-[#161b22] border border-red-900/40 rounded-lg p-4 bg-red-950/10">
              <div className="text-xs text-red-400 mb-1 font-semibold">Critical Severity</div>
              <div className="text-2xl font-bold font-mono text-red-400">
                {scan.critical_count}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Credentials & remote execution</p>
            </div>

            <div className="bg-[#161b22] border border-amber-900/40 rounded-lg p-4 bg-amber-950/10">
              <div className="text-xs text-amber-400 mb-1 font-semibold">High Severity</div>
              <div className="text-2xl font-bold font-mono text-amber-400">
                {scan.high_count}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">Injection & subprocess risks</p>
            </div>

            <div className="bg-[#161b22] border border-blue-900/40 rounded-lg p-4 bg-blue-950/10">
              <div className="text-xs text-blue-400 mb-1 font-semibold">Medium Severity</div>
              <div className="text-2xl font-bold font-mono text-blue-400">
                {scan.medium_count}
              </div>
              <p className="text-[11px] text-[#8b949e] mt-1">TLS & configuration risks</p>
            </div>
          </div>

          {/* Security Findings List */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-[#e6edf3]">
              Security Findings ({scan.total_findings})
            </h3>

            <div className="space-y-3">
              {scan.findings.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#8b949e] flex flex-col items-center space-y-2">
                  <ShieldCheck className="w-8 h-8 text-emerald-400" />
                  <span className="text-sm font-semibold text-[#e6edf3]">
                    No Static Security Vulnerabilities Detected
                  </span>
                  <span className="text-xs text-[#8b949e] max-w-md">
                    Zero hardcoded secrets, SQL injection patterns, or unsafe subprocess calls found in indexed source files.
                  </span>
                </div>
              ) : (
                scan.findings.map((finding: SecurityFinding) => (
                  <div
                    key={finding.id}
                    className="p-4 rounded-lg bg-[#0d1117] border border-[#30363d] text-xs font-mono space-y-2 hover:border-[#484f58] transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            finding.severity === 'CRITICAL'
                              ? 'bg-red-950 text-red-400 border border-red-800'
                              : finding.severity === 'HIGH'
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-blue-950 text-blue-400 border border-blue-800'
                          }`}
                        >
                          {finding.severity}
                        </span>
                        <span className="font-bold text-[#e6edf3]">{finding.rule_name}</span>
                        <span className="text-[10px] text-[#8b949e]">({finding.rule_id})</span>
                      </div>
                      <span
                        onClick={() => onOpenFileInExplorer(finding.file_path)}
                        className="text-[#58a6ff] hover:underline cursor-pointer"
                      >
                        {finding.file_path}:{finding.start_line}
                      </span>
                    </div>

                    <div className="text-[11px] text-[#8b949e] font-sans">
                      {finding.explanation}
                    </div>

                    <pre className="p-2 bg-[#161b22] rounded text-[11px] text-amber-300 font-mono overflow-x-auto">
                      Matched: {finding.matched_snippet}
                    </pre>

                    <div className="text-[11px] text-emerald-400/90 font-sans pt-1">
                      🛡️ <strong>Mitigation:</strong> {finding.recommendation}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="p-3 bg-[#0d1117] border border-[#30363d] rounded-lg text-[11px] text-[#8b949e]">
            {scan.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
