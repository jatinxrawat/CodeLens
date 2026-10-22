import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  ArrowUp,
  Search,
  Globe,
  Brain,
  Plus,
  Mic,
  MicOff,
  Copy,
  Check,
  ExternalLink,
  RotateCcw,
  Sparkles,
  ChevronDown,
  X,
  FileCode,
  ThumbsUp,
  ThumbsDown,
  Share2,
  SquarePen,
  Clock,
  Layers,
  GitBranch,
  FolderGit2,
  AlertCircle,
  Loader2,
  CheckCircle2,
} from 'lucide-react';
import type { SearchResponse, SearchMode, SearchResultItem, AskResponse, RepositorySummary, CitationSource } from '../types';
import { executeSearch, askCodebase, ingestRemoteRepository, fetchRepositoryStatus } from '../services/api';

interface ChatSearchPageProps {
  selectedRepo: string;
  repositories?: RepositorySummary[];
  onSelectRepo?: (repoId: string) => void;
  onRefreshRepositories?: () => Promise<void>;
  onOpenFileInExplorer: (filePath: string) => void;
  onNavigateToTab?: (tab: string) => void;
  initialSearchOnly?: boolean;
  initialQuery?: string;
}

interface ChatTurn {
  id: string;
  query: string;
  answer?: string;
  sources?: CitationSource[];
  searchResponse?: SearchResponse | null;
  latencyMs?: number;
  category?: string;
  confidenceLevel?: string;
  isGeneralAi?: boolean;
  repoUsed?: string;
  isLoading?: boolean;
  error?: string | null;
  feedback?: 'up' | 'down' | null;
  isSearchOnly?: boolean;
}

// Official GitHub SVG Icon
const GithubIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
    />
  </svg>
);

// CodeLens AI Official Icon
const CodeLensAIIcon: React.FC<{ className?: string }> = ({ className = 'w-7 h-7' }) => (
  <div
    className={`rounded-full bg-gradient-to-br from-sky-500 via-indigo-500 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-md ${className}`}
  >
    <Sparkles className="w-4 h-4 text-white" />
  </div>
);

const CodeBlock: React.FC<{ children: React.ReactNode; className?: string }> = ({
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
    <div className="my-3 rounded-xl overflow-hidden border border-[#383838] bg-[#141414] shadow-lg">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#1f1f1f] border-b border-[#333333] text-[11px] font-mono text-[#b4b4b4]">
        <span className="uppercase font-semibold tracking-wider text-sky-400">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-2 py-0.5 rounded hover:bg-[#2f2f2f] text-[#b4b4b4] hover:text-[#ececec] transition-colors cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy code</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-xs font-mono text-[#ececec] overflow-x-auto leading-relaxed max-h-96">
        <code>{codeText}</code>
      </pre>
    </div>
  );
};

export const ChatSearchPage: React.FC<ChatSearchPageProps> = ({
  selectedRepo,
  repositories = [],
  onSelectRepo,
  onRefreshRepositories,
  onOpenFileInExplorer,
  onNavigateToTab,
  initialSearchOnly = false,
  initialQuery = '',
}) => {
  const [inputQuery, setInputQuery] = useState(initialQuery || '');
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [isSearchOnly, setIsSearchOnly] = useState<boolean>(initialSearchOnly);
  const [isSearchActive, setIsSearchActive] = useState(true);
  const [isReasonActive, setIsReasonActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState('CodeLens AI');
  const [showSourcesPanel, setShowSourcesPanel] = useState(false);
  const [activeSources, setActiveSources] = useState<SearchResultItem[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Sync prop changes
  useEffect(() => {
    if (initialSearchOnly !== undefined) {
      setIsSearchOnly(initialSearchOnly);
    }
  }, [initialSearchOnly]);

  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      setInputQuery(initialQuery);
    }
  }, [initialQuery]);

  // GitHub Attachment Modal State
  const [isAttachModalOpen, setIsAttachModalOpen] = useState(false);
  const [gitUrlInput, setGitUrlInput] = useState('');
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestStatusStep, setIngestStatusStep] = useState<string>('');
  const [ingestProgress, setIngestProgress] = useState<number>(0);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [ingestSuccessRepo, setIngestSuccessRepo] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const bottomTextareaRef = useRef<HTMLTextAreaElement | null>(null);
  const chatScrollContainerRef = useRef<HTMLDivElement | null>(null);

  const adjustHeight = (el: HTMLTextAreaElement | null) => {
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  };

  useEffect(() => {
    adjustHeight(textareaRef.current);
    adjustHeight(bottomTextareaRef.current);
  }, [inputQuery]);

  // Auto-scroll to bottom on turns update
  useEffect(() => {
    if (chatScrollContainerRef.current) {
      chatScrollContainerRef.current.scrollTop = chatScrollContainerRef.current.scrollHeight;
    }
  }, [turns]);

  const handleSearch = async (queryText?: string) => {
    const q = (queryText !== undefined ? queryText : inputQuery).trim();
    if (!q) return;

    const turnId = Date.now().toString();
    const newTurn: ChatTurn = {
      id: turnId,
      query: q,
      isLoading: true,
      repoUsed: selectedRepo || 'General Mode',
      isSearchOnly: isSearchOnly,
    };

    setTurns((prev) => [...prev, newTurn]);
    setInputQuery('');

    // If Search Only toggle is active, execute fast hybrid code search without LLM essay
    if (isSearchOnly) {
      if (!selectedRepo) {
        setTurns((prev) =>
          prev.map((turn) => {
            if (turn.id !== turnId) return turn;
            return {
              ...turn,
              isLoading: false,
              error: 'Please attach or select a repository to search indexed code chunks.',
            };
          })
        );
        return;
      }

      try {
        const t0 = performance.now();
        const searchRes = await executeSearch(
          selectedRepo,
          q,
          8,
          'hybrid',
          0.6
        );
        const duration = performance.now() - t0;

        setTurns((prev) =>
          prev.map((turn) => {
            if (turn.id !== turnId) return turn;
            return {
              ...turn,
              isLoading: false,
              searchResponse: searchRes,
              latencyMs: searchRes.latency_ms || Math.round(duration),
            };
          })
        );

        if (searchRes.results.length > 0) {
          setActiveSources(searchRes.results);
        }
      } catch (err: any) {
        setTurns((prev) =>
          prev.map((turn) => {
            if (turn.id !== turnId) return turn;
            return {
              ...turn,
              isLoading: false,
              error: err.message || 'Search execution failed.',
            };
          })
        );
      }
      return;
    }

    // Default conversational RAG / Local AI mode
    try {
      // 1. If repo is selected, run live vector/hybrid search for sources
      let searchRes: SearchResponse | null = null;
      if (selectedRepo) {
        searchRes = await executeSearch(
          selectedRepo,
          q,
          6,
          isSearchActive ? 'hybrid' : 'vector',
          0.6
        ).catch(() => null);
      }

      // 2. Ask CodeLens AI reasoning engine (works with or without repo!)
      const ansRes = await askCodebase(selectedRepo || '', q, 5, 0.6);

      setTurns((prev) =>
        prev.map((turn) => {
          if (turn.id !== turnId) return turn;
          return {
            ...turn,
            isLoading: false,
            answer: ansRes.answer,
            sources: ansRes.sources,
            searchResponse: searchRes,
            latencyMs: ansRes.latency_ms,
            category: ansRes.category,
            confidenceLevel: ansRes.confidence_level,
            isGeneralAi: !selectedRepo || ansRes.repository_id === 'general',
          };
        })
      );

      if (searchRes && searchRes.results.length > 0) {
        setActiveSources(searchRes.results);
      }
    } catch (err: any) {
      console.error('CodeLens AI query error:', err);
      setTurns((prev) =>
        prev.map((turn) => {
          if (turn.id !== turnId) return turn;
          return {
            ...turn,
            isLoading: false,
            error: err.message || 'Failed to complete query. Ensure the local backend is running.',
          };
        })
      );
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleReset = () => {
    setTurns([]);
    setInputQuery('');
    setActiveSources([]);
    setShowSourcesPanel(false);
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 50);
  };

  const handleCopyAnswer = (turnId: string, answerText?: string) => {
    if (answerText) {
      navigator.clipboard.writeText(answerText);
      setCopiedId(turnId);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const toggleFeedback = (turnId: string, type: 'up' | 'down') => {
    setTurns((prev) =>
      prev.map((turn) => {
        if (turn.id !== turnId) return turn;
        return {
          ...turn,
          feedback: turn.feedback === type ? null : type,
        };
      })
    );
  };

  // Ingest GitHub Repository Handler
  const handleAttachGithubRepo = async (targetUrl?: string) => {
    const url = (targetUrl || gitUrlInput).trim();
    if (!url) return;

    setIsIngesting(true);
    setIngestError(null);
    setIngestSuccessRepo(null);
    setIngestProgress(10);
    setIngestStatusStep('Connecting to GitHub & cloning repository...');

    try {
      const resp = await ingestRemoteRepository(url, false);
      const repoId = resp.repository_name;

      setIngestStatusStep('Cloning repository files...');
      setIngestProgress(25);

      // Poll ingestion status until complete
      const pollInterval = setInterval(async () => {
        try {
          const status = await fetchRepositoryStatus(repoId);
          if (status.status === 'ingesting') {
            setIngestProgress((prev) => Math.min(prev + 15, 85));
            setIngestStatusStep(status.current_step || 'Parsing AST and building FAISS vectors...');
          } else if (status.status === 'ready') {
            clearInterval(pollInterval);
            setIngestProgress(100);
            setIngestStatusStep('Repository successfully attached & indexed!');
            setIngestSuccessRepo(repoId);

            if (onSelectRepo) {
              onSelectRepo(repoId);
            }
            if (onRefreshRepositories) {
              await onRefreshRepositories();
            }

            setTimeout(() => {
              setIsIngesting(false);
              setIsAttachModalOpen(false);
              setGitUrlInput('');
              setIngestSuccessRepo(null);
            }, 1200);
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setIsIngesting(false);
            setIngestError(status.error || 'Ingestion failed. Please check the repository URL.');
          }
        } catch {
          // Keep polling if transient network hitch
        }
      }, 1000);
    } catch (err: any) {
      setIsIngesting(false);
      setIngestError(err.message || 'Failed to initiate repository clone.');
    }
  };

  const presetRepos = [
    { name: 'pallets/click', url: 'https://github.com/pallets/click.git', desc: 'Python CLI framework' },
    { name: 'fastapi/fastapi', url: 'https://github.com/fastapi/fastapi.git', desc: 'Async Python web API' },
    { name: 'facebook/react', url: 'https://github.com/facebook/react.git', desc: 'Frontend UI library' },
    { name: 'tiangolo/sqlmodel', url: 'https://github.com/tiangolo/sqlmodel.git', desc: 'SQL databases in Python' },
  ];

  interface ActionPill {
    label: string;
    icon: React.FC<{ className?: string }>;
    isSpecial?: boolean;
    query?: string;
    onClick?: () => void;
  }

  const actionPills: ActionPill[] = [
    {
      label: 'Attach GitHub Repo',
      isSpecial: true,
      icon: GithubIcon,
      onClick: () => setIsAttachModalOpen(true),
    },
  ];

  const isConversational = turns.length > 0;
  const isAnyLoading = turns.some((t) => t.isLoading);

  return (
    <div className="flex h-full bg-[#121215] text-[#ececec] font-sans overflow-hidden select-none">
      {/* Main Conversation & Search Canvas */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Header Bar */}
        <header className="h-12 px-4 flex items-center justify-between border-b border-[#252530] bg-[#121215] shrink-0 z-20">
          <div className="flex items-center space-x-2">
            {/* Model Dropdown */}
            <div className="relative">
              <button
                onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl hover:bg-[#1c1c24] text-sm font-semibold text-[#ececec] transition-colors cursor-pointer border border-transparent hover:border-[#2f2f3d]"
              >
                <span>{selectedModel}</span>
                <ChevronDown className="w-3.5 h-3.5 text-[#a1a1aa]" />
              </button>

              {modelDropdownOpen && (
                <div className="absolute top-10 left-0 w-64 bg-[#18181f] border border-[#2d2d3d] rounded-2xl shadow-2xl p-1.5 z-50 text-xs">
                  <div className="px-3 py-1.5 text-[11px] font-semibold text-[#a1a1aa] uppercase tracking-wider">
                    Model Engine
                  </div>
                  {[
                    { id: 'CodeLens AI', desc: 'Fastest for general coding, Q&A, and codebase exploration' },
                    { id: 'CodeLens AI (Deep Reason)', desc: 'Multi-step architectural logic & AST call graph tracing' },
                    { id: 'CodeLens AI (Hybrid BM25+FAISS)', desc: 'Trained GBDT ranker + local dense vectors' },
                  ].map((m) => (
                    <button
                      key={m.id}
                      onClick={() => {
                        setSelectedModel(m.id);
                        setModelDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-xl hover:bg-[#252535] transition-colors flex flex-col cursor-pointer ${
                        selectedModel === m.id ? 'bg-[#252535]' : ''
                      }`}
                    >
                      <span className="font-medium text-[#ececec]">{m.id}</span>
                      <span className="text-[11px] text-[#a1a1aa]">{m.desc}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Attached Repository Indicator Pill */}
            {selectedRepo ? (
              <button
                onClick={() => setIsAttachModalOpen(true)}
                className="flex items-center space-x-1.5 text-xs text-sky-300 font-mono px-2.5 py-1 bg-sky-950/40 hover:bg-sky-900/50 rounded-lg border border-sky-800/50 transition-colors cursor-pointer"
                title="Change or attach another repository"
              >
                <GithubIcon className="w-3.5 h-3.5 text-sky-400" />
                <span>repo:</span>
                <strong className="text-white">{selectedRepo}</strong>
                <ChevronDown className="w-3 h-3 text-sky-400 opacity-70" />
              </button>
            ) : (
              <button
                onClick={() => setIsAttachModalOpen(true)}
                className="flex items-center space-x-1.5 text-xs text-indigo-300 px-2.5 py-1 bg-indigo-950/40 hover:bg-indigo-900/50 rounded-lg border border-indigo-800/50 transition-colors cursor-pointer animate-pulse"
                title="Attach a GitHub repository"
              >
                <GithubIcon className="w-3.5 h-3.5 text-indigo-400" />
                <span>Attach GitHub Repo</span>
                <Plus className="w-3 h-3 text-indigo-400" />
              </button>
            )}
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center space-x-2">
            {/* Quick Attach GitHub Repo Button */}
            <button
              onClick={() => setIsAttachModalOpen(true)}
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-[#1c1c26] hover:bg-[#262635] text-xs font-medium text-[#ececec] border border-[#2e2e3f] transition-all cursor-pointer shadow-sm"
            >
              <GithubIcon className="w-3.5 h-3.5 text-sky-400" />
              <span className="hidden sm:inline">Attach Repo</span>
            </button>

            {isConversational && (
              <button
                onClick={handleReset}
                className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg hover:bg-[#1c1c26] text-[#a1a1aa] hover:text-[#ececec] text-xs transition-colors cursor-pointer"
                title="New Chat"
              >
                <SquarePen className="w-4 h-4" />
                <span className="hidden sm:inline">New chat</span>
              </button>
            )}

            {activeSources.length > 0 && (
              <button
                onClick={() => setShowSourcesPanel(!showSourcesPanel)}
                className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  showSourcesPanel
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                    : 'hover:bg-[#1c1c26] text-[#a1a1aa] hover:text-[#ececec]'
                }`}
                title="Toggle Sources"
              >
                <Globe className="w-4 h-4" />
                <span>Sources</span>
                <span className="px-1.5 py-0.2 rounded-full bg-[#1c1c26] text-[10px] font-mono text-sky-400">
                  {activeSources.length}
                </span>
              </button>
            )}
          </div>
        </header>

        {/* Scrollable Viewport */}
        <div
          ref={chatScrollContainerRef}
          className="flex-1 overflow-y-auto px-4 py-8 flex flex-col items-center"
        >
          {!isConversational ? (
            /* ================= INITIAL CHATGPT HOME SEARCH VIEW ================= */
            <div className="w-full max-w-[768px] my-auto flex flex-col items-center text-center animate-in fade-in duration-300">
              {/* ChatGPT Headline */}
              <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-[#ececec] mb-8 font-sans">
                What can I help with?
              </h1>

              {/* Signature Composer Capsule */}
              <div className="w-full bg-[#1b1b22] hover:bg-[#202029] focus-within:bg-[#1b1b22] border border-[#2d2d3a] focus-within:border-[#4f4f66] focus-within:ring-1 focus-within:ring-[#4f4f66] rounded-[26px] shadow-[0_8px_32px_rgba(0,0,0,0.4)] transition-all p-3.5 flex flex-col mb-5 text-left">
                {/* Textarea */}
                <textarea
                  ref={textareaRef}
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  placeholder={
                    isSearchOnly
                      ? 'Search code symbols, functions, or keywords (Fast BM25 + FAISS)...'
                      : 'Ask CodeLens AI anything, or search attached codebase...'
                  }
                  className="w-full bg-transparent text-[#ececec] placeholder-[#71717a] text-base resize-none focus:outline-none px-1.5 pt-0.5 pb-2 leading-relaxed font-sans min-h-[44px] max-h-48"
                />

                {/* Internal Composer Toolbar */}
                <div className="flex items-center justify-between pt-1">
                  {/* Left: Search Only toggle, Attach Repo, Reason toggle */}
                  <div className="flex items-center space-x-1.5">
                    {/* Attach GitHub Repo button (+) */}
                    <button
                      type="button"
                      onClick={() => setIsAttachModalOpen(true)}
                      className="p-1.5 rounded-full hover:bg-[#2a2a38] text-[#a1a1aa] hover:text-[#ececec] transition-colors cursor-pointer group"
                      title="Attach GitHub Repository"
                    >
                      <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
                    </button>

                    {/* Dedicated Attach Repo Pill */}
                    <button
                      type="button"
                      onClick={() => setIsAttachModalOpen(true)}
                      className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                        selectedRepo
                          ? 'bg-sky-950/60 text-sky-400 border border-sky-800/60 hover:bg-sky-900/60'
                          : 'bg-[#262635] text-[#b4b4c4] hover:text-[#ececec] border border-[#353548] hover:bg-[#303042]'
                      }`}
                      title={selectedRepo ? `Attached: ${selectedRepo}` : 'Attach GitHub Repository'}
                    >
                      <GithubIcon className="w-3.5 h-3.5 text-sky-400" />
                      <span>{selectedRepo ? selectedRepo : 'Attach Repo'}</span>
                    </button>

                    {/* Search Only Toggle Pill */}
                    <button
                      type="button"
                      onClick={() => setIsSearchOnly(!isSearchOnly)}
                      className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                        isSearchOnly
                          ? 'bg-amber-950/70 text-amber-300 border border-amber-500/60 shadow-[0_0_12px_rgba(245,158,11,0.25)]'
                          : 'bg-[#262635] text-[#a1a1aa] hover:text-[#ececec] border border-[#353548] hover:bg-[#303042]'
                      }`}
                      title={isSearchOnly ? 'Search only mode is ON (no LLM generation, fast code chunk hits)' : 'Enable Search only mode'}
                    >
                      <Search className={`w-3.5 h-3.5 ${isSearchOnly ? 'text-amber-400' : 'text-[#a1a1aa]'}`} />
                      <span>Search only</span>
                      <span className={`w-1.5 h-1.5 rounded-full ${isSearchOnly ? 'bg-amber-400 animate-pulse' : 'bg-[#52525b]'}`} />
                    </button>

                    {/* Reason Toggle Pill */}
                    <button
                      type="button"
                      onClick={() => setIsReasonActive(!isReasonActive)}
                      className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                        isReasonActive
                          ? 'bg-purple-950/60 text-purple-300 border border-purple-500/40 shadow-sm'
                          : 'hover:bg-[#2a2a38] text-[#a1a1aa]'
                      }`}
                      title="Deep Reasoning Mode"
                    >
                      <Brain className="w-3.5 h-3.5" />
                      <span>Reason</span>
                    </button>
                  </div>

                  {/* Right: Mic & Circular Up Arrow Send Button */}
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => setIsListening(!isListening)}
                      className={`p-1.5 rounded-full hover:bg-[#2a2a38] transition-colors cursor-pointer ${
                        isListening ? 'text-rose-400 animate-pulse' : 'text-[#a1a1aa] hover:text-[#ececec]'
                      }`}
                      title="Voice input"
                    >
                      {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleSearch()}
                      disabled={!inputQuery.trim() || isAnyLoading}
                      className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                        inputQuery.trim() && !isAnyLoading
                          ? 'bg-white text-black hover:bg-[#e4e4e7] hover:scale-105 shadow-md cursor-pointer'
                          : 'bg-[#323240] text-[#71717a] cursor-not-allowed'
                      }`}
                      title="Send message"
                    >
                      <ArrowUp className="w-4 h-4 stroke-[2.5]" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Action Pills Underneath Search Bar */}
              <div className="flex flex-wrap items-center justify-center gap-2 max-w-xl">
                {actionPills.map((pill, i) => {
                  const Icon = pill.icon;
                  return (
                    <button
                      key={i}
                      onClick={() => {
                        if (pill.onClick) {
                          pill.onClick();
                        } else if (pill.query) {
                          setInputQuery(pill.query);
                          handleSearch(pill.query);
                        }
                      }}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs transition-all cursor-pointer ${
                        pill.isSpecial
                          ? 'bg-gradient-to-r from-sky-950/80 to-indigo-950/80 hover:from-sky-900/90 hover:to-indigo-900/90 border border-sky-500/40 text-sky-200 font-medium shadow-sm'
                          : 'bg-[#1b1b24] hover:bg-[#262635] border border-[#2e2e3f] text-[#a1a1aa] hover:text-[#ececec]'
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 ${pill.isSpecial ? 'text-sky-400' : 'text-[#a1a1aa]'}`} />
                      <span>{pill.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Clean Helper Note */}
              <div className="text-[11px] text-[#71717a] mt-6">
                Ask any general coding question like ChatGPT, or attach a GitHub repository to ground answers with AST citations.
              </div>
            </div>
          ) : (
            /* ================= CONVERSATIONAL STREAM VIEW ================= */
            <div className="w-full max-w-[768px] flex flex-col space-y-8 pb-36 animate-in fade-in duration-200">
              {turns.map((turn) => (
                <div key={turn.id} className="space-y-6">
                  {/* User Message Bubble */}
                  <div className="flex justify-end">
                    <div className="max-w-[80%] sm:max-w-[70%] bg-[#22222d] border border-[#323244] text-[#ececec] px-4 py-2.5 rounded-[22px] text-base leading-relaxed shadow-sm">
                      <p className="whitespace-pre-wrap">{turn.query}</p>
                    </div>
                  </div>

                  {/* Assistant Message */}
                  <div className="flex items-start space-x-4">
                    <CodeLensAIIcon />

                    <div className="flex-1 min-w-0 space-y-3">
                      {/* Meta Pills (Search Only Mode vs Searched Sources vs General AI) */}
                      {turn.isSearchOnly ? (
                        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-950/40 border border-amber-600/40 text-xs text-amber-300">
                          <Search className="w-3.5 h-3.5 text-amber-400" />
                          <span className="font-medium">Search Only Mode</span>
                          {turn.searchResponse && (
                            <span className="text-[11px] text-amber-400/80">
                              • {turn.searchResponse.results.length} matches
                            </span>
                          )}
                          {turn.latencyMs !== undefined && (
                            <span className="text-[10px] font-mono text-amber-400/70">
                              ({turn.latencyMs.toFixed(0)}ms)
                            </span>
                          )}
                        </div>
                      ) : turn.searchResponse && turn.searchResponse.results.length > 0 ? (
                        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#1c1c26] border border-[#2e2e3f] text-xs text-[#a1a1aa]">
                          <Globe className="w-3.5 h-3.5 text-sky-400" />
                          <span>Searched {turn.searchResponse.results.length} code sources</span>
                          {turn.latencyMs !== undefined && (
                            <span className="text-[10px] font-mono text-[#71717a]">
                              ({turn.latencyMs.toFixed(0)}ms)
                            </span>
                          )}
                          <button
                            onClick={() => {
                              setActiveSources(turn.searchResponse?.results || []);
                              setShowSourcesPanel(true);
                            }}
                            className="text-sky-400 hover:underline font-medium cursor-pointer ml-1"
                          >
                            View sources →
                          </button>
                        </div>
                      ) : turn.isGeneralAi ? (
                        <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-indigo-950/40 border border-indigo-800/40 text-[11px] text-indigo-300">
                          <Sparkles className="w-3 h-3 text-indigo-400" />
                          <span>CodeLens General AI</span>
                          {turn.latencyMs !== undefined && (
                            <span className="text-[10px] font-mono text-indigo-400/70">
                              ({turn.latencyMs.toFixed(0)}ms)
                            </span>
                          )}
                        </div>
                      ) : null}

                      {/* Thinking Pulse while loading */}
                      {turn.isLoading && (
                        <div className="flex items-center space-x-2.5 text-sm text-[#a1a1aa] py-3">
                          <div className={`w-3 h-3 rounded-full animate-pulse ${turn.isSearchOnly ? 'bg-amber-400' : 'bg-sky-400'}`} />
                          <span>
                            {turn.isSearchOnly
                              ? 'Searching AST chunks and BM25+FAISS vector index...'
                              : 'Reasoning & synthesizing response...'}
                          </span>
                        </div>
                      )}

                      {/* Error message */}
                      {turn.error && (
                        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs flex items-center space-x-2">
                          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                          <span>{turn.error}</span>
                        </div>
                      )}

                      {/* SEARCH ONLY VIEW: Render code chunk cards */}
                      {turn.isSearchOnly && !turn.isLoading && turn.searchResponse && (
                        <div className="space-y-3.5 pt-1">
                          {turn.searchResponse.results.length === 0 ? (
                            <div className="p-6 text-center text-xs text-[#a1a1aa] bg-[#161622] border border-[#2b2b3d] rounded-xl">
                              No matching code chunks found for &ldquo;{turn.query}&rdquo;. Try another symbol or search term.
                            </div>
                          ) : (
                            turn.searchResponse.results.map((item, idx) => {
                              const cardKey = `search_${turn.id}_${idx}`;
                              return (
                                <div
                                  key={cardKey}
                                  className="bg-[#14141d] border border-[#262638] hover:border-amber-500/40 rounded-xl overflow-hidden shadow-sm transition-all"
                                >
                                  {/* Card Header */}
                                  <div className="px-3.5 py-2.5 bg-[#191924] border-b border-[#262638] flex flex-wrap items-center justify-between gap-2">
                                    <div className="flex items-center space-x-2">
                                      <span className="w-5 h-5 rounded-full bg-amber-950 text-amber-300 border border-amber-800/60 flex items-center justify-center text-[10px] font-bold font-mono">
                                        #{item.rank || idx + 1}
                                      </span>
                                      <button
                                        onClick={() => onOpenFileInExplorer(item.file_path)}
                                        className="font-mono text-xs font-semibold text-sky-400 hover:underline cursor-pointer"
                                      >
                                        {item.file_path.split('/').pop()}
                                      </button>
                                      <span className="text-[11px] text-[#71717a] font-mono">
                                        (L{item.start_line}–{item.end_line})
                                      </span>
                                      {item.symbol && (
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-sky-950/40 text-sky-300 border border-sky-800/40">
                                          {item.chunk_type}: {item.symbol}
                                        </span>
                                      )}
                                    </div>

                                    <div className="flex items-center space-x-2">
                                      <span className="text-[10px] font-mono bg-[#1c1c28] border border-[#2c2c3d] px-2 py-0.5 rounded text-emerald-400">
                                        {(item.similarity * 100).toFixed(1)}% match
                                      </span>
                                      <button
                                        onClick={() => {
                                          navigator.clipboard.writeText(item.code);
                                          setCopiedId(cardKey);
                                          setTimeout(() => setCopiedId(null), 2000);
                                        }}
                                        className="p-1 text-[#a1a1aa] hover:text-white rounded hover:bg-[#252535] transition-colors cursor-pointer"
                                        title="Copy code snippet"
                                      >
                                        {copiedId === cardKey ? (
                                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                                        ) : (
                                          <Copy className="w-3.5 h-3.5" />
                                        )}
                                      </button>
                                      <button
                                        onClick={() => onOpenFileInExplorer(item.file_path)}
                                        className="flex items-center space-x-1 px-2 py-1 bg-[#222230] hover:bg-sky-950/60 hover:text-sky-300 text-[#ececec] rounded text-[11px] font-medium transition-colors cursor-pointer border border-[#323246]"
                                      >
                                        <span>Open in Explorer</span>
                                        <ExternalLink className="w-3 h-3" />
                                      </button>
                                    </div>
                                  </div>

                                  {/* File path sub-bar */}
                                  <div className="px-3.5 py-1.5 bg-[#101017] border-b border-[#20202e] text-[11px] font-mono text-[#71717a] flex items-center justify-between">
                                    <span className="truncate">{item.file_path}</span>
                                    {item.docstring && (
                                      <span className="italic text-[#a1a1aa] truncate max-w-[50%]">
                                        &ldquo;{item.docstring}&rdquo;
                                      </span>
                                    )}
                                  </div>

                                  {/* Code Block with Line Numbers */}
                                  <div className="p-3.5 bg-[#0a0a0f] overflow-x-auto text-xs font-mono text-[#ececec] leading-relaxed max-h-72">
                                    <pre>
                                      {item.code.split('\n').map((line, lineIdx) => {
                                        const currentLineNum = item.start_line + lineIdx;
                                        return (
                                          <div key={lineIdx} className="table-row hover:bg-[#161622]">
                                            <span className="table-cell select-none text-[#52525b] pr-4 text-right opacity-60 w-8">
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
                            })
                          )}
                        </div>
                      )}

                      {/* CONVERSATIONAL MODE: Grounded Markdown Answer */}
                      {!turn.isSearchOnly && turn.answer && (
                        <div className="prose prose-invert max-w-none text-base text-[#ececec] leading-relaxed">
                          <ReactMarkdown
                            components={{
                              code: CodeBlock as any,
                            }}
                          >
                            {turn.answer}
                          </ReactMarkdown>
                        </div>
                      )}

                      {/* Sources Carousel preview (if repo returned sources in conversational mode) */}
                      {!turn.isSearchOnly && turn.sources && turn.sources.length > 0 && (
                        <div className="pt-2">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-semibold text-[#a1a1aa] uppercase tracking-wider">
                              Referenced Code Files
                            </span>
                            {turn.searchResponse && (
                              <button
                                onClick={() => {
                                  setActiveSources(turn.searchResponse?.results || []);
                                  setShowSourcesPanel(true);
                                }}
                                className="text-xs text-sky-400 hover:underline cursor-pointer"
                              >
                                See all sources
                              </button>
                            )}
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {turn.sources.slice(0, 4).map((src, i) => (
                              <button
                                key={i}
                                onClick={() => onOpenFileInExplorer(src.file_path)}
                                className="p-3 rounded-xl bg-[#1b1b24] hover:bg-[#252535] border border-[#2e2e3f] text-left transition-colors cursor-pointer group flex flex-col justify-between"
                              >
                                <div className="flex items-center justify-between w-full mb-1">
                                  <span className="text-xs font-mono font-medium text-[#ececec] truncate group-hover:text-sky-400">
                                    {src.file_path.split('/').pop()}
                                  </span>
                                  <span className="text-[10px] font-mono text-sky-400 bg-sky-950/60 px-1.5 py-0.2 rounded">
                                    {(src.similarity * 100).toFixed(0)}%
                                  </span>
                                </div>
                                <p className="text-[11px] text-[#71717a] truncate font-mono">
                                  {src.file_path} (L{src.start_line}–{src.end_line})
                                </p>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Bottom Action Row (Copy, Thumbs, Share) */}
                      {!turn.isLoading && turn.answer && (
                        <div className="flex items-center space-x-1 pt-2 text-[#a1a1aa]">
                          <button
                            onClick={() => handleCopyAnswer(turn.id, turn.answer)}
                            className="p-1.5 rounded-lg hover:bg-[#252535] hover:text-[#ececec] transition-colors cursor-pointer"
                            title="Copy answer"
                          >
                            {copiedId === turn.id ? (
                              <Check className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>

                          <button
                            onClick={() => toggleFeedback(turn.id, 'up')}
                            className={`p-1.5 rounded-lg hover:bg-[#252535] transition-colors cursor-pointer ${
                              turn.feedback === 'up' ? 'text-emerald-400 bg-[#252535]' : 'hover:text-[#ececec]'
                            }`}
                            title="Good response"
                          >
                            <ThumbsUp className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => toggleFeedback(turn.id, 'down')}
                            className={`p-1.5 rounded-lg hover:bg-[#252535] transition-colors cursor-pointer ${
                              turn.feedback === 'down' ? 'text-rose-400 bg-[#252535]' : 'hover:text-[#ececec]'
                            }`}
                            title="Poor response"
                          >
                            <ThumbsDown className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sticky Bottom Composer when conversation is active */}
        {isConversational && (
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#121215] via-[#121215]/95 to-transparent z-20 flex flex-col items-center">
            <div className="w-full max-w-[768px] flex flex-col">
              <div className="w-full bg-[#1b1b24] hover:bg-[#20202d] focus-within:bg-[#1b1b24] border border-[#2e2e40] focus-within:border-[#4f4f66] focus-within:ring-1 focus-within:ring-[#4f4f66] rounded-[26px] shadow-2xl p-3 flex flex-col transition-all">
                <textarea
                  ref={bottomTextareaRef}
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  placeholder={
                    isSearchOnly
                      ? 'Search code symbols, functions, or keywords (Fast BM25 + FAISS)...'
                      : 'Ask CodeLens AI a follow-up or search code...'
                  }
                  className="w-full bg-transparent text-[#ececec] placeholder-[#71717a] text-base resize-none focus:outline-none px-1.5 pt-0.5 pb-2 leading-relaxed font-sans min-h-[36px] max-h-36"
                />

                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center space-x-1.5">
                    {/* Attach Repo (+) */}
                    <button
                      type="button"
                      onClick={() => setIsAttachModalOpen(true)}
                      className="p-1.5 rounded-full hover:bg-[#2a2a38] text-[#a1a1aa] hover:text-[#ececec] transition-colors cursor-pointer group"
                      title="Attach GitHub Repository"
                    >
                      <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
                    </button>

                    {/* Dedicated Attach Repo Pill */}
                    <button
                      type="button"
                      onClick={() => setIsAttachModalOpen(true)}
                      className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                        selectedRepo
                          ? 'bg-sky-950/60 text-sky-400 border border-sky-800/60'
                          : 'bg-[#262635] text-[#b4b4c4] border border-[#353548]'
                      }`}
                    >
                      <GithubIcon className="w-3.5 h-3.5 text-sky-400" />
                      <span>{selectedRepo ? selectedRepo : 'Attach Repo'}</span>
                    </button>

                    {/* Search Only Toggle Pill */}
                    <button
                      type="button"
                      onClick={() => setIsSearchOnly(!isSearchOnly)}
                      className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                        isSearchOnly
                          ? 'bg-amber-950/70 text-amber-300 border border-amber-500/60 shadow-[0_0_12px_rgba(245,158,11,0.25)]'
                          : 'bg-[#262635] text-[#a1a1aa] hover:text-[#ececec] border border-[#353548]'
                      }`}
                      title={isSearchOnly ? 'Search only mode is ON (no LLM generation, fast code chunk hits)' : 'Enable Search only mode'}
                    >
                      <Search className={`w-3.5 h-3.5 ${isSearchOnly ? 'text-amber-400' : 'text-[#a1a1aa]'}`} />
                      <span>Search only</span>
                      <span className={`w-1.5 h-1.5 rounded-full ${isSearchOnly ? 'bg-amber-400 animate-pulse' : 'bg-[#52525b]'}`} />
                    </button>

                    {/* Reason Toggle Pill */}
                    <button
                      type="button"
                      onClick={() => setIsReasonActive(!isReasonActive)}
                      className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                        isReasonActive
                          ? 'bg-purple-950/60 text-purple-300 border border-purple-500/40'
                          : 'hover:bg-[#2a2a38] text-[#a1a1aa]'
                      }`}
                    >
                      <Brain className="w-3.5 h-3.5" />
                      <span>Reason</span>
                    </button>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => handleSearch()}
                      disabled={!inputQuery.trim() || isAnyLoading}
                      className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                        inputQuery.trim() && !isAnyLoading
                          ? 'bg-white text-black hover:bg-[#e4e4e7] hover:scale-105 shadow-md cursor-pointer'
                          : 'bg-[#323240] text-[#71717a] cursor-not-allowed'
                      }`}
                      title="Send message"
                    >
                      <ArrowUp className="w-4 h-4 stroke-[2.5]" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Subtext Disclaimer */}
              <div className="text-[11px] text-[#71717a] text-center mt-2">
                CodeLens AI can make mistakes. Always review code before deploying.
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sources Side Panel Drawer (Right Rail) */}
      {showSourcesPanel && (
        <aside className="w-80 border-l border-[#252532] bg-[#16161d] flex flex-col h-full z-30 shrink-0 animate-in slide-in-from-right duration-200">
          <div className="h-12 px-4 flex items-center justify-between border-b border-[#252532] shrink-0">
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-semibold text-[#ececec]">Sources</h3>
              <span className="text-xs text-[#a1a1aa] font-mono">
                ({activeSources.length})
              </span>
            </div>
            <button
              onClick={() => setShowSourcesPanel(false)}
              className="p-1 rounded-md hover:bg-[#252535] text-[#a1a1aa] hover:text-[#ececec] transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {activeSources.length > 0 ? (
              activeSources.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-[#1e1e28] border border-[#2e2e40] hover:border-[#44445c] transition-all"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-mono font-semibold text-[#ececec] truncate">
                      {item.file_path.split('/').pop()}
                    </span>
                    <span className="text-[10px] font-mono text-sky-400 bg-sky-950/60 px-1.5 py-0.2 rounded border border-sky-800/40">
                      {(item.similarity * 100).toFixed(0)}%
                    </span>
                  </div>

                  <p className="text-[11px] font-mono text-[#a1a1aa] truncate mb-2">
                    {item.file_path} {item.start_line && `(L${item.start_line}–${item.end_line})`}
                  </p>

                  <pre className="p-2 text-[10px] font-mono text-[#ececec] bg-[#121217] rounded-lg overflow-x-auto max-h-28 border border-[#2a2a38]">
                    <code>{item.code}</code>
                  </pre>

                  <button
                    onClick={() => onOpenFileInExplorer(item.file_path)}
                    className="w-full mt-2.5 flex items-center justify-center space-x-1.5 py-1 px-2 rounded-lg bg-[#272736] hover:bg-[#323245] text-[11px] text-[#ececec] font-medium transition-colors cursor-pointer"
                  >
                    <span>Open in Code Explorer</span>
                    <ExternalLink className="w-3 h-3 text-[#a1a1aa]" />
                  </button>
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-xs text-[#a1a1aa]">
                No sources loaded yet. Perform a query with an attached repo to inspect code chunks.
              </div>
            )}
          </div>
        </aside>
      )}

      {/* ================= ATTACH GITHUB REPOSITORY MODAL ================= */}
      {isAttachModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-xl bg-[#181822] border border-[#2e2e42] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-[#29293b] flex items-center justify-between bg-[#15151e]">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
                  <GithubIcon className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Attach GitHub Repository</h3>
                  <p className="text-xs text-[#a1a1aa]">
                    Clone and index any public GitHub repo to ground CodeLens AI in your code.
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  if (!isIngesting) {
                    setIsAttachModalOpen(false);
                    setIngestError(null);
                  }
                }}
                disabled={isIngesting}
                className="p-1.5 rounded-lg hover:bg-[#252535] text-[#a1a1aa] hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Clone Remote Repository Section */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-[#ececec] uppercase tracking-wider block">
                  GitHub Repository URL
                </label>
                <div className="flex items-center space-x-2">
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={gitUrlInput}
                      onChange={(e) => setGitUrlInput(e.target.value)}
                      placeholder="https://github.com/pallets/click.git"
                      disabled={isIngesting}
                      className="w-full px-3.5 py-2.5 bg-[#121218] border border-[#2e2e42] focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded-xl text-sm text-white placeholder-[#71717a] focus:outline-none transition-all font-mono"
                    />
                  </div>
                  <button
                    onClick={() => handleAttachGithubRepo()}
                    disabled={!gitUrlInput.trim() || isIngesting}
                    className={`px-4 py-2.5 rounded-xl font-medium text-sm flex items-center space-x-1.5 transition-all ${
                      gitUrlInput.trim() && !isIngesting
                        ? 'bg-sky-500 hover:bg-sky-400 text-white shadow-md cursor-pointer'
                        : 'bg-[#282838] text-[#71717a] cursor-not-allowed'
                    }`}
                  >
                    {isIngesting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        <span>Cloning...</span>
                      </>
                    ) : (
                      <>
                        <GithubIcon className="w-4 h-4" />
                        <span>Attach & Ingest</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Quick Presets */}
                <div className="pt-1">
                  <span className="text-[11px] text-[#71717a] block mb-2">Or attach a popular open-source preset:</span>
                  <div className="flex flex-wrap gap-2">
                    {presetRepos.map((preset) => (
                      <button
                        key={preset.name}
                        onClick={() => {
                          setGitUrlInput(preset.url);
                          handleAttachGithubRepo(preset.url);
                        }}
                        disabled={isIngesting}
                        className="px-2.5 py-1 rounded-lg bg-[#20202d] hover:bg-[#28283a] border border-[#2e2e42] text-xs text-[#a1a1aa] hover:text-white transition-all cursor-pointer flex items-center space-x-1.5"
                      >
                        <GithubIcon className="w-3 h-3 text-sky-400" />
                        <span>{preset.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Ingestion Progress View */}
              {isIngesting && (
                <div className="p-4 rounded-xl bg-[#14141e] border border-sky-900/40 space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-sky-300 flex items-center space-x-2">
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />
                      <span>{ingestStatusStep}</span>
                    </span>
                    <span className="font-mono text-sky-400 font-bold">{ingestProgress}%</span>
                  </div>
                  <div className="w-full h-2 bg-[#20202e] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-sky-500 to-indigo-500 transition-all duration-300 rounded-full"
                      style={{ width: `${ingestProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Ingestion Success View */}
              {ingestSuccessRepo && (
                <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 text-xs flex items-center space-x-2 animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>
                    Successfully attached <strong>{ingestSuccessRepo}</strong>! Switching active context...
                  </span>
                </div>
              )}

              {/* Error Message */}
              {ingestError && (
                <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs flex items-center space-x-2 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{ingestError}</span>
                </div>
              )}

              {/* Available / Already Indexed Repositories List */}
              <div className="space-y-3 pt-2 border-t border-[#252538]">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-[#ececec] uppercase tracking-wider">
                    Already Indexed Repositories ({repositories.length})
                  </label>
                  {onRefreshRepositories && (
                    <button
                      onClick={() => onRefreshRepositories()}
                      className="text-xs text-sky-400 hover:underline cursor-pointer"
                    >
                      Refresh
                    </button>
                  )}
                </div>

                {repositories.length > 0 ? (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {repositories.map((repo) => {
                      const isActive = repo.repository_id === selectedRepo;
                      return (
                        <div
                          key={repo.repository_id}
                          className={`p-3 rounded-xl border flex items-center justify-between transition-all ${
                            isActive
                              ? 'bg-sky-950/30 border-sky-700/50'
                              : 'bg-[#1b1b26] border-[#29293d] hover:border-[#3d3d59]'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <FolderGit2 className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-[#71717a]'}`} />
                            <div>
                              <div className="text-sm font-semibold text-white flex items-center space-x-2">
                                <span>{repo.repository_name}</span>
                                {isActive && (
                                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30">
                                    Active
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-[#71717a] flex items-center space-x-2">
                                <span>{repo.total_files} files</span>
                                <span>•</span>
                                <span>{repo.total_chunks} code chunks</span>
                              </div>
                            </div>
                          </div>

                          {!isActive && onSelectRepo && (
                            <button
                              onClick={() => {
                                onSelectRepo(repo.repository_id);
                                setIsAttachModalOpen(false);
                              }}
                              className="px-3 py-1.5 rounded-lg bg-[#28283a] hover:bg-[#34344d] text-xs font-medium text-white transition-colors cursor-pointer"
                            >
                              Attach
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-6 text-xs text-[#71717a]">
                    No repositories indexed yet. Enter a GitHub URL above to clone one!
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 border-t border-[#252538] bg-[#14141e] flex items-center justify-end">
              <button
                onClick={() => setIsAttachModalOpen(false)}
                disabled={isIngesting}
                className="px-4 py-2 rounded-xl bg-[#222230] hover:bg-[#2b2b3d] text-xs font-medium text-white transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
