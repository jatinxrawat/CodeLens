import type {
  RepositorySummary,
  RepositoryStatus,
  RepositoryStats,
  SearchResponse,
  SearchMode,
  FileItem,
  FileContent,
  GraphResponse,
  EvaluationResponse,
  AskResponse,
  FunctionFlowResult,
  ImpactAnalysisResult,
  ArchitectureReport,
  RepositoryQualityMetrics,
  CodeSmellReport,
  SecurityScanReport,
  RepoComparisonResult,
  IncrementalUpdateSummary,
} from '../types';

const API_BASE = '/api';

export async function fetchRepositories(): Promise<RepositorySummary[]> {
  const res = await fetch(`${API_BASE}/repositories`);
  if (!res.ok) throw new Error('Failed to fetch repositories');
  return res.json();
}

export async function fetchRepositoryStatus(repoId: string): Promise<RepositoryStatus> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/status`);
  if (!res.ok) throw new Error('Failed to fetch repository status');
  return res.json();
}

export async function fetchRepositoryStats(repoId: string): Promise<RepositoryStats> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/stats`);
  if (!res.ok) throw new Error('Failed to fetch repository statistics');
  return res.json();
}

export async function ingestRemoteRepository(gitUrl: string, force: boolean = false): Promise<{ job_id: string; repository_name: string }> {
  const res = await fetch(`${API_BASE}/repositories/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ git_url: gitUrl, force }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to start ingestion');
  }
  return res.json();
}

export async function ingestLocalRepository(repoPath: string): Promise<{ job_id: string; repository_name: string }> {
  const res = await fetch(`${API_BASE}/repositories/ingest-local`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_path: repoPath }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to start local ingestion');
  }
  return res.json();
}

export async function executeSearch(
  repoId: string,
  query: string,
  topK: number = 5,
  mode: SearchMode = 'hybrid',
  alpha: number = 0.6
): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_id: repoId,
      query,
      top_k: topK,
      mode,
      alpha,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Search query failed');
  }
  return res.json();
}

export async function fetchRepositoryFiles(repoId: string): Promise<FileItem[]> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/files`);
  if (!res.ok) throw new Error('Failed to fetch repository files');
  return res.json();
}

export async function fetchFileContent(repoId: string, filePath: string): Promise<FileContent> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/file-content?path=${encodeURIComponent(filePath)}`);
  if (!res.ok) throw new Error('Failed to fetch file content');
  return res.json();
}

export async function fetchDependencyGraph(repoId: string): Promise<GraphResponse> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/graph`);
  if (!res.ok) throw new Error('Failed to fetch dependency graph');
  return res.json();
}

export async function runEvaluationBenchmark(repoId: string, topK: number = 5): Promise<EvaluationResponse> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ top_k: topK }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Evaluation benchmark failed');
  }
  return res.json();
}

/* --- Phase 4 API Methods --- */

export async function askCodebase(
  repoId: string,
  query: string,
  topK: number = 5,
  alpha: number = 0.6
): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/reasoning/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_id: repoId,
      query,
      top_k: topK,
      alpha,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to process question');
  }
  return res.json();
}

export async function fetchArchitectureAnalysis(repoId: string): Promise<ArchitectureReport> {
  const res = await fetch(`${API_BASE}/analysis/${encodeURIComponent(repoId)}/architecture`);
  if (!res.ok) throw new Error('Failed to load architecture analysis');
  return res.json();
}

export async function fetchFunctionFlow(repoId: string, symbol: string, filePath?: string): Promise<FunctionFlowResult> {
  let url = `${API_BASE}/analysis/${encodeURIComponent(repoId)}/flow?symbol=${encodeURIComponent(symbol)}`;
  if (filePath) url += `&file_path=${encodeURIComponent(filePath)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to trace function flow');
  return res.json();
}

export async function fetchImpactAnalysis(repoId: string, target: string): Promise<ImpactAnalysisResult> {
  const res = await fetch(`${API_BASE}/analysis/${encodeURIComponent(repoId)}/impact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target }),
  });
  if (!res.ok) throw new Error('Failed to compute impact analysis');
  return res.json();
}

export async function fetchQualityMetrics(repoId: string): Promise<RepositoryQualityMetrics> {
  const res = await fetch(`${API_BASE}/analysis/${encodeURIComponent(repoId)}/quality`);
  if (!res.ok) throw new Error('Failed to load quality metrics');
  return res.json();
}

export async function fetchCodeSmells(repoId: string): Promise<CodeSmellReport> {
  const res = await fetch(`${API_BASE}/analysis/${encodeURIComponent(repoId)}/smells`);
  if (!res.ok) throw new Error('Failed to load code smells');
  return res.json();
}

export async function fetchSecurityScan(repoId: string): Promise<SecurityScanReport> {
  const res = await fetch(`${API_BASE}/analysis/${encodeURIComponent(repoId)}/security`);
  if (!res.ok) throw new Error('Failed to load security scan');
  return res.json();
}

export async function fetchReportData(repoId: string): Promise<Record<string, any>> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/report`);
  if (!res.ok) throw new Error('Failed to load repository report');
  return res.json();
}

export async function fetchReportMarkdown(repoId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/report/markdown`);
  if (!res.ok) throw new Error('Failed to load markdown report');
  return res.text();
}

export async function compareRepositories(repoA: string, repoB: string): Promise<RepoComparisonResult> {
  const res = await fetch(`${API_BASE}/repositories/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_a: repoA, repo_b: repoB }),
  });
  if (!res.ok) throw new Error('Failed to compare repositories');
  return res.json();
}

export async function triggerIncrementalUpdate(repoId: string): Promise<IncrementalUpdateSummary> {
  const res = await fetch(`${API_BASE}/repositories/${encodeURIComponent(repoId)}/incremental-update`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to trigger incremental update');
  return res.json();
}

/* --- Phase 5 ML Studio API --- */

export async function fetchMLDatasetStats(): Promise<import('../types').MLDatasetStatsResponse> {
  const res = await fetch(`${API_BASE}/ml/dataset/stats`);
  if (!res.ok) throw new Error('Failed to load ML dataset statistics');
  return res.json();
}

export async function trainMLRanker(params: { n_estimators: number; learning_rate: number; max_depth: number }): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/ranker/train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to train ranker model');
  return res.json();
}

export async function fetchMLRankerBaselines(): Promise<import('../types').MLBaselineComparison[]> {
  const res = await fetch(`${API_BASE}/ml/ranker/baselines`);
  if (!res.ok) throw new Error('Failed to load ranker baseline comparisons');
  return res.json();
}

export async function fetchMLRankerAblation(): Promise<import('../types').MLAblationResult[]> {
  const res = await fetch(`${API_BASE}/ml/ranker/ablation`);
  if (!res.ok) throw new Error('Failed to load feature ablation results');
  return res.json();
}

export async function trainMLMaintainability(params: { n_estimators: number; learning_rate: number; max_depth: number }): Promise<any> {
  const res = await fetch(`${API_BASE}/ml/maintainability/train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to train maintainability model');
  return res.json();
}

export async function fetchMLMaintainabilityMetrics(): Promise<import('../types').MaintainabilityMetricsResponse> {
  const res = await fetch(`${API_BASE}/ml/maintainability/metrics`);
  if (!res.ok) throw new Error('Failed to load maintainability metrics');
  return res.json();
}

export async function fetchMLExperiments(): Promise<import('../types').MLExperimentRecord[]> {
  const res = await fetch(`${API_BASE}/ml/experiments`);
  if (!res.ok) throw new Error('Failed to load ML experiments history');
  return res.json();
}

export async function fetchMLFailures(): Promise<import('../types').MLFailureAnalysisResponse> {
  const res = await fetch(`${API_BASE}/ml/failures`);
  if (!res.ok) throw new Error('Failed to load ML failure analysis');
  return res.json();
}

