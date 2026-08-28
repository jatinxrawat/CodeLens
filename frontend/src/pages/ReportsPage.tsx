import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  RefreshCw,
  AlertCircle,
  Eye,
  Code2,
  Sparkles,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { fetchReportMarkdown, fetchReportData } from '../services/api';

interface ReportsPageProps {
  selectedRepo: string;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ selectedRepo }) => {
  const [markdown, setMarkdown] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'rendered' | 'raw'>('rendered');
  const [exportingJson, setExportingJson] = useState(false);

  const loadReport = async (forceRefresh: boolean = false) => {
    if (!selectedRepo) return;
    setLoading(true);
    setError(null);
    try {
      const md = await fetchReportMarkdown(selectedRepo, forceRefresh);
      setMarkdown(md);
    } catch (err: any) {
      console.error('Failed to load report:', err);
      setError(err?.message || 'Failed to compile analysis report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedRepo) {
      loadReport(false);
    }
  }, [selectedRepo]);

  const handleCopy = () => {
    if (!markdown) return;
    navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedRepo}-analysis-report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = async () => {
    if (!selectedRepo) return;
    setExportingJson(true);
    try {
      const data = await fetchReportData(selectedRepo, false);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedRepo}-analysis-report.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error(err);
      alert('Failed to export JSON report: ' + (err?.message || 'Unknown error'));
    } finally {
      setExportingJson(false);
    }
  };

  if (!selectedRepo) {
    return (
      <div className="p-8 max-w-5xl mx-auto flex flex-col items-center justify-center min-h-[60vh] text-center">
        <FileText className="w-12 h-12 text-[#8b949e] mb-3 opacity-60" />
        <h2 className="text-base font-semibold text-[#e6edf3]">No Repository Selected</h2>
        <p className="text-xs text-[#8b949e] mt-1 max-w-md">
          Please select an indexed repository from the sidebar to inspect its architecture, code quality, and security report.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-semibold text-[#e6edf3]">Repository Analysis Report</h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/30">
              {selectedRepo}
            </span>
          </div>
          <p className="text-xs text-[#8b949e] mt-0.5">
            Export comprehensive code intelligence, architecture topologies, and static security metrics.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {/* Refresh Button */}
          <button
            onClick={() => loadReport(true)}
            disabled={loading}
            title="Recompile report fresh from source metrics"
            className="px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] disabled:opacity-50 text-[#e6edf3] rounded-md text-xs font-mono transition-colors flex items-center space-x-1.5 border border-[#30363d]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#58a6ff]' : ''}`} />
            <span>{loading ? 'Compiling...' : 'Recompute'}</span>
          </button>

          {/* Copy MD */}
          <button
            onClick={handleCopy}
            disabled={loading || !markdown}
            className="px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] disabled:opacity-50 text-[#e6edf3] rounded-md text-xs font-mono transition-colors flex items-center space-x-1.5 border border-[#30363d]"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy MD'}</span>
          </button>

          {/* Export Markdown */}
          <button
            onClick={handleDownloadMarkdown}
            disabled={loading || !markdown}
            className="px-3 py-1.5 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white rounded-md text-xs font-mono transition-colors flex items-center space-x-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export MD</span>
          </button>

          {/* Export JSON */}
          <button
            onClick={handleDownloadJSON}
            disabled={loading || exportingJson}
            className="px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white rounded-md text-xs font-mono transition-colors flex items-center space-x-1.5 shadow-sm"
          >
            <Download className={`w-3.5 h-3.5 ${exportingJson ? 'animate-spin' : ''}`} />
            <span>{exportingJson ? 'Exporting...' : 'Export JSON'}</span>
          </button>
        </div>
      </div>

      {/* Main Report Card */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden shadow-sm">
        {/* Card Header & View Switcher */}
        <div className="h-11 bg-[#0d1117] border-b border-[#30363d] px-4 flex items-center justify-between text-xs font-mono text-[#8b949e]">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-[#58a6ff]" />
            <span className="text-[#e6edf3] font-medium">{selectedRepo}-report.md</span>
          </div>

          <div className="flex items-center space-x-1 bg-[#161b22] p-0.5 rounded-lg border border-[#30363d]">
            <button
              onClick={() => setViewMode('rendered')}
              className={`px-2.5 py-1 rounded-md text-[11px] font-sans flex items-center space-x-1.5 transition-all ${
                viewMode === 'rendered'
                  ? 'bg-[#1f6feb] text-white shadow-sm'
                  : 'text-[#8b949e] hover:text-[#e6edf3]'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-2.5 py-1 rounded-md text-[11px] font-sans flex items-center space-x-1.5 transition-all ${
                viewMode === 'raw'
                  ? 'bg-[#1f6feb] text-white shadow-sm'
                  : 'text-[#8b949e] hover:text-[#e6edf3]'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Raw Markdown</span>
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="min-h-[400px]">
          {loading ? (
            <div className="p-16 flex flex-col items-center justify-center text-center space-y-4">
              <div className="relative">
                <div className="w-12 h-12 rounded-full border-2 border-[#1f6feb]/30 border-t-[#58a6ff] animate-spin" />
                <Sparkles className="w-5 h-5 text-[#58a6ff] absolute inset-0 m-auto animate-pulse" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-[#e6edf3]">Compiling Analysis Report...</p>
                <p className="text-xs text-[#8b949e]">
                  Analyzing AST chunks, inferring architecture topologies, calculating cyclomatic metrics, and scanning security patterns.
                </p>
              </div>
            </div>
          ) : error ? (
            <div className="p-12 flex flex-col items-center justify-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-red-400">Failed to Compile Report</p>
                <p className="text-xs text-[#8b949e] max-w-md font-mono">{error}</p>
              </div>
              <button
                onClick={() => loadReport(true)}
                className="px-4 py-2 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] rounded-md text-xs font-mono transition-colors flex items-center space-x-2 border border-[#30363d]"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Compilation</span>
              </button>
            </div>
          ) : viewMode === 'rendered' ? (
            <div className="p-8 max-h-[75vh] overflow-y-auto prose prose-invert max-w-none text-xs text-[#e6edf3] leading-relaxed space-y-4">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold text-[#e6edf3] border-b border-[#30363d] pb-2 mb-4">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-base font-semibold text-[#58a6ff] border-b border-[#21262d] pb-1.5 mt-6 mb-3">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-sm font-semibold text-[#79c0ff] mt-4 mb-2">
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="text-xs text-[#c9d1d9] leading-relaxed mb-3">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside space-y-1.5 text-xs text-[#c9d1d9] mb-3 ml-2">
                      {children}
                    </ul>
                  ),
                  li: ({ children }) => (
                    <li className="text-xs text-[#c9d1d9]">{children}</li>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-2 border-[#1f6feb] pl-3 py-1 bg-[#1f6feb]/5 text-[#8b949e] rounded-r my-3">
                      {children}
                    </blockquote>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-4 border border-[#30363d] rounded-lg">
                      <table className="min-w-full text-left text-xs divide-y divide-[#30363d]">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-[#0d1117] text-[#8b949e] font-mono text-[11px]">
                      {children}
                    </thead>
                  ),
                  tbody: ({ children }) => (
                    <tbody className="divide-y divide-[#21262d] bg-[#161b22]/50 font-mono text-[11px]">
                      {children}
                    </tbody>
                  ),
                  th: ({ children }) => (
                    <th className="px-3 py-2 font-medium">{children}</th>
                  ),
                  td: ({ children }) => (
                    <td className="px-3 py-2 text-[#c9d1d9]">{children}</td>
                  ),
                  code: ({ children }) => (
                    <code className="px-1.5 py-0.5 rounded bg-[#21262d] text-[#ff7b72] font-mono text-[11px] border border-[#30363d]/50">
                      {children}
                    </code>
                  ),
                  hr: () => <hr className="border-[#30363d] my-6" />,
                }}
              >
                {markdown}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="p-6 bg-[#0b0f14] overflow-auto max-h-[75vh] font-mono text-xs text-[#e6edf3] leading-relaxed whitespace-pre-wrap select-text">
              {markdown}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
