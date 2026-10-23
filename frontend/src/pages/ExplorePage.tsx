import React, { useState, useEffect, useRef } from 'react';
import {
  Compass,
  Star,
  GitFork,
  ExternalLink,
  Search,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Info,
  X,
  Filter,
  Flame,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import type { ExploreRepoItem, ReadinessScore } from '../types';
import { fetchExploreRepos, analyzeRepository, fetchRepoStatus } from '../services/api';

interface ExplorePageProps {
  onSelectRepo: (repoId: string) => void;
  onNavigateToTab: (tab: string) => void;
  onRefreshRepositories?: () => Promise<void>;
}

export const ExplorePage: React.FC<ExplorePageProps> = ({
  onSelectRepo,
  onNavigateToTab,
  onRefreshRepositories,
}) => {
  const [repos, setRepos] = useState<ExploreRepoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('All');
  const [selectedTopic, setSelectedTopic] = useState('All');
  const [minStars, setMinStars] = useState(50);
  const [recentlyActive, setRecentlyActive] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Ingestion tracking
  const [analyzingRepoUrl, setAnalyzingRepoUrl] = useState<string | null>(null);
  const [analyzingRepoName, setAnalyzingRepoName] = useState<string>('');
  const [analyzingItem, setAnalyzingItem] = useState<ExploreRepoItem | null>(null);
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

  // Readiness details modal
  const [activeReadinessRepo, setActiveReadinessRepo] = useState<ExploreRepoItem | null>(null);

  const languages = ['All', 'Python', 'TypeScript', 'JavaScript', 'Go', 'Rust', 'C++', 'Java'];
  const topics = ['All', 'AI/ML', 'Web', 'DevOps', 'Systems', 'Mobile'];

  const loadRepos = async (isNewSearch: boolean = false) => {
    try {
      if (isNewSearch) {
        setLoading(true);
        setPage(1);
      }
      setError(null);
      const currentPage = isNewSearch ? 1 : page;
      const resp = await fetchExploreRepos({
        language: selectedLanguage !== 'All' ? selectedLanguage : undefined,
        topic: selectedTopic !== 'All' ? selectedTopic : undefined,
        min_stars: minStars,
        recently_active: recentlyActive,
        q: searchQuery.trim() || undefined,
        page: currentPage,
        per_page: 15,
      });

      if (isNewSearch) {
        setRepos(resp.repos);
      } else {
        setRepos((prev) => [...prev, ...resp.repos]);
      }
      setHasMore(resp.repos.length >= 15);
    } catch (err: any) {
      console.error('Failed to load explore repos:', err);
      setError(err.message || 'Failed to load repositories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRepos(true);
  }, [selectedLanguage, selectedTopic, minStars, recentlyActive]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadRepos(true);
  };

  const handleLoadMore = () => {
    setPage((prev) => prev + 1);
  };

  useEffect(() => {
    if (page > 1) {
      loadRepos(false);
    }
  }, [page]);

  const handleAnalyze = async (repo: ExploreRepoItem) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    try {
      setAnalyzingItem(repo);
      setAnalyzingRepoUrl(repo.html_url);
      setAnalyzingRepoName(repo.name);
      setAnalysisProgress(5);
      setAnalysisStage('Queued');
      setAnalysisMessage('Job queued for analysis...');
      setAnalysisError(null);

      const jobResp = await analyzeRepository(repo.html_url);
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
            setAnalysisMessage(statusResp.message || 'Indexing complete! Opening repository...');
            if (onRefreshRepositories) {
              await onRefreshRepositories();
            }
            setTimeout(() => {
              onSelectRepo(targetRepoId);
              onNavigateToTab('dashboard');
              setAnalyzingRepoUrl(null);
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

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A+':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'A':
        return 'bg-teal-500/20 text-teal-300 border-teal-500/40';
      case 'B':
        return 'bg-sky-500/20 text-sky-300 border-sky-500/40';
      case 'C':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      default:
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-[#f4f4f5] select-none font-sans">
      {/* Hero Header */}
      <div className="bg-gradient-to-r from-[#121218] via-[#161622] to-[#121218] border border-[#222230] rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-sky-950/60 border border-sky-800/50 text-[11px] font-mono text-sky-300">
              <Compass className="w-3.5 h-3.5 text-sky-400" />
              <span>Explore Top Repositories</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Discover Open-Source Codebases
            </h1>
            <p className="text-xs text-[#9ca3af] max-w-2xl leading-relaxed">
              Explore leading repositories with calculated <strong className="text-sky-300">Contribution-Readiness Scores</strong>. Click <strong>Analyze in CodeLens</strong> on any project to clone, extract AST chunks, and index it locally with AST search and reasoning.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={() => loadRepos(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#1d1d28] hover:bg-[#272738] border border-[#2e2e42] text-xs text-[#ececec] transition-colors cursor-pointer"
              title="Refresh feed"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-[#0e0e14] border border-[#20202c] rounded-2xl p-4 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-2.5">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#71717a] absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search repositories by name, keywords, or topics..."
              className="w-full bg-[#161620] border border-[#29293a] rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-sky-500 font-sans"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold transition-all cursor-pointer shadow-md"
          >
            Search Repos
          </button>
        </form>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-[#1a1a24] text-xs">
          {/* Languages */}
          <div className="flex items-center space-x-1.5 overflow-x-auto py-1">
            <span className="text-[11px] font-mono text-[#71717a] uppercase mr-1">Lang:</span>
            {languages.map((lang) => (
              <button
                key={lang}
                onClick={() => setSelectedLanguage(lang)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  selectedLanguage === lang
                    ? 'bg-sky-500 text-white shadow-sm'
                    : 'bg-[#181822] text-[#9ca3af] hover:text-white hover:bg-[#20202e]'
                }`}
              >
                {lang}
              </button>
            ))}
          </div>

          {/* Right: Stars & Active Toggle */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 text-xs text-[#9ca3af]">
              <span className="font-mono text-[11px]">Min Stars:</span>
              <select
                value={minStars}
                onChange={(e) => setMinStars(Number(e.target.value))}
                className="bg-[#181822] border border-[#2b2b3d] text-white text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-sky-500 cursor-pointer"
              >
                <option value={50}>50+ stars</option>
                <option value={500}>500+ stars</option>
                <option value={2000}>2,000+ stars</option>
                <option value={10000}>10,000+ stars</option>
              </select>
            </div>

            <button
              onClick={() => setRecentlyActive(!recentlyActive)}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                recentlyActive
                  ? 'bg-amber-950/40 text-amber-300 border-amber-600/40'
                  : 'bg-[#181822] text-[#71717a] border-[#29293a]'
              }`}
            >
              <Flame className={`w-3.5 h-3.5 ${recentlyActive ? 'text-amber-400' : 'text-[#71717a]'}`} />
              <span>Trending (Active)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid View */}
      {loading && repos.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-[#101016] border border-[#20202c] rounded-2xl p-5 space-y-4 animate-pulse"
            >
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-[#20202e]" />
                <div className="space-y-1.5 flex-1">
                  <div className="h-4 bg-[#20202e] rounded w-2/3" />
                  <div className="h-3 bg-[#181824] rounded w-1/3" />
                </div>
              </div>
              <div className="h-12 bg-[#181824] rounded-lg" />
              <div className="h-8 bg-[#20202e] rounded-xl" />
            </div>
          ))}
        </div>
      ) : error && repos.length === 0 ? (
        <div className="p-12 text-center bg-[#101016] border border-[#20202c] rounded-2xl space-y-3">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <h3 className="text-sm font-semibold text-white">Failed to Load Repositories</h3>
          <p className="text-xs text-[#9ca3af] max-w-md mx-auto">{error}</p>
          <button
            onClick={() => loadRepos(true)}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold cursor-pointer"
          >
            Retry Fetching
          </button>
        </div>
      ) : repos.length === 0 ? (
        <div className="p-16 text-center bg-[#101016] border border-[#20202c] rounded-2xl space-y-3">
          <Compass className="w-10 h-10 text-[#71717a] mx-auto" />
          <h3 className="text-sm font-semibold text-white">No Repositories Found</h3>
          <p className="text-xs text-[#71717a] max-w-md mx-auto">
            Try adjusting your search query, language filter, or minimum star threshold.
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedLanguage('All');
              setSelectedTopic('All');
              setMinStars(50);
            }}
            className="px-4 py-1.5 bg-[#20202e] hover:bg-[#28283a] text-white text-xs rounded-xl cursor-pointer"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {repos.map((repo) => {
            const readiness = repo.readiness;
            return (
              <div
                key={repo.id}
                className="bg-[#0f0f15] hover:bg-[#13131c] border border-[#20202e] hover:border-[#323248] rounded-2xl p-5 flex flex-col justify-between transition-all duration-200 shadow-md group relative"
              >
                <div>
                  {/* Top Header: Avatar + Repo Name + External Link */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2.5 min-w-0">
                      <img
                        src={repo.owner.avatar_url || 'https://github.com/github.png'}
                        alt={repo.owner.login}
                        className="w-8 h-8 rounded-lg border border-[#28283a] object-cover shrink-0"
                      />
                      <div className="min-w-0">
                        <h3 className="text-sm font-semibold text-white truncate group-hover:text-sky-400 transition-colors">
                          {repo.name}
                        </h3>
                        <p className="text-[11px] text-[#71717a] truncate font-mono">
                          {repo.full_name}
                        </p>
                      </div>
                    </div>

                    <a
                      href={repo.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 rounded-lg hover:bg-[#242436] text-[#71717a] hover:text-white transition-colors"
                      title="View on GitHub"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-[#a1a1aa] line-clamp-2 leading-relaxed mb-4 min-h-[36px]">
                    {repo.description}
                  </p>

                  {/* Readiness Score Badge */}
                  {readiness && (
                    <div className="mb-4">
                      <button
                        type="button"
                        onClick={() => setActiveReadinessRepo(repo)}
                        className={`w-full flex items-center justify-between px-3 py-1.5 rounded-xl border text-xs cursor-pointer transition-all hover:scale-[1.01] ${getGradeColor(
                          readiness.grade
                        )}`}
                        title="Click to view full 6-factor readiness breakdown"
                      >
                        <div className="flex items-center space-x-1.5">
                          <ShieldCheck className="w-4 h-4" />
                          <span className="font-semibold">{readiness.score}/100 Readiness</span>
                        </div>
                        <span className="font-mono text-[11px] uppercase font-bold tracking-wider">
                          Grade {readiness.grade} →
                        </span>
                      </button>
                    </div>
                  )}

                  {/* Meta Stats: Stars, Forks, Language */}
                  <div className="flex flex-wrap items-center gap-3 text-xs text-[#8e8e99] mb-4">
                    <span className="flex items-center space-x-1">
                      <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                      <span className="font-mono">{repo.stars.toLocaleString()}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <GitFork className="w-3.5 h-3.5 text-[#71717a]" />
                      <span className="font-mono">{repo.forks.toLocaleString()}</span>
                    </span>
                    {repo.language && (
                      <span className="px-2 py-0.5 rounded-md bg-[#1a1a24] text-[11px] font-mono text-[#c4c4d4]">
                        {repo.language}
                      </span>
                    )}
                  </div>
                </div>

                {/* Bottom CTA: Analyze in CodeLens */}
                <div className="pt-3 border-t border-[#1c1c28]">
                  <button
                    onClick={() => handleAnalyze(repo)}
                    className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md transition-all cursor-pointer group-hover:shadow-sky-500/20"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Analyze in CodeLens</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Load More Button */}
      {!loading && repos.length > 0 && hasMore && (
        <div className="text-center pt-4">
          <button
            onClick={handleLoadMore}
            className="px-6 py-2.5 rounded-xl bg-[#161622] hover:bg-[#202030] border border-[#2b2b3d] text-xs font-medium text-white transition-colors cursor-pointer shadow-sm"
          >
            Load More Repositories
          </button>
        </div>
      )}

      {/* Readiness Score Breakdown Modal */}
      {activeReadinessRepo && activeReadinessRepo.readiness && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-[#121218] border border-[#2e2e42] rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-[#242436] pb-3">
              <div className="flex items-center space-x-2.5">
                <ShieldCheck className="w-5 h-5 text-sky-400" />
                <div>
                  <h3 className="text-base font-bold text-white">
                    {activeReadinessRepo.name} Readiness
                  </h3>
                  <p className="text-[11px] text-[#71717a] font-mono">
                    6-Factor Contribution Readiness Score
                  </p>
                </div>
              </div>
              <button
                onClick={() => setActiveReadinessRepo(null)}
                className="p-1.5 rounded-lg hover:bg-[#202030] text-[#71717a] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Score Callout */}
            <div className="flex items-center justify-between p-4 rounded-2xl bg-[#181824] border border-[#2a2a3e]">
              <div>
                <span className="text-3xl font-extrabold text-white">
                  {activeReadinessRepo.readiness.score}
                </span>
                <span className="text-xs text-[#71717a] ml-1">/ 100</span>
                <p className="text-xs text-[#9ca3af] mt-0.5">
                  Overall Score: Grade {activeReadinessRepo.readiness.grade}
                </p>
              </div>
              <div
                className={`px-3 py-1 rounded-xl text-xs font-bold font-mono uppercase ${getGradeColor(
                  activeReadinessRepo.readiness.grade
                )}`}
              >
                Grade {activeReadinessRepo.readiness.grade}
              </div>
            </div>

            {/* Factor Bars */}
            <div className="space-y-3">
              <h4 className="text-[11px] font-semibold uppercase tracking-wider text-[#71717a]">
                Factor Breakdown
              </h4>
              {[
                {
                  label: 'Recent Commit Activity (30d)',
                  score: activeReadinessRepo.readiness.breakdown.recent_commit_activity,
                  max: 20,
                  desc: `${activeReadinessRepo.readiness.details.commits_last_30_days} commits in last month`,
                },
                {
                  label: 'Median PR Merge Time',
                  score: activeReadinessRepo.readiness.breakdown.pr_merge_time,
                  max: 20,
                  desc: `~${activeReadinessRepo.readiness.details.median_pr_merge_days} days median turnaround`,
                },
                {
                  label: 'Maintainer Issue Response Time',
                  score: activeReadinessRepo.readiness.breakdown.maintainer_response_time,
                  max: 20,
                  desc: `~${activeReadinessRepo.readiness.details.maintainer_response_hours} hours on beginner tickets`,
                },
                {
                  label: 'CONTRIBUTING.md Guidelines',
                  score: activeReadinessRepo.readiness.breakdown.contributing_guidelines,
                  max: 15,
                  desc: activeReadinessRepo.readiness.details.has_contributing_md
                    ? 'Verified contributing guide found'
                    : 'No clear contribution guide detected',
                },
                {
                  label: 'Beginner / Good First Issues',
                  score: activeReadinessRepo.readiness.breakdown.beginner_issue_ratio,
                  max: 15,
                  desc: `${activeReadinessRepo.readiness.details.good_first_issue_count} labeled starter issues`,
                },
                {
                  label: 'Open PR Backlog Health',
                  score: activeReadinessRepo.readiness.breakdown.open_pr_backlog,
                  max: 10,
                  desc: `${activeReadinessRepo.readiness.details.open_pr_count} open pull requests in queue`,
                },
              ].map((f, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#ececec] font-medium">{f.label}</span>
                    <span className="font-mono text-sky-400">
                      {f.score} / {f.max} pts
                    </span>
                  </div>
                  <div className="h-1.5 bg-[#1f1f2e] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-sky-500 to-emerald-500 rounded-full"
                      style={{ width: `${(f.score / f.max) * 100}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-[#71717a] font-mono">{f.desc}</p>
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => {
                  const r = activeReadinessRepo;
                  setActiveReadinessRepo(null);
                  handleAnalyze(r);
                }}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold cursor-pointer shadow-md"
              >
                Analyze this Repo in CodeLens
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ingestion Progress Modal */}
      {analyzingRepoUrl && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#121218] border border-[#2e2e42] rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-5 text-center animate-in zoom-in-95 duration-200">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mx-auto border ${
              analysisError
                ? 'bg-rose-500/20 border-rose-500/40 text-rose-400'
                : 'bg-sky-500/20 border-sky-500/40 text-sky-400'
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
              <p className="text-xs text-sky-400 font-semibold mt-1">
                Stage: {analysisStage}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1.5">
              <div className="h-2.5 bg-[#1b1b26] rounded-full overflow-hidden border border-[#2b2b3d]">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    analysisError
                      ? 'bg-rose-500'
                      : 'bg-gradient-to-r from-sky-500 to-emerald-400'
                  }`}
                  style={{ width: `${Math.max(0, Math.min(100, analysisProgress))}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] font-mono text-[#71717a]">
                <span className="text-[#a1a1aa] font-medium">{analysisStage}</span>
                <span className="text-sky-400 font-semibold">{analysisProgress}%</span>
              </div>
            </div>

            {/* Message or Explanatory Text */}
            <p className="text-xs text-[#9ca3af] leading-relaxed bg-[#181822] p-2.5 rounded-xl border border-[#262638]">
              {analysisMessage}
            </p>

            {analysisError ? (
              <div className="space-y-3 pt-2">
                <div className="p-3 bg-rose-950/40 border border-rose-800/50 rounded-xl text-xs text-rose-300 text-left leading-relaxed">
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
                    className="flex-1 py-2 bg-[#1f1f2e] hover:bg-[#2a2a3e] text-[#a1a1aa] hover:text-white rounded-xl text-xs font-semibold transition"
                  >
                    Dismiss
                  </button>
                  <button
                    onClick={() => {
                      if (analyzingItem) {
                        handleAnalyze(analyzingItem);
                      }
                    }}
                    className="flex-1 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition shadow-lg shadow-sky-600/30"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Retry Analysis</span>
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-[11px] text-[#71717a]">
                Cloning AST nodes, generating local embeddings, and configuring search indexes...
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
