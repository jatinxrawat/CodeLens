import React, { useState } from 'react';
import {
  Workflow,
  Search,
  ArrowRight,
  ArrowDown,
  FileCode,
  CheckCircle2,
  HelpCircle,
  ExternalLink,
} from 'lucide-react';
import type { FunctionFlowResult, FlowStep } from '../types';
import { fetchFunctionFlow } from '../services/api';

interface CodeFlowPageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
}

export const CodeFlowPage: React.FC<CodeFlowPageProps> = ({
  selectedRepo,
  onOpenFileInExplorer,
}) => {
  const [symbol, setSymbol] = useState('login_user');
  const [result, setResult] = useState<FunctionFlowResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTrace = async (sym: string) => {
    if (!sym.trim() || !selectedRepo) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchFunctionFlow(selectedRepo, sym.trim());
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to trace function flow');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleTrace(symbol);
  };

  const exampleSymbols = ['login_user', 'process_card_payment', 'allocate_buffer', 'LRUCache'];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[#e6edf3]">Static Code Flow & Call Graph Tracer</h1>
        <p className="text-xs text-[#8b949e] mt-0.5">
          Traces static caller and callee execution pathways across AST function and method invocations.
        </p>
      </div>

      {/* Target Symbol Form */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-3">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="flex-1 relative">
            <Workflow className="w-4 h-4 text-[#8b949e] absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="Enter function or method symbol name..."
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg pl-10 pr-4 py-2.5 text-xs text-[#e6edf3] placeholder-[#8b949e] focus:outline-none focus:border-[#58a6ff] font-mono shadow-inner"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !symbol.trim() || !selectedRepo}
            className="px-5 py-2.5 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors flex items-center space-x-2 shrink-0 shadow-sm"
          >
            <span>{loading ? 'Tracing...' : 'Trace Flow'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] text-[#8b949e] mr-1">Examples:</span>
          {exampleSymbols.map((sym) => (
            <button
              key={sym}
              type="button"
              onClick={() => {
                setSymbol(sym);
                handleTrace(sym);
              }}
              className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#0d1117] hover:bg-[#21262d] text-[#58a6ff] border border-[#30363d] transition-colors"
            >
              {sym}()
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Target Function Hero Card */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#8b949e]">
                Target Function / Symbol
              </span>
              <h2 className="text-base font-bold text-[#58a6ff] font-mono mt-0.5">
                {result.target_symbol}()
              </h2>
              <p className="text-xs text-[#8b949e] font-mono mt-1">
                Defined in: <span className="text-[#e6edf3]">{result.target_file}</span> (Line {result.target_line})
              </p>
            </div>

            <button
              onClick={() => onOpenFileInExplorer(result.target_file)}
              className="px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] rounded text-xs font-mono transition-colors flex items-center space-x-1.5"
            >
              <span>View Source</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* 3-Column Visual Call Graph (Callers -> Target -> Callees) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Callers Column */}
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 space-y-3">
              <h3 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between pb-2 border-b border-[#30363d]">
                <span>Callers ({result.callers.length})</span>
                <span className="text-[10px] text-blue-400 font-mono">Invokes target</span>
              </h3>

              {result.callers.length === 0 ? (
                <div className="p-4 text-center text-xs text-[#8b949e] italic">
                  No static callers detected in codebase.
                </div>
              ) : (
                <div className="space-y-2">
                  {result.callers.map((c, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded bg-[#0d1117] border border-[#30363d] text-xs font-mono space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[#58a6ff] font-bold">{c.symbol}()</span>
                        <span className="text-[10px] text-emerald-400 bg-emerald-950 px-1 rounded">
                          Confirmed
                        </span>
                      </div>
                      <div className="text-[11px] text-[#8b949e] truncate">
                        {c.file_path} (Line {c.start_line})
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Callees Column */}
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 space-y-3">
              <h3 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between pb-2 border-b border-[#30363d]">
                <span>Callees ({result.callees.length})</span>
                <span className="text-[10px] text-emerald-400 font-mono">Called by target</span>
              </h3>

              {result.callees.length === 0 ? (
                <div className="p-4 text-center text-xs text-[#8b949e] italic">
                  No outgoing function invocations in body.
                </div>
              ) : (
                <div className="space-y-2">
                  {result.callees.map((c, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded bg-[#0d1117] border border-[#30363d] text-xs font-mono space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-emerald-400 font-bold">{c.symbol}()</span>
                        <span
                          className={`text-[10px] px-1 rounded ${
                            c.relationship === 'confirmed_static'
                              ? 'text-emerald-400 bg-emerald-950'
                              : 'text-purple-400 bg-purple-950'
                          }`}
                        >
                          {c.relationship === 'confirmed_static' ? 'Internal' : 'Inferred / External'}
                        </span>
                      </div>
                      <div className="text-[11px] text-[#8b949e] truncate">
                        {c.file_path || 'External library or built-in'}
                      </div>
                    </div>
                  ))}
                </div>
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
