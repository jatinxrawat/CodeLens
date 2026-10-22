import React, { useState, useEffect } from 'react';
import {
  FileCode,
  Folder,
  ChevronRight,
  ChevronDown,
  Copy,
  Check,
  Code2,
  Layers,
  Search,
  Workflow,
  ArrowRight,
  ArrowDown,
  ArrowLeft,
  X,
  ExternalLink,
  Play,
  Loader2,
  Sparkles,
} from 'lucide-react';
import type { FileItem, FileContent, FunctionFlowResult, FlowStep } from '../types';
import { fetchRepositoryFiles, fetchFileContent, fetchFunctionFlow } from '../services/api';

interface ExplorerPageProps {
  selectedRepo: string;
  initialFilePath?: string;
  initialFlowSymbol?: string;
}

export const ExplorerPage: React.FC<ExplorerPageProps> = ({
  selectedRepo,
  initialFilePath,
  initialFlowSymbol,
}) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [loadingContent, setLoadingContent] = useState(false);
  const [copied, setCopied] = useState(false);

  // Function Flow State
  const [activeFlowSymbol, setActiveFlowSymbol] = useState<string | null>(initialFlowSymbol || null);
  const [flowResult, setFlowResult] = useState<FunctionFlowResult | null>(null);
  const [loadingFlow, setLoadingFlow] = useState(false);
  const [flowError, setFlowError] = useState<string | null>(null);
  const [manualSymbolInput, setManualSymbolInput] = useState('');

  useEffect(() => {
    if (!selectedRepo) return;
    setLoadingFiles(true);
    fetchRepositoryFiles(selectedRepo)
      .then((items) => {
        setFiles(items);
        const target = initialFilePath || (items.length > 0 ? items[0].path : null);
        if (target) {
          setSelectedFile(target);
        }
      })
      .catch((err) => console.error('Failed to load files:', err))
      .finally(() => setLoadingFiles(false));
  }, [selectedRepo]);

  useEffect(() => {
    if (!selectedRepo || !selectedFile) return;
    setLoadingContent(true);
    fetchFileContent(selectedRepo, selectedFile)
      .then(setFileContent)
      .catch((err) => console.error('Failed to load file content:', err))
      .finally(() => setLoadingContent(false));
  }, [selectedRepo, selectedFile]);

  // Trigger flow if initialFlowSymbol is passed
  useEffect(() => {
    if (initialFlowSymbol && selectedRepo) {
      handleTraceFlow(initialFlowSymbol);
    }
  }, [initialFlowSymbol, selectedRepo]);

  const handleTraceFlow = async (sym: string, filePath?: string) => {
    const symbolToTrace = sym.trim();
    if (!symbolToTrace || !selectedRepo) return;

    setActiveFlowSymbol(symbolToTrace);
    setLoadingFlow(true);
    setFlowError(null);

    try {
      const res = await fetchFunctionFlow(selectedRepo, symbolToTrace, filePath || selectedFile || undefined);
      setFlowResult(res);
    } catch (err: any) {
      console.error('Failed to trace function flow:', err);
      setFlowError(err.message || `No static call pathways found for ${symbolToTrace}`);
      setFlowResult(null);
    } finally {
      setLoadingFlow(false);
    }
  };

  const handleCopy = () => {
    if (fileContent?.code) {
      navigator.clipboard.writeText(fileContent.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const filteredFiles = files.filter((f) =>
    f.path.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const activeFileInfo = files.find((f) => f.path === selectedFile);

  return (
    <div className="flex h-[calc(100vh-3.5rem)] bg-[#0d0d12] text-[#ececec] overflow-hidden select-none">
      {/* File Tree Left Sidebar */}
      <div className="w-72 bg-[#121218] border-r border-[#222230] flex flex-col shrink-0">
        <div className="p-3 border-b border-[#222230]">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#71717a] absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search repository files..."
              className="w-full bg-[#181822] border border-[#2b2b3d] rounded-xl pl-8 pr-2.5 py-1.5 text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-sky-500 font-mono"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {loadingFiles && (
            <div className="p-6 text-center text-xs text-[#a1a1aa] flex items-center justify-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
              <span>Loading repository tree...</span>
            </div>
          )}

          {!loadingFiles &&
            filteredFiles.map((file) => {
              const isSelected = selectedFile === file.path;
              return (
                <button
                  key={file.path}
                  onClick={() => setSelectedFile(file.path)}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-colors text-left cursor-pointer ${
                    isSelected
                      ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                      : 'text-[#a1a1aa] hover:text-white hover:bg-[#181824]'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate pr-2">
                    <FileCode className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-sky-400' : 'text-[#71717a]'}`} />
                    <span className="truncate">{file.path}</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#181824] text-[#71717a] shrink-0 font-mono">
                    {file.total_chunks}
                  </span>
                </button>
              );
            })}
        </div>
      </div>

      {/* Main Code Viewer & Editor Canvas */}
      <div className="flex-1 flex flex-col bg-[#0f0f14] overflow-hidden">
        {selectedFile && (
          <div className="h-11 bg-[#15151e] border-b border-[#222230] px-4 flex items-center justify-between shrink-0">
            <div className="flex items-center space-x-2.5 font-mono text-xs text-white">
              <FileCode className="w-4 h-4 text-emerald-400" />
              <span className="font-semibold">{selectedFile}</span>
              {fileContent && (
                <span className="text-[#71717a] text-[11px]">
                  ({fileContent.total_lines} lines • {fileContent.language})
                </span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {activeFlowSymbol && (
                <button
                  onClick={() => setActiveFlowSymbol(null)}
                  className="flex items-center space-x-1 px-2.5 py-1 bg-indigo-950/40 text-indigo-300 border border-indigo-800/40 hover:bg-indigo-900/50 rounded-lg text-xs transition-colors cursor-pointer"
                >
                  <Workflow className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Viewing Flow: {activeFlowSymbol}</span>
                  <X className="w-3 h-3 ml-1 text-indigo-400" />
                </button>
              )}

              <button
                onClick={handleCopy}
                className="flex items-center space-x-1.5 px-2.5 py-1 bg-[#1f1f2c] hover:bg-[#28283a] text-white rounded-lg text-xs transition-colors cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-[#a1a1aa]" />}
                <span>{copied ? 'Copied' : 'Copy Code'}</span>
              </button>
            </div>
          </div>
        )}

        <div className="flex-1 flex overflow-hidden">
          {/* Source Code Line View */}
          <div className="flex-1 overflow-auto p-4 font-mono text-xs text-white bg-[#0f0f14] leading-relaxed select-text">
            {loadingContent && (
              <div className="p-8 text-center text-[#71717a]">Loading file content...</div>
            )}
            {!loadingContent && fileContent && (
              <pre className="table w-full">
                {fileContent.code.split('\n').map((line, idx) => (
                  <div key={idx} className="table-row hover:bg-[#181824]/60">
                    <span className="table-cell select-none text-[#71717a] pr-4 text-right opacity-50 w-10">
                      {idx + 1}
                    </span>
                    <span className="table-cell whitespace-pre">{line}</span>
                  </div>
                ))}
              </pre>
            )}
          </div>

          {/* ================= RIGHT PANEL: AST SYMBOLS & FUNCTION FLOW TRACER ================= */}
          <div className="w-80 bg-[#14141c] border-l border-[#222230] flex flex-col shrink-0 overflow-hidden">
            {/* Quick Flow Tracer Search Input */}
            <div className="p-3 border-b border-[#222230] bg-[#121218]">
              <div className="flex items-center space-x-1.5">
                <div className="relative flex-1">
                  <Workflow className="w-3.5 h-3.5 text-sky-400 absolute left-2.5 top-2.5" />
                  <input
                    type="text"
                    value={manualSymbolInput}
                    onChange={(e) => setManualSymbolInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && manualSymbolInput.trim()) {
                        handleTraceFlow(manualSymbolInput.trim());
                      }
                    }}
                    placeholder="Trace function flow..."
                    className="w-full bg-[#191924] border border-[#2b2b3d] rounded-xl pl-8 pr-2.5 py-1.5 text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
                <button
                  onClick={() => manualSymbolInput.trim() && handleTraceFlow(manualSymbolInput.trim())}
                  disabled={!manualSymbolInput.trim()}
                  className="px-2.5 py-1.5 rounded-xl bg-sky-500 hover:bg-sky-400 disabled:opacity-40 text-white text-xs font-semibold cursor-pointer"
                  title="Trace function flow"
                >
                  <Play className="w-3 h-3 fill-current" />
                </button>
              </div>
            </div>

            {/* Content: Active Flow Results vs Symbols List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {activeFlowSymbol ? (
                /* Function Call Flow View */
                <div className="space-y-4 animate-in fade-in duration-200">
                  <div className="flex items-center justify-between pb-2 border-b border-[#242434]">
                    <div className="flex items-center space-x-2">
                      <Workflow className="w-4 h-4 text-sky-400" />
                      <h4 className="text-xs font-bold text-white font-mono">{activeFlowSymbol}()</h4>
                    </div>
                    <button
                      onClick={() => setActiveFlowSymbol(null)}
                      className="text-xs text-[#a1a1aa] hover:text-white cursor-pointer px-1.5 py-0.5 rounded bg-[#1e1e2a]"
                    >
                      Close Flow
                    </button>
                  </div>

                  {loadingFlow && (
                    <div className="p-6 text-center text-xs text-[#a1a1aa] flex items-center justify-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
                      <span>Tracing static AST call hierarchy...</span>
                    </div>
                  )}

                  {flowError && (
                    <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/40 text-rose-300 text-xs">
                      {flowError}
                    </div>
                  )}

                  {flowResult && (
                    <div className="space-y-4 text-xs font-mono">
                      {/* Flow Metrics Pill */}
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-[#181824] p-2 rounded-xl border border-[#272738]">
                          <span className="text-[10px] text-[#71717a] block">Callers</span>
                          <span className="text-sm font-bold text-sky-400">{flowResult.callers?.length || 0}</span>
                        </div>
                        <div className="bg-[#181824] p-2 rounded-xl border border-[#272738]">
                          <span className="text-[10px] text-[#71717a] block">Callees</span>
                          <span className="text-sm font-bold text-emerald-400">{flowResult.callees?.length || 0}</span>
                        </div>
                        <div className="bg-[#181824] p-2 rounded-xl border border-[#272738]">
                          <span className="text-[10px] text-[#71717a] block">Flow Steps</span>
                          <span className="text-sm font-bold text-purple-400">{flowResult.flow_steps?.length || 1}</span>
                        </div>
                      </div>

                      {/* 1. Inbound Callers */}
                      <div className="space-y-1.5">
                        <span className="text-[10px] uppercase font-bold text-[#71717a] tracking-wider block">
                          ↑ Inbound Callers
                        </span>
                        {flowResult.callers && flowResult.callers.length > 0 ? (
                          flowResult.callers.map((c, i) => (
                            <div
                              key={i}
                              className="p-2 rounded-xl bg-[#191925] border border-[#2b2b3d] hover:border-sky-500/50 flex items-center justify-between"
                            >
                              <div>
                                <span className="font-semibold text-sky-300">{c.symbol}()</span>
                                <p className="text-[10px] text-[#71717a] truncate">{c.file_path}</p>
                              </div>
                              <button
                                onClick={() => handleTraceFlow(c.symbol, c.file_path)}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-[#242436] text-sky-400 hover:bg-sky-900/50 cursor-pointer"
                                title="Trace this caller"
                              >
                                Trace →
                              </button>
                            </div>
                          ))
                        ) : (
                          <div className="p-2 rounded-lg bg-[#181824] text-[11px] text-[#71717a] italic">
                            Root entrypoint or unreferenced
                          </div>
                        )}
                      </div>

                      {/* Central Target Function Highlight */}
                      <div className="p-2.5 rounded-xl bg-gradient-to-r from-sky-950/60 to-indigo-950/60 border border-sky-500/50 text-center font-bold text-white shadow-sm">
                        <span className="text-[10px] text-sky-400 block uppercase font-mono tracking-widest">
                          Target Function
                        </span>
                        <span>{activeFlowSymbol}()</span>
                      </div>

                      {/* 2. Outbound Callees */}
                      <div className="space-y-1.5">
                        <span className="text-[10px] uppercase font-bold text-[#71717a] tracking-wider block">
                          ↓ Outbound Callees
                        </span>
                        {flowResult.callees && flowResult.callees.length > 0 ? (
                          flowResult.callees.map((c, i) => (
                            <div
                              key={i}
                              className="p-2 rounded-xl bg-[#191925] border border-[#2b2b3d] hover:border-emerald-500/50 flex items-center justify-between"
                            >
                              <div>
                                <span className="font-semibold text-emerald-300">{c.symbol}()</span>
                                <p className="text-[10px] text-[#71717a] truncate">{c.file_path}</p>
                              </div>
                              <button
                                onClick={() => handleTraceFlow(c.symbol, c.file_path)}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-[#242436] text-emerald-400 hover:bg-emerald-900/50 cursor-pointer"
                                title="Trace this callee"
                              >
                                Trace →
                              </button>
                            </div>
                          ))
                        ) : (
                          <div className="p-2 rounded-lg bg-[#181824] text-[11px] text-[#71717a] italic">
                            Leaf routine (no sub-calls detected)
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* Standard Detected Symbols Outline */
                <div className="space-y-2">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-[11px] font-semibold text-[#a1a1aa] uppercase tracking-wider flex items-center space-x-1.5">
                      <Code2 className="w-3.5 h-3.5 text-sky-400" />
                      <span>AST Symbols ({activeFileInfo?.symbols.length || 0})</span>
                    </h4>
                    <span className="text-[10px] text-[#71717a]">Click symbol to trace</span>
                  </div>

                  {activeFileInfo && activeFileInfo.symbols.length > 0 ? (
                    activeFileInfo.symbols.map((sym, idx) => {
                      const isFunc = sym.type.toLowerCase().includes('function') || sym.type.toLowerCase().includes('method');
                      return (
                        <div
                          key={idx}
                          onClick={() => handleTraceFlow(sym.symbol)}
                          className="p-2.5 rounded-xl bg-[#181824] hover:bg-[#202030] border border-[#28283a] hover:border-sky-500/40 text-xs font-mono space-y-1 transition-all cursor-pointer group"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-white font-medium truncate group-hover:text-sky-400">
                              {sym.symbol}
                            </span>
                            <span className="text-[10px] text-sky-400 bg-sky-950/60 px-1.5 py-0.2 rounded font-mono">
                              {sym.type}
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-[10px] text-[#71717a]">
                            <span>L{sym.start_line}–{sym.end_line}</span>
                            <span className="text-sky-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-0.5">
                              <span>Trace flow</span>
                              <ArrowRight className="w-3 h-3" />
                            </span>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-6 text-center text-xs text-[#71717a]">
                      No AST symbols extracted in this file. Select another file from the left tree.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
