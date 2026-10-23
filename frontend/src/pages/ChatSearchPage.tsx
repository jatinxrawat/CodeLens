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
  Compass,
  ShieldCheck,
  Cpu,
  Star,
  GitFork,
} from 'lucide-react';
import type {
  SearchResponse,
  SearchMode,
  SearchResultItem,
  AskResponse,
  RepositorySummary,
  CitationSource,
  ExploreRepoItem,
  LLMProviderStatus,
} from '../types';
import {
  executeSearch,
  askCodebase,
  ingestRemoteRepository,
  fetchRepositoryStatus,
  fetchExploreRepos,
  analyzeRepository,
  fetchRepoStatus,
  fetchProviderStatus,
  setLLMProvider,
} from '../services/api';

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
    className={`rounded-full bg-zinc-900 border border-zinc-700/80 flex items-center justify-center text-white shrink-0 shadow-sm ${className}`}
  >
    <Sparkles className="w-3.5 h-3.5 text-zinc-200" />
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
    <div className="my-3 rounded-xl overflow-hidden border border-[#18181b] bg-[#000000] shadow-md">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#08080a] border-b border-[#18181b] text-[11px] font-mono text-zinc-400">
        <span className="uppercase font-semibold tracking-wider text-zinc-200">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-2 py-0.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-white" />
              <span className="text-white">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy code</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-xs font-mono text-zinc-200 overflow-x-auto leading-relaxed max-h-96">
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
  const [selectedModel, setSelectedModel] = useState('Gemini 2.5 Flash');
  const [activeProvider, setActiveProvider] = useState<'gemini' | 'local'>('gemini');
  const [explanationMode, setExplanationMode] = useState<'beginner' | 'expert'>('beginner');
  const [showSourcesPanel, setShowSourcesPanel] = useState(false);
  const [activeSources, setActiveSources] = useState<SearchResultItem[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Front Door & Explore Feed State (when no repo is attached)
  const [exploreFeedRepos, setExploreFeedRepos] = useState<ExploreRepoItem[]>([]);
  const [loadingExploreFeed, setLoadingExploreFeed] = useState(false);
  const [frontDoorUrl, setFrontDoorUrl] = useState('');
  const [frontDoorAnalyzing, setFrontDoorAnalyzing] = useState(false);
  const [frontDoorProgress, setFrontDoorProgress] = useState(0);
  const [frontDoorStep, setFrontDoorStep] = useState('Initiating analysis...');
  const [frontDoorError, setFrontDoorError] = useState<string | null>(null);

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

  // Load Provider status & Explore feed when no repo attached
  useEffect(() => {
    fetchProviderStatus()
      .then((s) => {
        setActiveProvider(s.active_provider);
        setSelectedModel(s.active_provider === 'gemini' ? 'Gemini 2.5 Flash' : 'Local ML Engine');
      })
      .catch(() => {});

    if (!selectedRepo) {
      setLoadingExploreFeed(true);
      fetchExploreRepos({ min_stars: 100, page: 1, per_page: 6 })
        .then((res) => setExploreFeedRepos(res.repos))
        .catch(() => {})
        .finally(() => setLoadingExploreFeed(false));
    }
  }, [selectedRepo]);

  const frontDoorIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (frontDoorIntervalRef.current) {
        clearInterval(frontDoorIntervalRef.current);
        frontDoorIntervalRef.current = null;
      }
    };
  }, []);

  const handleFrontDoorAnalyze = async (urlToAnalyze?: string) => {
    const targetUrl = (urlToAnalyze || frontDoorUrl).trim();
    if (!targetUrl) return;

    if (frontDoorIntervalRef.current) {
      clearInterval(frontDoorIntervalRef.current);
      frontDoorIntervalRef.current = null;
    }

    try {
      setFrontDoorAnalyzing(true);
      setFrontDoorProgress(5);
      setFrontDoorStep('Job queued for analysis...');
      setFrontDoorError(null);

      const jobResp = await analyzeRepository(targetUrl);
      const targetRepoId = jobResp.repo_id;
      if (jobResp.message) setFrontDoorStep(jobResp.message);
      if (typeof jobResp.progress_pct === 'number') setFrontDoorProgress(jobResp.progress_pct);

      let attempts = 0;
      const maxAttempts = 150;

      frontDoorIntervalRef.current = window.setInterval(async () => {
        attempts += 1;
        if (attempts > maxAttempts) {
          if (frontDoorIntervalRef.current) {
            clearInterval(frontDoorIntervalRef.current);
            frontDoorIntervalRef.current = null;
          }
          setFrontDoorError('Analysis timed out. Please try again.');
          setFrontDoorAnalyzing(false);
          return;
        }

        try {
          const status = await fetchRepoStatus(targetRepoId);
          if (typeof status.progress_pct === 'number') setFrontDoorProgress(status.progress_pct);
          if (status.message) {
            setFrontDoorStep(status.message);
          } else if (status.stage) {
            setFrontDoorStep(`Stage: ${status.stage}`);
          } else if (status.current_step) {
            setFrontDoorStep(status.current_step);
          }

          if (status.status === 'ready' || status.progress_pct === 100) {
            if (frontDoorIntervalRef.current) {
              clearInterval(frontDoorIntervalRef.current);
              frontDoorIntervalRef.current = null;
            }
            setFrontDoorProgress(100);
            setFrontDoorStep(status.message || 'Ready! Opening repository overview...');
            if (onRefreshRepositories) await onRefreshRepositories();
            setTimeout(() => {
              if (onSelectRepo) onSelectRepo(targetRepoId);
              if (onNavigateToTab) onNavigateToTab('dashboard');
              setFrontDoorAnalyzing(false);
            }, 1000);
          } else if (status.status === 'failed') {
            if (frontDoorIntervalRef.current) {
              clearInterval(frontDoorIntervalRef.current);
              frontDoorIntervalRef.current = null;
            }
            setFrontDoorError(status.error || status.message || 'Analysis failed');
            setFrontDoorAnalyzing(false);
          }
        } catch {
          // ignore transient poll error
        }
      }, 1500);
    } catch (err: any) {
      if (frontDoorIntervalRef.current) {
        clearInterval(frontDoorIntervalRef.current);
        frontDoorIntervalRef.current = null;
      }
      setFrontDoorError(err.message || 'Failed to start ingestion');
      setFrontDoorAnalyzing(false);
    }
  };

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
      const ansRes = await askCodebase(
        selectedRepo || '',
        q,
        5,
        0.6,
        explanationMode,
        activeProvider,
        isReasonActive ? 'pro' : 'flash'
      );

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
    {
      label: 'Explain this repo',
      icon: Sparkles,
      query: selectedRepo
        ? `Explain what ${selectedRepo} does, its core purpose, and its high-level architecture.`
        : 'Explain the high-level architecture of this codebase.',
    },
    {
      label: 'Where is authentication handled?',
      icon: ShieldCheck,
      query: 'Where is authentication or authorization handled in this codebase? List key files and functions.',
    },
    {
      label: 'Which files should I read first?',
      icon: FileCode,
      query: 'Which files should a new contributor read first to understand how this project works?',
    },
  ];

  const isConversational = turns.length > 0;
  const isAnyLoading = turns.some((t) => t.isLoading);

  return (
    <div className="flex h-full bg-[#000000] text-[#ececec] font-sans overflow-hidden select-none">
      {/* Main Conversation & Search Canvas */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Header Bar */}
        <header className="h-12 px-4 flex items-center justify-between border-b border-[#18181b] bg-[#000000] shrink-0 z-20">
          <div className="flex items-center space-x-2">
            {/* Model Dropdown */}
            <div className="relative">
              <button
                onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl hover:bg-zinc-900 text-sm font-semibold text-white transition-colors cursor-pointer border border-transparent hover:border-zinc-800"
              >
                <span>{selectedModel}</span>
                <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />
              </button>

              {modelDropdownOpen && (
                <div className="absolute top-10 left-0 w-64 bg-[#08080a] border border-[#18181b] rounded-2xl shadow-2xl p-1.5 z-50 text-xs">
                  <div className="px-3 py-1.5 text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Model Engine
                  </div>
                  {[
                    { id: 'CodeLens AI (Gemini)', desc: 'Google Gemini 2.5 Flash / Pro cloud provider' },
                    { id: 'CodeLens AI (Local Qwen)', desc: '100% offline local embeddings + LLM' },
                  ].map((m) => (
                    <button
                      key={m.id}
                      onClick={() => {
                        setSelectedModel(m.id);
                        setModelDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-xl hover:bg-zinc-900 transition-colors flex flex-col cursor-pointer ${
                        selectedModel === m.id ? 'bg-zinc-900 text-white' : 'text-zinc-300'
                      }`}
                    >
                      <span className="font-medium text-white">{m.id}</span>
                      <span className="text-[11px] text-zinc-500">{m.desc}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Attached Repository Indicator Pill */}
            {selectedRepo ? (
              <button
                onClick={() => setIsAttachModalOpen(true)}
                className="flex items-center space-x-1.5 text-xs text-zinc-200 font-mono px-2.5 py-1 bg-[#08080a] hover:bg-zinc-900 rounded-lg border border-[#18181b] transition-colors cursor-pointer"
                title="Change or attach another repository"
              >
                <GithubIcon className="w-3.5 h-3.5 text-zinc-400" />
                <span>repo:</span>
                <strong className="text-white">{selectedRepo}</strong>
                <ChevronDown className="w-3 h-3 text-zinc-400 opacity-70" />
              </button>
            ) : (
              <button
                onClick={() => setIsAttachModalOpen(true)}
                className="flex items-center space-x-1.5 text-xs text-zinc-300 px-2.5 py-1 bg-[#08080a] hover:bg-zinc-900 rounded-lg border border-[#18181b] transition-colors cursor-pointer"
                title="Attach a GitHub repository"
              >
                <GithubIcon className="w-3.5 h-3.5 text-zinc-400" />
                <span>Attach GitHub Repo</span>
                <Plus className="w-3 h-3 text-zinc-400" />
              </button>
            )}
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center space-x-2">
            {/* Quick Attach GitHub Repo Button */}
            <button
              onClick={() => setIsAttachModalOpen(true)}
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-zinc-200 border border-zinc-700/80 transition-all cursor-pointer shadow-sm"
            >
              <GithubIcon className="w-3.5 h-3.5 text-zinc-300" />
              <span className="hidden sm:inline">Attach Repo</span>
            </button>

            {isConversational && (
              <button
                onClick={handleReset}
                className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg hover:bg-zinc-900 text-zinc-400 hover:text-white text-xs transition-colors cursor-pointer"
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
                    ? 'bg-zinc-800 text-white border border-zinc-600'
                    : 'hover:bg-zinc-900 text-zinc-400 hover:text-white'
                }`}
                title="Toggle Sources"
              >
                <Globe className="w-4 h-4" />
                <span>Sources</span>
                <span className="px-1.5 py-0.5 rounded-full bg-zinc-900 text-[10px] font-mono text-zinc-200 border border-zinc-700">
                  {activeSources.length}
                </span>
              </button>
            )}
          </div>
        </header>

        {/* Cloud AI Privacy Notice Banner (Active when Gemini provider is selected) */}
        {activeProvider === 'gemini' && selectedRepo && (
          <div className="bg-[#08080a] border-b border-[#18181b] px-4 py-2 flex items-center justify-between text-xs text-zinc-300 shrink-0">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-zinc-400 shrink-0" />
              <span>
                <strong>Cloud AI Notice:</strong> CodeLens is using Gemini Flash/Pro. Code context from <code className="text-white bg-zinc-900 px-1 py-0.5 rounded font-mono border border-zinc-800">{selectedRepo}</code> will be processed by Google APIs.
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={async () => {
                  await setLLMProvider('local');
                  setActiveProvider('local');
                  setSelectedModel('Local ML Engine');
                }}
                className="px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/80 transition-colors cursor-pointer text-[11px]"
              >
                Switch to Local
              </button>
            </div>
          </div>
        )}

        {/* Scrollable Viewport */}
        <div
          ref={chatScrollContainerRef}
          className="flex-1 overflow-y-auto px-4 py-8 flex flex-col items-center"
        >
          {!isConversational ? (
            /* ================= INITIAL HOME VIEW ================= */
            !selectedRepo ? (
              /* ================= FRONT DOOR: NO REPO ATTACHED ================= */
              <div className="w-full max-w-4xl flex flex-col items-center text-center animate-in fade-in duration-300 pb-12">
                <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-700 flex items-center justify-center text-white mb-4 shadow-xl">
                  <Compass className="w-6 h-6" />
                </div>
                <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-2 font-sans">
                  CodeLens Intelligence
                </h1>
                <p className="text-sm text-zinc-400 max-w-xl mb-8">
                  Attach any public GitHub repository to index code symbols, explore architectures, and ask questions with cited AST sources.
                </p>

                {/* Primary Front Door Input Card */}
                <div className="w-full max-w-2xl bg-[#08080a] border border-[#18181b] rounded-2xl p-5 mb-8 text-left shadow-2xl">
                  <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                    Attach GitHub Repository
                  </label>
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                    <div className="relative flex-1">
                      <GithubIcon className="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="url"
                        value={frontDoorUrl}
                        onChange={(e) => setFrontDoorUrl(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleFrontDoorAnalyze();
                        }}
                        placeholder="https://github.com/owner/repository"
                        disabled={frontDoorAnalyzing}
                        className="w-full pl-10 pr-3 py-2.5 rounded-xl bg-[#000000] border border-[#1c1c21] text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 font-mono"
                      />
                    </div>
                    <button
                      onClick={() => handleFrontDoorAnalyze()}
                      disabled={!frontDoorUrl.trim() || frontDoorAnalyzing}
                      className="px-5 py-2.5 rounded-xl bg-white hover:bg-zinc-200 disabled:opacity-50 text-black text-sm font-semibold flex items-center justify-center space-x-2 shadow-sm cursor-pointer disabled:cursor-not-allowed transition-all"
                    >
                      {frontDoorAnalyzing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin text-black" />
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-black" />
                          <span>Analyze in CodeLens</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Progress Indicator */}
                  {frontDoorAnalyzing && (
                    <div className="mt-4 pt-4 border-t border-[#18181b] space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-white flex items-center space-x-1.5">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>{frontDoorStep}</span>
                        </span>
                        <span className="font-mono text-zinc-400">{frontDoorProgress}%</span>
                      </div>
                      <div className="h-2 w-full bg-[#000000] rounded-full overflow-hidden border border-[#18181b]">
                        <div
                          className="h-full bg-white transition-all duration-300"
                          style={{ width: `${frontDoorProgress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Error Notification */}
                  {frontDoorError && (
                    <div className="mt-3 p-3 rounded-xl bg-zinc-900 border border-zinc-700 text-rose-400 text-xs flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                        <span>{frontDoorError}</span>
                      </div>
                      <button
                        onClick={() => handleFrontDoorAnalyze()}
                        className="px-2.5 py-1 bg-white hover:bg-zinc-200 text-black rounded-lg text-xs font-semibold shrink-0 transition"
                      >
                        Retry
                      </button>
                    </div>
                  )}

                  {/* Quick Presets */}
                  <div className="mt-4 flex flex-wrap items-center gap-2 pt-3 border-t border-[#18181b]">
                    <span className="text-[11px] text-zinc-500">Quick presets:</span>
                    {presetRepos.map((p) => (
                      <button
                        key={p.name}
                        onClick={() => {
                          setFrontDoorUrl(p.url);
                          handleFrontDoorAnalyze(p.url);
                        }}
                        disabled={frontDoorAnalyzing}
                        className="px-2.5 py-1 rounded-lg bg-[#000000] hover:bg-zinc-900 border border-[#1c1c21] text-[11px] font-mono text-zinc-400 hover:text-white transition-colors cursor-pointer"
                      >
                        {p.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Explore Feed Preview */}
                <div className="w-full text-left space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-white">
                        Trending Repositories to Explore
                      </h2>
                      <p className="text-xs text-zinc-400">
                        Pick any top open-source project to analyze its architecture and ask questions.
                      </p>
                    </div>
                    {onNavigateToTab && (
                      <button
                        onClick={() => onNavigateToTab('explore')}
                        className="text-xs text-zinc-400 hover:text-white flex items-center space-x-1 cursor-pointer"
                      >
                        <span>View all in Explore</span>
                        <ChevronDown className="w-3.5 h-3.5 -rotate-90" />
                      </button>
                    )}
                  </div>

                  {loadingExploreFeed ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                      {[1, 2, 3, 4, 5, 6].map((i) => (
                        <div key={i} className="h-36 rounded-xl bg-[#08080a] animate-pulse border border-[#18181b]" />
                      ))}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                      {exploreFeedRepos.slice(0, 6).map((repo) => (
                        <div
                          key={repo.name}
                          className="bg-[#08080a] hover:bg-[#0c0c0e] border border-[#18181b] hover:border-[#27272a] rounded-xl p-4 flex flex-col justify-between transition-all group"
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-xs font-mono font-semibold text-white group-hover:text-zinc-200 truncate">
                                {repo.name}
                              </span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#000000] border border-[#1c1c21] text-zinc-300 font-mono">
                                {repo.readiness?.score || 85}/100
                              </span>
                            </div>
                            <p className="text-xs text-zinc-400 line-clamp-2 mb-3 leading-relaxed">
                              {repo.description || 'No description provided.'}
                            </p>
                          </div>

                          <div className="flex items-center justify-between pt-2 border-t border-[#18181b] text-[11px] text-zinc-500">
                            <div className="flex items-center space-x-3">
                              <span className="text-zinc-400 font-medium">{repo.language}</span>
                              <span className="flex items-center space-x-1">
                                <Star className="w-3 h-3 text-zinc-400" />
                                <span>{(repo.stars / 1000).toFixed(1)}k</span>
                              </span>
                            </div>

                            <button
                              onClick={() => {
                                setFrontDoorUrl(repo.html_url);
                                handleFrontDoorAnalyze(repo.html_url);
                              }}
                              disabled={frontDoorAnalyzing}
                              className="px-2.5 py-1 rounded-lg bg-white hover:bg-zinc-200 text-black text-xs font-semibold flex items-center space-x-1 transition-all cursor-pointer shadow-sm"
                            >
                              <Sparkles className="w-3 h-3 text-black" />
                              <span>Analyze</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* ================= REPO ATTACHED: HERO PROMPT VIEW ================= */
              <div className="w-full max-w-[768px] my-auto flex flex-col items-center text-center animate-in fade-in duration-300">
                <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-white mb-2 font-sans">
                  What can I help with?
                </h1>
                <p className="text-xs font-mono text-zinc-400 mb-8">
                  attached: <strong className="text-white">{selectedRepo}</strong>
                </p>

                {/* Signature Composer Capsule */}
                <div className="w-full bg-[#08080a] hover:bg-[#0c0c0e] focus-within:bg-[#08080a] border border-[#18181b] focus-within:border-zinc-700 focus-within:ring-1 focus-within:ring-zinc-700 rounded-[26px] shadow-2xl transition-all p-3.5 flex flex-col mb-5 text-left">
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
                        : `Ask CodeLens AI about ${selectedRepo}...`
                    }
                    className="w-full bg-transparent text-white placeholder-zinc-500 text-base resize-none focus:outline-none px-1.5 pt-0.5 pb-2 leading-relaxed font-sans min-h-[44px] max-h-48"
                  />

                  {/* Internal Composer Toolbar */}
                  <div className="flex items-center justify-between pt-1">
                    {/* Left: Search Only toggle, Attach Repo, Reason toggle, Mode toggle */}
                    <div className="flex items-center space-x-1.5">
                      {/* Attach GitHub Repo button (+) */}
                      <button
                        type="button"
                        onClick={() => setIsAttachModalOpen(true)}
                        className="p-1.5 rounded-full hover:bg-zinc-900 text-zinc-400 hover:text-white transition-colors cursor-pointer group"
                        title="Attach GitHub Repository"
                      >
                        <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
                      </button>

                      {/* Dedicated Attach Repo Pill */}
                      <button
                        type="button"
                        onClick={() => setIsAttachModalOpen(true)}
                        className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer bg-[#000000] text-zinc-200 border border-[#1c1c21] hover:bg-zinc-900"
                        title={`Attached: ${selectedRepo}`}
                      >
                        <GithubIcon className="w-3.5 h-3.5 text-zinc-400" />
                        <span>{selectedRepo}</span>
                      </button>

                      {/* Search Only Toggle Pill */}
                      <button
                        type="button"
                        onClick={() => setIsSearchOnly(!isSearchOnly)}
                        className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                          isSearchOnly
                            ? 'bg-zinc-800 text-white border border-zinc-600'
                            : 'bg-[#000000] text-zinc-400 hover:text-white border border-[#1c1c21] hover:bg-zinc-900'
                        }`}
                        title={isSearchOnly ? 'Search only mode is ON (no LLM generation, fast code chunk hits)' : 'Enable Search only mode'}
                      >
                        <Search className={`w-3.5 h-3.5 ${isSearchOnly ? 'text-white' : 'text-zinc-400'}`} />
                        <span>Search only</span>
                        <span className={`w-1.5 h-1.5 rounded-full ${isSearchOnly ? 'bg-white animate-pulse' : 'bg-zinc-600'}`} />
                      </button>

                      {/* Reason Toggle Pill */}
                      <button
                        type="button"
                        onClick={() => setIsReasonActive(!isReasonActive)}
                        className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                          isReasonActive
                            ? 'bg-zinc-800 text-white border border-zinc-600'
                            : 'hover:bg-zinc-900 text-zinc-400'
                        }`}
                        title="Deep Reasoning Mode"
                      >
                        <Brain className="w-3.5 h-3.5" />
                        <span>Reason</span>
                      </button>

                      {/* Explanation Mode Toggle Pill (Beginner vs Expert) */}
                      <button
                        type="button"
                        onClick={() => setExplanationMode(explanationMode === 'beginner' ? 'expert' : 'beginner')}
                        className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer bg-[#000000] text-zinc-300 border border-[#1c1c21] hover:bg-zinc-900"
                        title="Toggle explanation style between Beginner (student friendly) and Expert (architectural depth)"
                      >
                        <span>{explanationMode === 'beginner' ? '🎓 Beginner' : '⚡ Expert'}</span>
                      </button>
                    </div>

                    {/* Right: Mic & Circular Up Arrow Send Button */}
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => setIsListening(!isListening)}
                        className={`p-1.5 rounded-full hover:bg-zinc-900 transition-colors cursor-pointer ${
                          isListening ? 'text-rose-400 animate-pulse' : 'text-zinc-400 hover:text-white'
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
                            ? 'bg-white text-black hover:bg-zinc-200 hover:scale-105 shadow-md cursor-pointer'
                            : 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
                        }`}
                        title="Send message"
                      >
                        <ArrowUp className="w-4 h-4 stroke-[2.5]" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Repo-Specific Action Pills Underneath Search Bar */}
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
                            ? 'bg-[#08080a] hover:bg-zinc-900 border border-zinc-700 text-white font-medium shadow-sm'
                            : 'bg-[#000000] hover:bg-zinc-900 border border-[#1c1c21] text-zinc-400 hover:text-white'
                        }`}
                      >
                        <Icon className={`w-3.5 h-3.5 ${pill.isSpecial ? 'text-zinc-200' : 'text-zinc-400'}`} />
                        <span>{pill.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Helper Note */}
                <div className="text-[11px] text-zinc-500 mt-6">
                  Answers cite exact file paths and line ranges. Low retrieval confidence will report &ldquo;not found in this codebase&rdquo;.
                </div>
              </div>
            )
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
                        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-zinc-800 border border-zinc-600 text-xs text-zinc-200">
                          <Search className="w-3.5 h-3.5 text-white" />
                          <span className="font-medium">Search Only Mode</span>
                          {turn.searchResponse && (
                            <span className="text-[11px] text-zinc-400">
                              • {turn.searchResponse.results.length} matches
                            </span>
                          )}
                          {turn.latencyMs !== undefined && (
                            <span className="text-[10px] font-mono text-zinc-500">
                              ({turn.latencyMs.toFixed(0)}ms)
                            </span>
                          )}
                        </div>
                      ) : turn.searchResponse && turn.searchResponse.results.length > 0 ? (
                        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#08080a] border border-[#18181b] text-xs text-zinc-300">
                          <Globe className="w-3.5 h-3.5 text-zinc-400" />
                          <span>Searched {turn.searchResponse.results.length} code sources</span>
                          {turn.latencyMs !== undefined && (
                            <span className="text-[10px] font-mono text-zinc-500">
                              ({turn.latencyMs.toFixed(0)}ms)
                            </span>
                          )}
                          <button
                            onClick={() => {
                              setActiveSources(turn.searchResponse?.results || []);
                              setShowSourcesPanel(true);
                            }}
                            className="text-white hover:underline font-medium cursor-pointer ml-1"
                          >
                            View sources →
                          </button>
                        </div>
                      ) : turn.isGeneralAi ? (
                        <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-zinc-900 border border-zinc-700 text-[11px] text-zinc-200">
                          <Sparkles className="w-3 h-3 text-zinc-400" />
                          <span>CodeLens General AI</span>
                          {turn.latencyMs !== undefined && (
                            <span className="text-[10px] font-mono text-zinc-500">
                              ({turn.latencyMs.toFixed(0)}ms)
                            </span>
                          )}
                        </div>
                      ) : null}

                      {/* Thinking Pulse while loading */}
                      {turn.isLoading && (
                        <div className="flex items-center space-x-2.5 text-sm text-zinc-400 py-3">
                          <div className="w-3 h-3 rounded-full animate-pulse bg-white" />
                          <span>
                            {turn.isSearchOnly
                              ? 'Searching AST chunks and BM25+FAISS vector index...'
                              : 'Reasoning & synthesizing response...'}
                          </span>
                        </div>
                      )}

                      {/* Error message */}
                      {turn.error && (
                        <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-700 text-rose-400 text-xs flex items-center space-x-2">
                          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                          <span>{turn.error}</span>
                        </div>
                      )}

                      {/* SEARCH ONLY VIEW: Render code chunk cards */}
                      {turn.isSearchOnly && !turn.isLoading && turn.searchResponse && (
                        <div className="space-y-3.5 pt-1">
                          {turn.searchResponse.results.length === 0 ? (
                            <div className="p-6 text-center text-xs text-zinc-400 bg-[#08080a] border border-[#18181b] rounded-xl">
                              No matching code chunks found for &ldquo;{turn.query}&rdquo;. Try another symbol or search term.
                            </div>
                          ) : (
                            turn.searchResponse.results.map((item, idx) => {
                              const cardKey = `search_${turn.id}_${idx}`;
                              return (
                                <div
                                  key={cardKey}
                                  className="bg-[#08080a] border border-[#18181b] hover:border-zinc-700 rounded-xl overflow-hidden shadow-sm transition-all"
                                >
                                  {/* Card Header */}
                                  <div className="px-3.5 py-2.5 bg-[#000000] border-b border-[#18181b] flex flex-wrap items-center justify-between gap-2">
                                    <div className="flex items-center space-x-2">
                                      <span className="w-5 h-5 rounded-full bg-zinc-800 text-white border border-zinc-600 flex items-center justify-center text-[10px] font-bold font-mono">
                                        #{item.rank || idx + 1}
                                      </span>
                                      <button
                                        onClick={() => onOpenFileInExplorer(item.file_path)}
                                        className="font-mono text-xs font-semibold text-white hover:underline cursor-pointer"
                                      >
                                        {item.file_path.split('/').pop()}
                                      </button>
                                      <span className="text-[11px] text-zinc-500 font-mono">
                                        (L{item.start_line}–{item.end_line})
                                      </span>
                                      {item.symbol && (
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-900 text-zinc-200 border border-zinc-700">
                                          {item.chunk_type}: {item.symbol}
                                        </span>
                                      )}
                                    </div>

                                    <div className="flex items-center space-x-2">
                                      <span className="text-[10px] font-mono bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded text-zinc-300">
                                        {(item.similarity * 100).toFixed(1)}% match
                                      </span>
                                      <button
                                        onClick={() => {
                                          navigator.clipboard.writeText(item.code);
                                          setCopiedId(cardKey);
                                          setTimeout(() => setCopiedId(null), 2000);
                                        }}
                                        className="p-1 text-zinc-400 hover:text-white rounded hover:bg-zinc-800 transition-colors cursor-pointer"
                                        title="Copy code snippet"
                                      >
                                        {copiedId === cardKey ? (
                                          <Check className="w-3.5 h-3.5 text-white" />
                                        ) : (
                                          <Copy className="w-3.5 h-3.5" />
                                        )}
                                      </button>
                                      <button
                                        onClick={() => onOpenFileInExplorer(item.file_path)}
                                        className="flex items-center space-x-1 px-2 py-1 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-[11px] font-medium transition-colors cursor-pointer border border-zinc-700"
                                      >
                                        <span>Open in Explorer</span>
                                        <ExternalLink className="w-3 h-3" />
                                      </button>
                                    </div>
                                  </div>

                                  {/* File path sub-bar */}
                                  <div className="px-3.5 py-1.5 bg-[#08080a] border-b border-[#18181b] text-[11px] font-mono text-zinc-500 flex items-center justify-between">
                                    <span className="truncate">{item.file_path}</span>
                                    {item.docstring && (
                                      <span className="italic text-zinc-400 truncate max-w-[50%]">
                                        &ldquo;{item.docstring}&rdquo;
                                      </span>
                                    )}
                                  </div>

                                  {/* Code Block with Line Numbers */}
                                  <div className="p-3.5 bg-[#000000] overflow-x-auto text-xs font-mono text-zinc-200 leading-relaxed max-h-72">
                                    <pre>
                                      {item.code.split('\n').map((line, lineIdx) => {
                                        const currentLineNum = item.start_line + lineIdx;
                                        return (
                                          <div key={lineIdx} className="table-row hover:bg-zinc-900/60">
                                            <span className="table-cell select-none text-zinc-600 pr-4 text-right opacity-60 w-8">
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
                            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                              Referenced Code Files
                            </span>
                            {turn.searchResponse && (
                              <button
                                onClick={() => {
                                  setActiveSources(turn.searchResponse?.results || []);
                                  setShowSourcesPanel(true);
                                }}
                                className="text-xs text-zinc-300 hover:text-white hover:underline cursor-pointer"
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
                                className="p-3 rounded-xl bg-[#08080a] hover:bg-zinc-900 border border-[#18181b] text-left transition-colors cursor-pointer group flex flex-col justify-between"
                              >
                                <div className="flex items-center justify-between w-full mb-1">
                                  <span className="text-xs font-mono font-medium text-white truncate group-hover:text-zinc-200">
                                    {src.file_path.split('/').pop()}
                                  </span>
                                  <span className="text-[10px] font-mono text-zinc-300 bg-zinc-900 border border-zinc-700 px-1.5 py-0.5 rounded">
                                    {(src.similarity * 100).toFixed(0)}%
                                  </span>
                                </div>
                                <p className="text-[11px] text-zinc-500 truncate font-mono">
                                  {src.file_path} (L{src.start_line}–{src.end_line})
                                </p>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Bottom Action Row (Copy, Thumbs, Share) */}
                      {!turn.isLoading && turn.answer && (
                        <div className="flex items-center space-x-1 pt-2 text-zinc-400">
                          <button
                            onClick={() => handleCopyAnswer(turn.id, turn.answer)}
                            className="p-1.5 rounded-lg hover:bg-zinc-900 hover:text-white transition-colors cursor-pointer"
                            title="Copy answer"
                          >
                            {copiedId === turn.id ? (
                              <Check className="w-4 h-4 text-white" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>

                          <button
                            onClick={() => toggleFeedback(turn.id, 'up')}
                            className={`p-1.5 rounded-lg hover:bg-zinc-900 transition-colors cursor-pointer ${
                              turn.feedback === 'up' ? 'text-white bg-zinc-800' : 'hover:text-white'
                            }`}
                            title="Good response"
                          >
                            <ThumbsUp className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => toggleFeedback(turn.id, 'down')}
                            className={`p-1.5 rounded-lg hover:bg-zinc-900 transition-colors cursor-pointer ${
                              turn.feedback === 'down' ? 'text-rose-400 bg-zinc-800' : 'hover:text-white'
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
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#000000] via-[#000000]/95 to-transparent z-20 flex flex-col items-center">
            <div className="w-full max-w-[768px] flex flex-col">
              <div className="w-full bg-[#08080a] hover:bg-[#0c0c0e] focus-within:bg-[#08080a] border border-[#18181b] focus-within:border-zinc-700 focus-within:ring-1 focus-within:ring-zinc-700 rounded-[26px] shadow-2xl p-3 flex flex-col transition-all">
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
                  className="w-full bg-transparent text-white placeholder-zinc-500 text-base resize-none focus:outline-none px-1.5 pt-0.5 pb-2 leading-relaxed font-sans min-h-[36px] max-h-36"
                />

                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center space-x-1.5">
                    {/* Attach Repo (+) */}
                    <button
                      type="button"
                      onClick={() => setIsAttachModalOpen(true)}
                      className="p-1.5 rounded-full hover:bg-zinc-900 text-zinc-400 hover:text-white transition-colors cursor-pointer group"
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
                          ? 'bg-[#000000] text-zinc-200 border border-[#1c1c21]'
                          : 'bg-zinc-900 text-zinc-400 border border-zinc-800'
                      }`}
                    >
                      <GithubIcon className="w-3.5 h-3.5 text-zinc-400" />
                      <span>{selectedRepo ? selectedRepo : 'Attach Repo'}</span>
                    </button>

                    {/* Search Only Toggle Pill */}
                    <button
                      type="button"
                      onClick={() => setIsSearchOnly(!isSearchOnly)}
                      className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                        isSearchOnly
                          ? 'bg-zinc-800 text-white border border-zinc-600'
                          : 'bg-[#000000] text-zinc-400 hover:text-white border border-[#1c1c21]'
                      }`}
                      title={isSearchOnly ? 'Search only mode is ON (no LLM generation, fast code chunk hits)' : 'Enable Search only mode'}
                    >
                      <Search className={`w-3.5 h-3.5 ${isSearchOnly ? 'text-white' : 'text-zinc-400'}`} />
                      <span>Search only</span>
                      <span className={`w-1.5 h-1.5 rounded-full ${isSearchOnly ? 'bg-white animate-pulse' : 'bg-zinc-600'}`} />
                    </button>

                    {/* Reason Toggle Pill */}
                    <button
                      type="button"
                      onClick={() => setIsReasonActive(!isReasonActive)}
                      className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                        isReasonActive
                          ? 'bg-zinc-800 text-white border border-zinc-600'
                          : 'hover:bg-zinc-900 text-zinc-400'
                      }`}
                    >
                      <Brain className="w-3.5 h-3.5" />
                      <span>Reason</span>
                    </button>

                    {/* Explanation Mode Toggle Pill (Beginner vs Expert) */}
                    <button
                      type="button"
                      onClick={() => setExplanationMode(explanationMode === 'beginner' ? 'expert' : 'beginner')}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer bg-[#000000] text-zinc-300 border border-[#1c1c21] hover:bg-zinc-900"
                      title="Switch between student-friendly Beginner mode and architectural Expert mode"
                    >
                      <span>{explanationMode === 'beginner' ? '🎓 Beginner' : '⚡ Expert'}</span>
                    </button>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => handleSearch()}
                      disabled={!inputQuery.trim() || isAnyLoading}
                      className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                        inputQuery.trim() && !isAnyLoading
                          ? 'bg-white text-black hover:bg-zinc-200 hover:scale-105 shadow-md cursor-pointer'
                          : 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
                      }`}
                      title="Send message"
                    >
                      <ArrowUp className="w-4 h-4 stroke-[2.5]" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Subtext Disclaimer */}
              <div className="text-[11px] text-zinc-500 text-center mt-2">
                CodeLens AI can make mistakes. Always review code before deploying.
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sources Side Panel Drawer (Right Rail) */}
      {showSourcesPanel && (
        <aside className="w-80 border-l border-[#18181b] bg-[#08080a] flex flex-col h-full z-30 shrink-0 animate-in slide-in-from-right duration-200">
          <div className="h-12 px-4 flex items-center justify-between border-b border-[#18181b] shrink-0">
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4 text-zinc-400" />
              <h3 className="text-sm font-semibold text-white">Sources</h3>
              <span className="text-xs text-zinc-500 font-mono">
                ({activeSources.length})
              </span>
            </div>
            <button
              onClick={() => setShowSourcesPanel(false)}
              className="p-1 rounded-md hover:bg-zinc-900 text-zinc-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {activeSources.length > 0 ? (
              activeSources.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-[#000000] border border-[#18181b] hover:border-zinc-700 transition-all"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-mono font-semibold text-white truncate">
                      {item.file_path.split('/').pop()}
                    </span>
                    <span className="text-[10px] font-mono text-zinc-300 bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-700">
                      {(item.similarity * 100).toFixed(0)}%
                    </span>
                  </div>

                  <p className="text-[11px] font-mono text-zinc-400 truncate mb-2">
                    {item.file_path} {item.start_line && `(L${item.start_line}–${item.end_line})`}
                  </p>

                  <pre className="p-2 text-[10px] font-mono text-zinc-300 bg-[#08080a] rounded-lg overflow-x-auto max-h-28 border border-[#18181b]">
                    <code>{item.code}</code>
                  </pre>

                  <button
                    onClick={() => onOpenFileInExplorer(item.file_path)}
                    className="w-full mt-2.5 flex items-center justify-center space-x-1.5 py-1 px-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-[11px] text-white font-medium transition-colors cursor-pointer border border-zinc-700"
                  >
                    <span>Open in Code Explorer</span>
                    <ExternalLink className="w-3 h-3 text-zinc-400" />
                  </button>
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-xs text-zinc-500">
                No sources loaded yet. Perform a query with an attached repo to inspect code chunks.
              </div>
            )}
          </div>
        </aside>
      )}

      {/* ================= ATTACH GITHUB REPOSITORY MODAL ================= */}
      {isAttachModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-xl bg-[#08080a] border border-[#18181b] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-[#18181b] flex items-center justify-between bg-[#000000]">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-700 flex items-center justify-center text-white">
                  <GithubIcon className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Attach GitHub Repository</h3>
                  <p className="text-xs text-zinc-400">
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
                className="p-1.5 rounded-lg hover:bg-zinc-900 text-zinc-400 hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Clone Remote Repository Section */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">
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
                      className="w-full px-3.5 py-2.5 bg-[#000000] border border-[#1c1c21] focus:border-zinc-500 rounded-xl text-sm text-white placeholder-zinc-500 focus:outline-none transition-all font-mono"
                    />
                  </div>
                  <button
                    onClick={() => handleAttachGithubRepo()}
                    disabled={!gitUrlInput.trim() || isIngesting}
                    className={`px-4 py-2.5 rounded-xl font-semibold text-sm flex items-center space-x-1.5 transition-all ${
                      gitUrlInput.trim() && !isIngesting
                        ? 'bg-white hover:bg-zinc-200 text-black shadow-sm cursor-pointer'
                        : 'bg-zinc-900 text-zinc-600 border border-zinc-800 cursor-not-allowed'
                    }`}
                  >
                    {isIngesting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-black" />
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
                  <span className="text-[11px] text-zinc-500 block mb-2">Or attach a popular open-source preset:</span>
                  <div className="flex flex-wrap gap-2">
                    {presetRepos.map((preset) => (
                      <button
                        key={preset.name}
                        onClick={() => {
                          setGitUrlInput(preset.url);
                          handleAttachGithubRepo(preset.url);
                        }}
                        disabled={isIngesting}
                        className="px-2.5 py-1 rounded-lg bg-[#000000] hover:bg-zinc-900 border border-[#1c1c21] text-xs text-zinc-400 hover:text-white transition-all cursor-pointer flex items-center space-x-1.5"
                      >
                        <GithubIcon className="w-3 h-3 text-zinc-400" />
                        <span>{preset.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Ingestion Progress View */}
              {isIngesting && (
                <div className="p-4 rounded-xl bg-[#000000] border border-[#18181b] space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-white flex items-center space-x-2">
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                      <span>{ingestStatusStep}</span>
                    </span>
                    <span className="font-mono text-zinc-400 font-bold">{ingestProgress}%</span>
                  </div>
                  <div className="w-full h-2 bg-[#08080a] rounded-full overflow-hidden border border-[#18181b]">
                    <div
                      className="h-full bg-white transition-all duration-300 rounded-full"
                      style={{ width: `${ingestProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Ingestion Success View */}
              {ingestSuccessRepo && (
                <div className="p-3.5 rounded-xl bg-zinc-900 border border-zinc-700 text-white text-xs flex items-center space-x-2 animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4 text-white shrink-0" />
                  <span>
                    Successfully attached <strong>{ingestSuccessRepo}</strong>! Switching active context...
                  </span>
                </div>
              )}

              {/* Error Message */}
              {ingestError && (
                <div className="p-3.5 rounded-xl bg-zinc-900 border border-zinc-700 text-rose-400 text-xs flex items-center space-x-2 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{ingestError}</span>
                </div>
              )}

              {/* Available / Already Indexed Repositories List */}
              <div className="space-y-3 pt-2 border-t border-[#18181b]">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                    Already Indexed Repositories ({repositories.length})
                  </label>
                  {onRefreshRepositories && (
                    <button
                      onClick={() => onRefreshRepositories()}
                      className="text-xs text-zinc-300 hover:text-white hover:underline cursor-pointer"
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
                              ? 'bg-zinc-900 border-zinc-600'
                              : 'bg-[#000000] border-[#1c1c21] hover:border-zinc-700'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <FolderGit2 className={`w-4 h-4 ${isActive ? 'text-white' : 'text-zinc-500'}`} />
                            <div>
                              <div className="text-sm font-semibold text-white flex items-center space-x-2">
                                <span>{repo.repository_name}</span>
                                {isActive && (
                                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-white text-black font-semibold">
                                    Active
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-zinc-500 flex items-center space-x-2">
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
                              className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-white transition-colors cursor-pointer border border-zinc-700"
                            >
                              Attach
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-6 text-xs text-zinc-500">
                    No repositories indexed yet. Enter a GitHub URL above to clone one!
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 border-t border-[#18181b] bg-[#000000] flex items-center justify-end">
              <button
                onClick={() => setIsAttachModalOpen(false)}
                disabled={isIngesting}
                className="px-4 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-white transition-colors cursor-pointer border border-zinc-700"
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
