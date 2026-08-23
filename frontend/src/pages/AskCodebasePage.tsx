import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  MessageSquareCode,
  Sparkles,
  ExternalLink,
  Clock,
  HelpCircle,
  Code2,
  Copy,
  Check,
  AlertTriangle,
  FileCode2,
  Cpu,
  Layers,
  ArrowRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import type { AskResponse, CitationSource, DecisionFactor } from '../types';
import { askCodebase } from '../services/api';

interface AskCodebasePageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
}

const CodeBlockWithCopy: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => {
  const [copied, setCopied] = useState(false);
  const codeText = String(children).replace(/\n$/, '');
  const language = className ? className.replace('language-', '') : '';

  const handleCopy = () => {
    navigator.clipboard.writeText(codeText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-4 rounded-xl overflow-hidden border border-[#30363d] bg-[#0d1117] shadow-lg">
      <div className="flex items-center justify-between px-4 py-2 bg-[#161b22] border-b border-[#30363d] text-xs font-mono">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1.5 mr-2">
            <div className="w-2.5 h-2.5 rounded-full bg-[#f85149]/70" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#d29922]/70" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#3fb950]/70" />
          </div>
          <span className="text-emerald-400 font-semibold uppercase">{language || 'CODE'}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#21262d] hover:bg-[#30363d] text-[#8b949e] hover:text-white transition-all text-[11px] cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy snippet</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-xs font-mono text-[#e6edf3] overflow-x-auto leading-relaxed max-h-96">
        <code>{codeText}</code>
      </pre>
    </div>
  );
};

export const AskCodebasePage: React.FC<AskCodebasePageProps> = ({
  selectedRepo,
  onOpenFileInExplorer,
}) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const exampleQuestions = [
    'How is user authentication and login handled?',
    'What happens when a payment transaction is processed?',
    'Where is the LRU cache eviction logic implemented?',
    'Explain the architecture and main layers of this repository.',
    'Are there any potential security or credential risks in the codebase?',
  ];

  const handleAsk = async (qText: string) => {
    if (!qText.trim() || !selectedRepo) return;
    setQuery(qText);
    setLoading(true);
    setError(null);
    try {
      const res = await askCodebase(selectedRepo, qText);
      setResponse(res);
    } catch (err: any) {
      setError(err?.message || 'Failed to get answer from local intelligence engine.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto pb-16">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#30363d] pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-[#1f6feb]/20 to-[#388bfd]/10 text-[#58a6ff] border border-[#1f6feb]/40 shadow-inner">
            <MessageSquareCode className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center space-x-2.5">
              <span>Ask Codebase (RAG)</span>
              <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-700/60 font-mono flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3 inline mr-1" />
                <span>100% Offline AI</span>
              </span>
            </h1>
            <p className="text-xs text-[#8b949e] mt-0.5">
              Ask natural language architectural or execution questions grounded in multi-language AST code chunks.
            </p>
          </div>
        </div>
      </div>

      {/* Query Input Card */}
      <div className="p-5 rounded-2xl bg-gradient-to-b from-[#161b22] to-[#0d1117] border border-[#30363d] shadow-xl space-y-3">
        <div className="flex items-center space-x-3">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder={
                selectedRepo
                  ? `Ask a question about ${selectedRepo}...`
                  : 'Select a repository first...'
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk(query)}
              disabled={!selectedRepo || loading}
              className="w-full pl-11 pr-4 py-3 bg-[#0d1117] border border-[#30363d] rounded-xl text-sm text-white placeholder-[#8b949e] focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] transition-all shadow-inner"
            />
            <HelpCircle className="w-5 h-5 text-[#8b949e] absolute left-3.5 top-3.5" />
          </div>
          <button
            onClick={() => handleAsk(query)}
            disabled={!selectedRepo || loading || !query.trim()}
            className="px-6 py-3 bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white font-medium text-sm rounded-xl flex items-center space-x-2 transition-all shadow-md cursor-pointer hover:shadow-emerald-950/30"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Reasoning...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-emerald-300" />
                <span>Ask Engine</span>
              </>
            )}
          </button>
        </div>

        {/* Example prompts */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1.5">
          <span className="text-[11px] text-[#8b949e] font-mono mr-1 flex items-center">
            <Zap className="w-3 h-3 text-amber-400 mr-1" /> Try:
          </span>
          {exampleQuestions.map((eq, i) => (
            <button
              key={i}
              onClick={() => {
                setQuery(eq);
                handleAsk(eq);
              }}
              disabled={!selectedRepo || loading}
              className="text-[11px] px-3 py-1 rounded-lg bg-[#161b22] border border-[#30363d] text-[#58a6ff] hover:border-[#58a6ff]/60 hover:bg-[#1f6feb]/15 transition-all cursor-pointer text-left shadow-sm"
            >
              {eq}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/80 text-xs text-red-300 flex items-center space-x-3 shadow-md">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Answer Container */}
      {response && (
        <div className="space-y-6 animate-fadeIn">
          {/* Main Answer Header & Metadata */}
          <div className="p-6 rounded-2xl bg-[#161b22] border border-[#30363d] space-y-5 shadow-2xl">
            {/* Top Bar */}
            <div className="flex items-center justify-between border-b border-[#30363d] pb-4">
              <div className="flex items-center space-x-3">
                <span className="text-xs font-mono px-3 py-1 rounded-lg bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/40 font-semibold shadow-sm">
                  {response.category}
                </span>
                <span
                  className={`text-xs font-mono px-3 py-1 rounded-lg border font-medium ${
                    response.confidence_level === 'HIGH'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                      : response.confidence_level === 'MEDIUM'
                      ? 'bg-blue-950 text-blue-400 border-blue-800'
                      : response.confidence_level === 'LOW'
                      ? 'bg-amber-950 text-amber-400 border-amber-800'
                      : 'bg-red-950 text-red-400 border-red-800'
                  }`}
                >
                  Confidence: {response.confidence_level} ({(response.confidence_score * 100).toFixed(0)}%)
                </span>
              </div>
              <span className="text-xs font-mono text-[#8b949e] flex items-center space-x-1.5 bg-[#0d1117] px-3 py-1 rounded-lg border border-[#30363d]">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span>{response.latency_ms} ms</span>
              </span>
            </div>

            {/* Formatted Markdown Answer with Rich Card Aesthetics */}
            <div className="text-xs text-[#e6edf3] leading-relaxed font-sans bg-[#0d1117] p-6 rounded-xl border border-[#30363d] space-y-4">
              <ReactMarkdown
                components={{
                  h3: ({ children }) => (
                    <div className="pt-4 pb-2 border-b border-[#30363d]/60 first:pt-0 first:border-0">
                      <h3 className="text-sm font-bold text-[#58a6ff] flex items-center space-x-2">
                        <span>{children}</span>
                      </h3>
                    </div>
                  ),
                  h4: ({ children }) => (
                    <h4 className="text-xs font-bold text-[#79c0ff] pt-3 pb-1">{children}</h4>
                  ),
                  p: ({ children }) => (
                    <p className="text-xs text-[#e6edf3] leading-relaxed my-2.5">{children}</p>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="pl-4 border-l-3 border-[#58a6ff] text-xs italic text-[#8b949e] bg-[#161b22]/80 py-2 my-3 rounded-r-lg">
                      {children}
                    </blockquote>
                  ),
                  ul: ({ children }) => (
                    <ul className="space-y-2 text-xs text-[#e6edf3] my-3 pl-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="space-y-2 text-xs text-[#e6edf3] my-3 pl-1">{children}</ol>
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
                  a: ({ href, children }) => (
                    <span className="text-[#58a6ff] hover:underline font-mono inline-flex items-center space-x-1 cursor-pointer">
                      <span>{children}</span>
                    </span>
                  ),
                  code: ({ inline, className, children, ...props }: any) => {
                    if (inline) {
                      return (
                        <code
                          className="px-2 py-0.5 rounded-md bg-[#161b22] text-emerald-300 font-mono text-[11px] border border-[#30363d]"
                          {...props}
                        >
                          {children}
                        </code>
                      );
                    }
                    return (
                      <CodeBlockWithCopy className={className}>
                        {children}
                      </CodeBlockWithCopy>
                    );
                  },
                }}
              >
                {response.answer}
              </ReactMarkdown>
            </div>

            {/* Reasoning Evidence & Decision Factors */}
            {response.reasoning_evidence.length > 0 && (
              <div className="pt-4 border-t border-[#30363d] space-y-3">
                <h4 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-[#58a6ff]" />
                  <span>Explainability: Decision Factors</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {response.reasoning_evidence.map((df: DecisionFactor, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-[#0d1117] border border-[#30363d] text-xs font-mono space-y-1 shadow-sm"
                    >
                      <div className="text-[#58a6ff] font-semibold flex items-center space-x-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                        <span>{df.label}</span>
                      </div>
                      <div className="text-[11px] text-[#8b949e] pl-4">{df.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Grounded Citations Cards */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b949e] flex items-center space-x-2">
                <Code2 className="w-4 h-4 text-emerald-400" />
                <span>Grounded Evidence Citations ({response.sources.length} Sources)</span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {response.sources.map((src: CitationSource, idx: number) => (
                <div
                  key={`${src.file_path}-${src.start_line}-${idx}`}
                  className="p-5 rounded-2xl bg-[#161b22] border border-[#30363d] space-y-3 hover:border-[#58a6ff]/50 transition-all shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2.5">
                      <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
                        #{idx + 1}
                      </span>
                      <span className="text-xs font-mono font-semibold text-[#58a6ff] truncate max-w-[240px]">
                        {src.file_path}
                      </span>
                    </div>
                    <button
                      onClick={() => onOpenFileInExplorer(src.file_path)}
                      className="text-xs font-mono text-[#8b949e] hover:text-white flex items-center space-x-1.5 bg-[#0d1117] px-2.5 py-1 rounded-lg border border-[#30363d] cursor-pointer transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Inspect</span>
                    </button>
                  </div>

                  <div className="flex items-center space-x-2 text-[11px] font-mono text-[#8b949e]">
                    <span>Lines {src.start_line}–{src.end_line}</span>
                    {src.symbol_name && (
                      <span className="px-2 py-0.5 rounded bg-blue-950/80 text-[#58a6ff] border border-blue-800/60">
                        {src.chunk_type}: {src.symbol_name}
                      </span>
                    )}
                    <span className="text-emerald-400 font-semibold">
                      Match: {(src.similarity * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-[#0d1117] border border-[#30363d]/70 font-mono text-xs text-[#c9d1d9] overflow-x-auto max-h-40 shadow-inner">
                    <pre className="text-[11px] leading-relaxed">
                      <code>{src.code_preview}</code>
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
