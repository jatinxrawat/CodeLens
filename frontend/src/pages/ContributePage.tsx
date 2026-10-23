import React, { useState, useEffect, useRef } from 'react';
import {
  GitPullRequest,
  Sparkles,
  ExternalLink,
  Search,
  RotateCcw,
  Bookmark,
  CheckCircle2,
  Clock,
  Layers,
  FileCode,
  Tag,
  Briefcase,
  AlertCircle,
  Loader2,
  X,
  Compass,
  ArrowRight,
  ShieldCheck,
  Flame,
  Award,
  RefreshCw,
} from 'lucide-react';
import type { ContributeIssueItem, UserProfile } from '../types';
import {
  fetchContributeIssues,
  analyzeRepository,
  fetchRepoStatus,
  fetchUserProfile,
  toggleBookmark,
  toggleWorking,
} from '../services/api';

interface ContributePageProps {
  onSelectRepo: (repoId: string) => void;
  onNavigateToTab: (tab: string) => void;
  onRefreshRepositories?: () => Promise<void>;
}

export const ContributePage: React.FC<ContributePageProps> = ({
  onSelectRepo,
  onNavigateToTab,
  onRefreshRepositories,
}) => {
  const [issues, setIssues] = useState<ContributeIssueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active view: 'all' or 'my_contributions'
  const [activeTab, setActiveTab] = useState<'all' | 'my_contributions'>('all');

  // User Profile, Bookmarks, and Working list
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<string>>(new Set());
  const [workingIds, setWorkingIds] = useState<Set<string>>(new Set());

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('All');
  const [selectedDomain, setSelectedDomain] = useState('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Issue Detail Drawer
  const [selectedIssue, setSelectedIssue] = useState<ContributeIssueItem | null>(null);

  // Ingestion Modal State
  const [analyzingRepoUrl, setAnalyzingRepoUrl] = useState<string | null>(null);
  const [analyzingRepoName, setAnalyzingRepoName] = useState<string>('');
  const [analyzingIssue, setAnalyzingIssue] = useState<ContributeIssueItem | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState<number>(0);
  const [analysisStage, setAnalysisStage] = useState<string>('Queued');
  const [analysisMessage, setAnalysisMessage] = useState<string>('Preparing repository analysis...');
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const pollIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, []);

  // Seasonal Banner dismiss state
  const [showBanner, setShowBanner] = useState(true);

  const languages = ['All', 'Python', 'TypeScript', 'JavaScript', 'Go', 'Rust', 'C++'];
  const domains = ['All', 'AI/ML', 'Web', 'DevOps', 'Mobile'];
  const difficulties = ['All', 'Easy', 'Medium', 'Hard'];

  const loadUserData = async () => {
    try {
      const prof = await fetchUserProfile();
      setUserProfile(prof);
      setBookmarkedIds(new Set(prof.bookmarks.map((b) => b.issue_id)));
      setWorkingIds(new Set(prof.working.map((w) => w.issue_id)));
    } catch {
      // ignore guest error
    }
  };

  const loadIssues = async (isNewSearch: boolean = false) => {
    try {
      if (isNewSearch) {
        setLoading(true);
        setPage(1);
      }
      setError(null);
      const currentPage = isNewSearch ? 1 : page;
      const resp = await fetchContributeIssues({
        language: selectedLanguage !== 'All' ? selectedLanguage : undefined,
        domain: selectedDomain !== 'All' ? selectedDomain : undefined,
        difficulty: selectedDifficulty !== 'All' ? selectedDifficulty.toLowerCase() : undefined,
        q: searchQuery.trim() || undefined,
        page: currentPage,
        per_page: 15,
      });

      if (isNewSearch) {
        setIssues(resp.issues);
      } else {
        setIssues((prev) => [...prev, ...resp.issues]);
      }
      setHasMore(resp.issues.length >= 15);
    } catch (err: any) {
      console.error('Failed to load contribute issues:', err);
      setError(err.message || 'Failed to load contribution issues');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUserData();
    loadIssues(true);
  }, [selectedLanguage, selectedDomain, selectedDifficulty]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadIssues(true);
  };

  const handleLoadMore = () => {
    setPage((prev) => prev + 1);
  };

  useEffect(() => {
    if (page > 1) {
      loadIssues(false);
    }
  }, [page]);

  const handleToggleBookmark = async (e: React.MouseEvent, issue: ContributeIssueItem) => {
    e.stopPropagation();
    try {
      const res = await toggleBookmark({
        issue_id: issue.id,
        repo_name: issue.repository,
        title: issue.title,
        url: issue.html_url,
      });
      setBookmarkedIds((prev) => {
        const next = new Set(prev);
        if (res.is_bookmarked) {
          next.add(issue.id);
        } else {
          next.delete(issue.id);
        }
        return next;
      });
      await loadUserData();
    } catch (err) {
      console.error('Failed to toggle bookmark:', err);
    }
  };

  const handleToggleWorking = async (e: React.MouseEvent, issue: ContributeIssueItem) => {
    e.stopPropagation();
    try {
      const res = await toggleWorking({
        issue_id: issue.id,
        repo_name: issue.repository,
        title: issue.title,
        url: issue.html_url,
      });
      setWorkingIds((prev) => {
        const next = new Set(prev);
        if (res.is_working) {
          next.add(issue.id);
        } else {
          next.delete(issue.id);
        }
        return next;
      });
      await loadUserData();
    } catch (err) {
      console.error('Failed to toggle working status:', err);
    }
  };

  const handleAnalyze = async (issue: ContributeIssueItem) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    try {
      const gitUrl = issue.repository_url.startsWith('http')
        ? issue.repository_url
        : `https://github.com/${issue.repository}`;

      setAnalyzingIssue(issue);
      setAnalyzingRepoUrl(gitUrl);
      setAnalyzingRepoName(issue.repository);
      setAnalysisProgress(5);
      setAnalysisStage('Queued');
      setAnalysisMessage('Job queued for analysis...');
      setAnalysisError(null);

      const jobResp = await analyzeRepository(gitUrl);
      const targetRepoId = jobResp.repo_id;
      if (jobResp.stage) setAnalysisStage(jobResp.stage);
      if (jobResp.message) setAnalysisMessage(jobResp.message);
      if (typeof jobResp.progress_pct === 'number') setAnalysisProgress(jobResp.progress_pct);

      let attempts = 0;
      const maxAttempts = 150; // ~5 minutes max polling

      pollIntervalRef.current = window.setInterval(async () => {
        attempts += 1;
        if (attempts > maxAttempts) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setAnalysisStage('Failed');
          setAnalysisProgress(0);
          setAnalysisError('Analysis timed out. Please try again.');
          return;
        }

        try {
          const statusResp = await fetchRepoStatus(targetRepoId);
          if (typeof statusResp.progress_pct === 'number') {
            setAnalysisProgress(statusResp.progress_pct);
          }
          if (statusResp.stage) {
            setAnalysisStage(statusResp.stage);
          } else if (statusResp.current_step) {
            setAnalysisStage(statusResp.current_step);
          }
          if (statusResp.message) {
            setAnalysisMessage(statusResp.message);
          }

          if (statusResp.status === 'ready' || statusResp.progress_pct === 100) {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            setAnalysisProgress(100);
            setAnalysisStage('Ready');
            setAnalysisMessage(statusResp.message || 'Ready! Opening repository overview...');
            if (onRefreshRepositories) {
              await onRefreshRepositories();
            }
            setTimeout(() => {
              onSelectRepo(targetRepoId);
              onNavigateToTab('dashboard');
              setAnalyzingRepoUrl(null);
              setSelectedIssue(null);
            }, 1200);
          } else if (statusResp.status === 'failed') {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            setAnalysisStage('Failed');
            setAnalysisProgress(0);
            setAnalysisError(statusResp.error || statusResp.message || 'Repository analysis failed');
          }
        } catch {
          // ignore transient poll error
        }
      }, 1500);
    } catch (err: any) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      setAnalysisStage('Failed');
      setAnalysisProgress(0);
      setAnalysisError(err.message || 'Failed to trigger repository analysis');
    }
  };

  const getDifficultyBadge = (diff: string) => {
    switch (diff.toLowerCase()) {
      case 'easy':
        return 'bg-[#000000] text-zinc-200 border-[#1c1c21]';
      case 'medium':
        return 'bg-[#000000] text-zinc-300 border-[#1c1c21]';
      default:
        return 'bg-[#000000] text-zinc-400 border-[#1c1c21]';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-[#f4f4f5] select-none font-sans">
      {/* Seasonal Banner Slot */}
      {showBanner && (
        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-4 shadow-sm flex items-center justify-between animate-in fade-in duration-300">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-200">
              <Award className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase tracking-wider text-zinc-200 bg-zinc-900 px-2 py-0.5 rounded-md border border-zinc-800 font-mono">
                  Student Open-Source Challenge
                </span>
                <span className="text-[11px] text-[#71717a] font-mono">Active Season</span>
              </div>
              <p className="text-xs text-[#a1a1aa] mt-0.5">
                Pick a <strong className="text-white">Good First Issue</strong> below, click <strong className="text-white">Analyze</strong> to inspect likely files with AST search, and submit your PR!
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowBanner(false)}
            className="p-1.5 rounded-lg hover:bg-zinc-900 text-[#71717a] hover:text-white transition-colors"
            title="Dismiss banner"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Header & View Mode Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-md bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300 mb-1">
            <GitPullRequest className="w-3.5 h-3.5 text-zinc-300" />
            <span>Open-Source Contribution Hub</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Find Good First Issues & Start Contributing
          </h1>
          <p className="text-xs text-[#a1a1aa] mt-1 max-w-2xl leading-relaxed">
            Curated beginner-friendly issues enriched with Gemini summaries, required skills, and likely code files to inspect.
          </p>
        </div>

        {/* Tab switcher: All Issues vs My Contributions */}
        <div className="flex items-center bg-[#000000] border border-[#1c1c21] rounded-xl p-1 text-xs">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
              activeTab === 'all'
                ? 'bg-white text-black font-semibold shadow-sm'
                : 'text-[#a1a1aa] hover:text-white'
            }`}
          >
            Browse Issues ({issues.length})
          </button>
          <button
            onClick={() => setActiveTab('my_contributions')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer flex items-center space-x-1.5 ${
              activeTab === 'my_contributions'
                ? 'bg-white text-black font-semibold shadow-sm'
                : 'text-[#a1a1aa] hover:text-white'
            }`}
          >
            <Bookmark className="w-3.5 h-3.5" />
            <span>My Contributions</span>
            {(bookmarkedIds.size > 0 || workingIds.size > 0) && (
              <span className="w-1.5 h-1.5 rounded-full bg-white" />
            )}
          </button>
        </div>
      </div>

      {/* Filter and Search Bar (only for All Issues tab) */}
      {activeTab === 'all' && (
        <div className="bg-[#08080a] border border-[#18181b] rounded-2xl p-4 shadow-sm space-y-3">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#71717a] absolute left-3.5 top-3" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search issues by title, keywords, or labels..."
                className="w-full bg-[#000000] border border-[#1c1c21] rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-zinc-500 font-sans"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-white hover:bg-zinc-200 text-black rounded-xl text-xs font-semibold transition-all cursor-pointer shadow-sm"
            >
              Search Issues
            </button>
          </form>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-[#18181b] text-xs">
            {/* Languages */}
            <div className="flex items-center space-x-1.5 overflow-x-auto py-1">
              <span className="text-[11px] font-mono text-[#71717a] uppercase mr-1">Lang:</span>
              {languages.map((lang) => (
                <button
                  key={lang}
                  onClick={() => setSelectedLanguage(lang)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    selectedLanguage === lang
                      ? 'bg-white text-black font-semibold shadow-sm'
                      : 'bg-[#000000] text-[#a1a1aa] hover:text-white hover:bg-zinc-900 border border-[#1c1c21]'
                  }`}
                >
                  {lang}
                </button>
              ))}
            </div>

            {/* Domains & Difficulty */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1.5">
                <span className="font-mono text-[11px] text-[#71717a]">Domain:</span>
                <select
                  value={selectedDomain}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                  className="bg-[#000000] border border-[#1c1c21] text-white text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-zinc-500 cursor-pointer"
                >
                  {domains.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-1.5">
                <span className="font-mono text-[11px] text-[#71717a]">Difficulty:</span>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="bg-[#000000] border border-[#1c1c21] text-white text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-zinc-500 cursor-pointer"
                >
                  {difficulties.map((diff) => (
                    <option key={diff} value={diff}>
                      {diff}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {activeTab === 'my_contributions' ? (
        /* My Contributions View */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Working on this Section */}
            <div className="bg-[#0f0f15] border border-[#222232] rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1c1c28] pb-2.5">
                <div className="flex items-center space-x-2">
                  <Briefcase className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-semibold text-white">Issues I'm Working On</h3>
                </div>
                <span className="text-xs font-mono text-[#71717a]">
                  {userProfile?.working.length || 0} active
                </span>
              </div>

              {userProfile && userProfile.working.length > 0 ? (
                <div className="space-y-2.5">
                  {userProfile.working.map((item) => (
                    <div
                      key={item.issue_id}
                      className="p-3 bg-[#161622] border border-[#242436] rounded-xl flex items-center justify-between space-x-3"
                    >
                      <div className="min-w-0">
                        <span className="text-[10px] font-mono text-sky-400 block truncate">
                          {item.repo_name}
                        </span>
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-medium text-white hover:underline truncate block"
                        >
                          {item.title}
                        </a>
                      </div>
                      <button
                        onClick={() =>
                          handleAnalyze({
                            id: item.issue_id,
                            number: 0,
                            title: item.title,
                            html_url: item.url,
                            repository: item.repo_name,
                            repository_url: `https://github.com/${item.repo_name}`,
                            labels: [],
                            comments_count: 0,
                            created_at: '',
                            updated_at: '',
                            user: { login: '', avatar_url: '' },
                            difficulty: 'easy',
                            skills: [],
                            likely_files: [],
                            summary: '',
                          })
                        }
                        className="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-medium shrink-0 cursor-pointer"
                      >
                        Analyze
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-[#71717a]">
                  You have not marked any issues as "Working on this" yet. Click the briefcase icon on any issue to claim it!
                </div>
              )}
            </div>

            {/* Bookmarked Issues Section */}
            <div className="bg-[#0f0f15] border border-[#222232] rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1c1c28] pb-2.5">
                <div className="flex items-center space-x-2">
                  <Bookmark className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-semibold text-white">Bookmarked Issues</h3>
                </div>
                <span className="text-xs font-mono text-[#71717a]">
                  {userProfile?.bookmarks.length || 0} saved
                </span>
              </div>

              {userProfile && userProfile.bookmarks.length > 0 ? (
                <div className="space-y-2.5">
                  {userProfile.bookmarks.map((item) => (
                    <div
                      key={item.issue_id}
                      className="p-3 bg-[#161622] border border-[#242436] rounded-xl flex items-center justify-between space-x-3"
                    >
                      <div className="min-w-0">
                        <span className="text-[10px] font-mono text-sky-400 block truncate">
                          {item.repo_name}
                        </span>
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-medium text-white hover:underline truncate block"
                        >
                          {item.title}
                        </a>
                      </div>
                      <button
                        onClick={() =>
                          handleAnalyze({
                            id: item.issue_id,
                            number: 0,
                            title: item.title,
                            html_url: item.url,
                            repository: item.repo_name,
                            repository_url: `https://github.com/${item.repo_name}`,
                            labels: [],
                            comments_count: 0,
                            created_at: '',
                            updated_at: '',
                            user: { login: '', avatar_url: '' },
                            difficulty: 'easy',
                            skills: [],
                            likely_files: [],
                            summary: '',
                          })
                        }
                        className="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-medium shrink-0 cursor-pointer"
                      >
                        Analyze
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-[#71717a]">
                  No bookmarks yet. Star any issue to save it for later.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : loading && issues.length === 0 ? (
        /* Loading Skeleton */
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="bg-[#101016] border border-[#20202c] rounded-2xl p-4 space-y-2.5 animate-pulse"
            >
              <div className="h-4 bg-[#20202e] rounded w-1/3" />
              <div className="h-5 bg-[#252538] rounded w-3/4" />
              <div className="h-4 bg-[#181824] rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : error && issues.length === 0 ? (
        <div className="p-12 text-center bg-[#101016] border border-[#20202c] rounded-2xl space-y-3">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <h3 className="text-sm font-semibold text-white">Failed to Load Issues</h3>
          <p className="text-xs text-[#9ca3af] max-w-md mx-auto">{error}</p>
          <button
            onClick={() => loadIssues(true)}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold cursor-pointer"
          >
            Retry Fetching
          </button>
        </div>
      ) : issues.length === 0 ? (
        <div className="p-16 text-center bg-[#101016] border border-[#20202c] rounded-2xl space-y-3">
          <Compass className="w-10 h-10 text-[#71717a] mx-auto" />
          <h3 className="text-sm font-semibold text-white">No Matching Issues Found</h3>
          <p className="text-xs text-[#71717a] max-w-md mx-auto">
            Try broadening your language or difficulty filters to see more starter tickets.
          </p>
        </div>
      ) : (
        /* Issue Cards List */
        <div className="space-y-3">
          {issues.map((issue) => {
            const isBookmarked = bookmarkedIds.has(issue.id);
            const isWorking = workingIds.has(issue.id);

            return (
              <div
                key={issue.id}
                onClick={() => setSelectedIssue(issue)}
                className="bg-[#08080a] hover:bg-[#0c0c0e] border border-[#18181b] hover:border-[#27272a] rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all duration-200 cursor-pointer shadow-sm group"
              >
                {/* Left Meta & Title */}
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="font-mono text-zinc-200 font-semibold truncate max-w-xs">
                      {issue.repository}
                    </span>
                    <span className="text-zinc-600">•</span>
                    <span className="text-[11px] font-mono text-zinc-400">
                      #{issue.number}
                    </span>

                    {/* Difficulty Chip */}
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase font-bold border ${getDifficultyBadge(
                        issue.difficulty
                      )}`}
                    >
                      {issue.difficulty}
                    </span>

                    {/* Readiness Badge */}
                    {issue.readiness && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-[#000000] border border-[#1c1c21] text-zinc-300">
                        {issue.readiness.score}/100 readiness
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-semibold text-white group-hover:text-zinc-200 transition-colors leading-snug line-clamp-1">
                    {issue.title}
                  </h3>

                  {/* Skills Tags */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                    {issue.skills.map((skill, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2 py-0.5 rounded-md bg-[#000000] border border-[#1c1c21] text-[10px] font-mono text-zinc-400"
                      >
                        {skill}
                      </span>
                    ))}
                    {issue.labels.slice(0, 2).map((label, lIdx) => (
                      <span
                        key={lIdx}
                        className="px-2 py-0.5 rounded-md bg-[#000000] border border-[#1c1c21] text-[10px] font-mono text-zinc-300"
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Right Action Icons & Analyze Button */}
                <div className="flex items-center space-x-2 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-[#18181b]">
                  {/* Bookmark Button */}
                  <button
                    onClick={(e) => handleToggleBookmark(e, issue)}
                    className={`p-2 rounded-xl border transition-colors cursor-pointer ${
                      isBookmarked
                        ? 'bg-zinc-800 border-zinc-600 text-white'
                        : 'bg-[#000000] hover:bg-zinc-900 border-[#1c1c21] text-zinc-400 hover:text-white'
                    }`}
                    title={isBookmarked ? 'Remove bookmark' : 'Bookmark this issue'}
                  >
                    <Bookmark className="w-3.5 h-3.5 fill-current" />
                  </button>

                  {/* Working on this Button */}
                  <button
                    onClick={(e) => handleToggleWorking(e, issue)}
                    className={`flex items-center space-x-1 px-2.5 py-1.5 rounded-xl border text-xs font-medium transition-colors cursor-pointer ${
                      isWorking
                        ? 'bg-zinc-800 border-zinc-600 text-white'
                        : 'bg-[#000000] hover:bg-zinc-900 border-[#1c1c21] text-zinc-400 hover:text-white'
                    }`}
                    title={isWorking ? 'Stop working on this' : "Mark as I'm working on this"}
                  >
                    <Briefcase className="w-3.5 h-3.5" />
                    <span>{isWorking ? 'Working' : 'Claim'}</span>
                  </button>

                  {/* Analyze in CodeLens */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAnalyze(issue);
                    }}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-zinc-200 text-black text-xs font-semibold shadow-sm transition-all cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Analyze</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Load More Button */}
      {activeTab === 'all' && !loading && issues.length > 0 && hasMore && (
        <div className="text-center pt-4">
          <button
            onClick={handleLoadMore}
            className="px-6 py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-700/80 text-xs font-medium text-white transition-colors cursor-pointer shadow-sm"
          >
            Load More Issues
          </button>
        </div>
      )}

      {/* Issue Detail Drawer (Slide-out Right Drawer) */}
      {selectedIssue && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex justify-end animate-in fade-in duration-200">
          <div className="w-full max-w-xl bg-[#08080a] border-l border-[#18181b] h-full flex flex-col justify-between shadow-2xl p-6 overflow-y-auto animate-in slide-in-from-right duration-300 space-y-6">
            <div className="space-y-5">
              {/* Drawer Header */}
              <div className="flex items-start justify-between border-b border-[#18181b] pb-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono text-white font-bold">
                      {selectedIssue.repository}
                    </span>
                    <span className="text-[11px] text-zinc-400 font-mono">
                      #{selectedIssue.number}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase font-bold border ${getDifficultyBadge(
                        selectedIssue.difficulty
                      )}`}
                    >
                      {selectedIssue.difficulty}
                    </span>
                  </div>
                  <h2 className="text-base font-bold text-white leading-snug">
                    {selectedIssue.title}
                  </h2>
                </div>
                <button
                  onClick={() => setSelectedIssue(null)}
                  className="p-1.5 rounded-lg hover:bg-zinc-900 text-zinc-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Gemini AI Summary Box */}
              <div className="bg-[#000000] border border-[#18181b] rounded-2xl p-4 space-y-2">
                <div className="flex items-center space-x-1.5 text-zinc-200 text-xs font-semibold">
                  <Sparkles className="w-3.5 h-3.5 text-zinc-400" />
                  <span>AI Mentor Summary</span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed">
                  {selectedIssue.summary ||
                    'Analyze the issue description, identify key routines to patch, and add unit test coverage.'}
                </p>
              </div>

              {/* Likely Files to Inspect */}
              {selectedIssue.likely_files && selectedIssue.likely_files.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center space-x-1.5">
                    <FileCode className="w-3.5 h-3.5 text-zinc-300" />
                    <span>Likely Files to Inspect</span>
                  </h4>
                  <div className="space-y-1.5">
                    {selectedIssue.likely_files.map((file, fIdx) => (
                      <div
                        key={fIdx}
                        className="px-3 py-2 bg-[#000000] border border-[#18181b] rounded-xl text-xs font-mono text-zinc-200 truncate"
                      >
                        {file}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Required Skills & Concepts */}
              {selectedIssue.skills && selectedIssue.skills.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center space-x-1.5">
                    <Tag className="w-3.5 h-3.5 text-zinc-300" />
                    <span>Skills & Technologies</span>
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedIssue.skills.map((skill, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2.5 py-1 rounded-lg bg-[#000000] border border-[#18181b] text-xs font-mono text-zinc-300"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Repository Readiness Score */}
              {selectedIssue.readiness && (
                <div className="p-4 bg-[#000000] border border-[#18181b] rounded-2xl flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <ShieldCheck className="w-5 h-5 text-zinc-300" />
                    <div>
                      <h4 className="text-xs font-semibold text-white">
                        Repo Readiness: {selectedIssue.readiness.score}/100
                      </h4>
                      <p className="text-[10px] text-zinc-400">
                        Grade {selectedIssue.readiness.grade} • Active maintainers & beginner friendly
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* External GitHub Link */}
              <div className="pt-2">
                <a
                  href={selectedIssue.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 text-xs text-zinc-300 hover:text-white hover:underline"
                >
                  <span>Open original issue on GitHub</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            {/* Drawer Bottom Actions */}
            <div className="pt-4 border-t border-[#18181b] flex items-center space-x-3">
              <button
                onClick={() => handleAnalyze(selectedIssue)}
                className="flex-1 py-2.5 bg-white hover:bg-zinc-200 text-black rounded-xl text-xs font-semibold shadow-sm flex items-center justify-center space-x-2 cursor-pointer transition-all"
              >
                <Sparkles className="w-4 h-4" />
                <span>Analyze in CodeLens</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ingestion Progress Modal */}
      {analyzingRepoUrl && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#08080a] border border-[#18181b] rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-5 text-center animate-in zoom-in-95 duration-200">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mx-auto border ${
              analysisError
                ? 'bg-zinc-900 border-zinc-700 text-rose-400'
                : 'bg-zinc-900 border-zinc-700 text-white'
            }`}>
              {analysisError ? (
                <AlertCircle className="w-6 h-6" />
              ) : (
                <Loader2 className="w-6 h-6 animate-spin" />
              )}
            </div>

            <div>
              <h3 className="text-base font-bold text-white">
                Analyzing {analyzingRepoName}
              </h3>
              <p className="text-xs text-zinc-400 font-semibold mt-1">
                Stage: {analysisStage}
              </p>
            </div>

            <div className="space-y-1.5">
              <div className="h-2 bg-[#000000] rounded-full overflow-hidden border border-[#18181b]">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    analysisError
                      ? 'bg-rose-500'
                      : 'bg-white'
                  }`}
                  style={{ width: `${Math.max(0, Math.min(100, analysisProgress))}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] font-mono text-zinc-500">
                <span className="text-zinc-400 font-medium">{analysisStage}</span>
                <span className="text-white font-semibold">{analysisProgress}%</span>
              </div>
            </div>

            {/* Message or Explanatory Text */}
            <p className="text-xs text-zinc-400 leading-relaxed bg-[#000000] p-2.5 rounded-xl border border-[#18181b]">
              {analysisMessage}
            </p>

            {analysisError ? (
              <div className="space-y-3 pt-2">
                <div className="p-3 bg-zinc-900 border border-zinc-700 rounded-xl text-xs text-rose-400 text-left leading-relaxed">
                  {analysisError}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      if (pollIntervalRef.current) {
                        clearInterval(pollIntervalRef.current);
                        pollIntervalRef.current = null;
                      }
                      setAnalyzingRepoUrl(null);
                      setAnalysisError(null);
                    }}
                    className="flex-1 py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white rounded-xl text-xs font-semibold transition border border-zinc-700"
                  >
                    Dismiss
                  </button>
                  <button
                    onClick={() => {
                      if (analyzingIssue) {
                        handleAnalyze(analyzingIssue);
                      }
                    }}
                    className="flex-1 py-2 bg-white hover:bg-zinc-200 text-black rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition shadow-sm"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Retry Analysis</span>
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-[11px] text-zinc-500">
                Extracting AST symbols, computing vectors, and setting up workspace...
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
