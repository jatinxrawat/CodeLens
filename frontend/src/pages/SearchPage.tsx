import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Search,
  Sliders,
  Sparkles,
  Layers,
  FileCode,
  ExternalLink,
  Copy,
  Check,
  Clock,
  Code2,
  ShieldCheck,
  MessageSquareCode,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { SearchResponse, SearchMode, SearchResultItem, AskResponse } from '../types';
import { executeSearch, askCodebase } from '../services/api';

interface SearchPageProps {
  selectedRepo: string;
  initialQuery?: string;
  onOpenFileInExplorer: (filePath: string) => void;
}

export const SearchPage: React.FC<SearchPageProps> = ({
  selectedRepo,
  initialQuery = '',
  onOpenFileInExplorer,
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [mode, setMode] = useState<SearchMode>('hybrid');
  const [alpha, setAlpha] = useState(0.6);
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [reasoningAnswer, setReasoningAnswer] = useState<AskResponse | null>(null);
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      setQuery(initialQuery);
      performSearch(initialQuery, mode, alpha, topK);
    }
  }, [initialQuery, selectedRepo]);

  const performSearch = async (
    q: string,
    currentMode: SearchMode,
    currentAlpha: number,
    currentTopK: number
  ) => {
    if (!q.trim() || !selectedRepo) return;
    setLoading(true);
    setError(null);
    setReasoningAnswer(null);
    try {
      const resp = await executeSearch(selectedRepo, q.trim(), currentTopK, currentMode, currentAlpha);
      setSearchResponse(resp);

      // Concurrently fetch evidence-grounded summary answer
      setLoadingAnswer(true);
      try {
        const ans = await askCodebase(selectedRepo, q.trim(), currentTopK);
        setReasoningAnswer(ans);
      } catch {
        // Non-fatal if RAG summary fails
      } finally {
        setLoadingAnswer(false);
      }
    } catch (err: any) {
      setError(err.message || 'Search execution failed');
      setSearchResponse(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query, mode, alpha, topK);
  };

  const handleCopyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Search Controls Card */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
        <form onSubmit={handleSubmit} className="relative">
          <Search className="w-5 h-5 text-[#8b949e] absolute left-3.5 top-3.5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter question, concept, or code symbol (e.g. 'Where is user login and password authentication handled?')..."
            className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg pl-11 pr-28 py-3 text-sm text-[#e6edf3] placeholder-[#8b949e] focus:outline-none focus:border-[#58a6ff] font-mono shadow-inner"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 top-2 px-4 py-1.5 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white rounded-md text-xs font-medium transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {/* Search Parameter Controls */}
        <div className="pt-3 border-t border-[#30363d] flex flex-wrap items-center justify-between gap-4 text-xs">
          {/* Mode Switcher */}
          <div className="flex items-center space-x-2">
            <span className="text-[#8b949e] font-medium">Mode:</span>
            <div className="bg-[#0d1117] border border-[#30363d] p-0.5 rounded-md flex">
              {(['hybrid', 'vector', 'keyword'] as SearchMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => {
                    setMode(m);
                    if (query.trim()) performSearch(query, m, alpha, topK);
                  }}
                  className={`px-2.5 py-1 rounded text-xs font-mono capitalize transition-colors ${
                    mode === m
                      ? 'bg-[#1f6feb] text-white font-medium shadow-sm'
                      : 'text-[#8b949e] hover:text-[#e6edf3]'
                  }`}
                >
                  {m === 'hybrid' ? 'Hybrid (BM25 + FAISS)' : m === 'vector' ? 'Vector (Dense)' : 'Keyword (BM25)'}
                </button>
              ))}
            </div>
          </div>

          {/* Alpha Slider (visible on Hybrid mode) */}
          {mode === 'hybrid' && (
            <div className="flex items-center space-x-2.5 bg-[#0d1117] border border-[#30363d] px-3 py-1 rounded-md">
              <Sliders className="w-3.5 h-3.5 text-[#8b949e]" />
              <span className="text-[#8b949e] font-mono text-[11px]">
                α = <strong className="text-[#e6edf3]">{alpha.toFixed(2)}</strong> ({Math.round(alpha * 100)}% Dense + {Math.round((1 - alpha) * 100)}% BM25)
              </span>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={alpha}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setAlpha(val);
                  if (query.trim()) performSearch(query, mode, val, topK);
                }}
                className="w-24 accent-[#1f6feb] cursor-pointer"
              />
            </div>
          )}

          {/* Top-K Selector */}
          <div className="flex items-center space-x-2">
            <span className="text-[#8b949e] font-medium">Top K:</span>
            <select
              value={topK}
              onChange={(e) => {
                const k = parseInt(e.target.value, 10);
                setTopK(k);
                if (query.trim()) performSearch(query, mode, alpha, k);
              }}
              className="bg-[#0d1117] border border-[#30363d] text-[#e6edf3] px-2 py-1 rounded text-xs font-mono focus:outline-none"
            >
              <option value="3">3</option>
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="20">20</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Grounded AI Reasoning Answer & Summary Card */}
      {(loadingAnswer || reasoningAnswer) && (
        <div className="bg-[#161b22] border border-[#1f6feb]/40 rounded-xl p-5 shadow-sm space-y-3 bg-gradient-to-b from-[#1f6feb]/5 to-transparent">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#30363d]">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-[#58a6ff]" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#58a6ff]">
                Evidence-Grounded Code Summary
              </h3>
              {reasoningAnswer && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0d1117] text-[#8b949e] border border-[#30363d]">
                  Intent: {reasoningAnswer.category}
                </span>
              )}
            </div>

            {reasoningAnswer && (
              <div className="flex items-center space-x-2">
                <span
                  className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${
                    reasoningAnswer.confidence_level === 'HIGH'
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : reasoningAnswer.confidence_level === 'MEDIUM'
                      ? 'bg-amber-950 text-amber-400 border border-amber-800'
                      : 'bg-red-950 text-red-400 border border-red-800'
                  }`}
                >
                  {reasoningAnswer.confidence_level} Confidence ({Math.round(reasoningAnswer.confidence_score * 100)}%)
                </span>
              </div>
            )}
          </div>

          {loadingAnswer ? (
            <div className="py-4 flex items-center space-x-2 text-xs text-[#8b949e] font-mono animate-pulse">
              <div className="w-2 h-2 rounded-full bg-[#58a6ff] animate-ping"></div>
              <span>Synthesizing deep grounded explanation from retrieved AST chunks...</span>
            </div>
          ) : (
            reasoningAnswer && (
              <div className="space-y-3">
                <div className="space-y-3 text-xs text-[#e6edf3] leading-relaxed font-sans bg-[#0d1117] p-5 rounded-xl border border-[#30363d]">
                  <ReactMarkdown
                    components={{
                      h3: ({ children }) => (
                        <div className="pt-3 pb-1 border-b border-[#30363d]/60 first:pt-0 first:border-0">
                          <h4 className="text-xs font-bold text-[#58a6ff] flex items-center space-x-1.5">
                            <span>{children}</span>
                          </h4>
                        </div>
                      ),
                      h4: ({ children }) => (
                        <h5 className="text-[11px] font-bold text-[#79c0ff] pt-2">{children}</h5>
                      ),
                      p: ({ children }) => (
                        <p className="text-xs text-[#e6edf3] leading-relaxed my-2">{children}</p>
                      ),
                      blockquote: ({ children }) => (
                        <blockquote className="pl-3.5 border-l-2 border-[#58a6ff] text-xs italic text-[#8b949e] bg-[#161b22]/70 py-1.5 my-2 rounded-r">
                          {children}
                        </blockquote>
                      ),
                      ul: ({ children }) => (
                        <ul className="space-y-1.5 text-xs text-[#e6edf3] my-2 pl-1">{children}</ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="space-y-1.5 text-xs text-[#e6edf3] my-2 pl-1">{children}</ol>
                      ),
                      li: ({ children }) => (
                        <li className="text-xs text-[#e6edf3] leading-relaxed flex items-start space-x-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-[#58a6ff] mt-1.5 shrink-0" />
                          <div>{children}</div>
                        </li>
                      ),
                      strong: ({ children }) => (
                        <strong className="text-white font-semibold">{children}</strong>
                      ),
                      code: ({ inline, className, children, ...props }: any) => {
                        if (inline) {
                          return (
                            <code
                              className="px-1.5 py-0.5 rounded bg-[#161b22] text-emerald-300 font-mono text-[11px] border border-[#30363d]"
                              {...props}
                            >
                              {children}
                            </code>
                          );
                        }
                        const codeText = String(children).replace(/\n$/, '');
                        const lang = className ? className.replace('language-', '') : '';
                        return (
                          <div className="my-2 rounded-lg overflow-hidden border border-[#30363d] bg-[#090d13]">
                            <div className="px-3 py-1 bg-[#161b22] border-b border-[#30363d] text-[10px] font-mono text-emerald-400 font-semibold uppercase">
                              {lang || 'CODE'}
                            </div>
                            <pre className="p-3 text-[11px] font-mono text-[#e6edf3] overflow-x-auto leading-relaxed max-h-64">
                              <code>{codeText}</code>
                            </pre>
                          </div>
                        );
                      },
                    }}
                  >
                    {reasoningAnswer.answer}
                  </ReactMarkdown>
                </div>

                {/* Reasoning Decision Factors */}
                {reasoningAnswer.reasoning_evidence && reasoningAnswer.reasoning_evidence.length > 0 && (
                  <div className="pt-2 border-t border-[#30363d]/60 space-y-1">
                    <span className="text-[10px] font-semibold text-[#8b949e] uppercase tracking-wider block">
                      Decision Factors & Evidence:
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
                      {reasoningAnswer.reasoning_evidence.map((factor: any, fIdx: number) => (
                        <div key={fIdx} className="text-[11px] text-[#8b949e] flex items-center space-x-1.5 font-mono">
                          <span className="text-emerald-400">✓</span>
                          <span className="truncate">
                            {typeof factor === 'string' ? factor : factor.description || factor.label}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          )}
        </div>
      )}

      {/* Search Results Summary Header */}
      {searchResponse && (
        <div className="flex items-center justify-between text-xs text-[#8b949e] px-1">
          <span>
            Found <strong className="text-[#e6edf3]">{searchResponse.total_results}</strong> relevant code chunk(s) using{' '}
            <strong className="text-[#58a6ff] capitalize">{searchResponse.mode}</strong> retrieval:
          </span>
          <span className="flex items-center space-x-1 font-mono text-[11px] bg-[#161b22] px-2 py-0.5 rounded border border-[#30363d]">
            <Clock className="w-3 h-3 text-amber-400" />
            <span>{searchResponse.latency_ms} ms</span>
          </span>
        </div>
      )}

      {/* Results List */}
      {searchResponse && (
        <div className="space-y-4">
          {searchResponse.results.length === 0 && (
            <div className="p-8 text-center text-[#8b949e] bg-[#161b22] border border-[#30363d] rounded-lg">
              No matching code chunks found for this query. Try lowering alpha or using keyword terms.
            </div>
          )}

          {searchResponse.results.map((item: SearchResultItem, idx: number) => {
            const cardId = `chunk_${idx}`;
            return (
              <div
                key={cardId}
                className="bg-[#161b22] border border-[#30363d] hover:border-[#484f58] rounded-xl overflow-hidden shadow-sm transition-all"
              >
                {/* Result Card Header */}
                <div className="px-4 py-3 bg-[#0d1117]/60 border-b border-[#30363d] flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-5 h-5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center justify-center text-[10px] font-bold font-mono">
                      #{item.rank}
                    </span>
                    <span
                      className="font-mono text-xs font-semibold text-[#58a6ff] hover:underline cursor-pointer"
                      onClick={() => onOpenFileInExplorer(item.file_path)}
                    >
                      {item.file_path}
                    </span>
                    <span className="text-[11px] text-[#8b949e] font-mono">
                      (Lines {item.start_line}–{item.end_line})
                    </span>
                    {item.symbol && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-[#1f6feb]/15 text-[#58a6ff] border border-[#1f6feb]/30">
                        {item.chunk_type}: {item.symbol}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-mono bg-[#161b22] border border-[#30363d] px-2 py-0.5 rounded text-emerald-400">
                      Score: {(item.similarity * 100).toFixed(1)}%
                    </span>
                    <button
                      onClick={() => handleCopyCode(item.code, cardId)}
                      className="p-1 text-[#8b949e] hover:text-[#e6edf3] rounded hover:bg-[#21262d] transition-colors"
                      title="Copy code snippet"
                    >
                      {copiedId === cardId ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={() => onOpenFileInExplorer(item.file_path)}
                      className="flex items-center space-x-1 px-2 py-1 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] rounded text-[11px] font-medium transition-colors"
                    >
                      <span>View File</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>

                {/* Docstring if present */}
                {item.docstring && (
                  <div className="px-4 py-2 bg-[#161b22] text-xs text-[#8b949e] italic border-b border-[#30363d]/50">
                    "{item.docstring}"
                  </div>
                )}

                {/* Code Content with Line Numbers */}
                <div className="p-4 bg-[#0d1117] overflow-x-auto text-xs font-mono text-[#e6edf3] leading-relaxed">
                  <pre>
                    {item.code.split('\n').map((line, lineIdx) => {
                      const currentLineNum = item.start_line + lineIdx;
                      return (
                        <div key={lineIdx} className="table-row hover:bg-[#161b22]">
                          <span className="table-cell select-none text-[#8b949e] pr-4 text-right opacity-60 w-8">
                            {currentLineNum}
                          </span>
                          <span className="table-cell whitespace-pre">{line}</span>
                        </div>
                      );
                    })}
                  </pre>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
