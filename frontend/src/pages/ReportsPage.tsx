import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  RefreshCw,
} from 'lucide-react';
import { fetchReportMarkdown, fetchReportData } from '../services/api';

interface ReportsPageProps {
  selectedRepo: string;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ selectedRepo }) => {
  const [markdown, setMarkdown] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const loadReport = async () => {
    if (!selectedRepo) return;
    setLoading(true);
    try {
      const md = await fetchReportMarkdown(selectedRepo);
      setMarkdown(md);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [selectedRepo]);

  const handleCopy = () => {
    navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedRepo}-analysis-report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = async () => {
    try {
      const data = await fetchReportData(selectedRepo);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedRepo}-analysis-report.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold text-[#e6edf3]">Repository Analysis Report</h1>
          <p className="text-xs text-[#8b949e] mt-0.5">
            Export comprehensive code intelligence, architecture, and security reports as Markdown or JSON.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] rounded-md text-xs font-mono transition-colors flex items-center space-x-1.5"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy MD'}</span>
          </button>
          <button
            onClick={handleDownloadMarkdown}
            className="px-3 py-1.5 bg-[#1f6feb] hover:bg-[#388bfd] text-white rounded-md text-xs font-mono transition-colors flex items-center space-x-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Markdown</span>
          </button>
          <button
            onClick={handleDownloadJSON}
            className="px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] text-white rounded-md text-xs font-mono transition-colors flex items-center space-x-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Markdown Preview Box */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden shadow-sm">
        <div className="h-10 bg-[#0d1117] border-b border-[#30363d] px-4 flex items-center justify-between text-xs font-mono text-[#8b949e]">
          <div className="flex items-center space-x-2">
            <FileText className="w-3.5 h-3.5 text-[#58a6ff]" />
            <span>{selectedRepo}-report.md</span>
          </div>
          <span>GFM Markdown</span>
        </div>

        <div className="p-6 bg-[#0b0f14] overflow-auto max-h-[70vh] font-mono text-xs text-[#e6edf3] leading-relaxed whitespace-pre-wrap select-text">
          {loading ? 'Compiling analysis report...' : markdown}
        </div>
      </div>
    </div>
  );
};
