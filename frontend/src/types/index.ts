export type SearchMode = 'hybrid' | 'vector' | 'keyword';

export interface RepositorySummary {
  repository_id: string;
  repository_name: string;
  source: string;
  indexed_at: string;
  total_files: number;
  total_chunks: number;
  languages: Record<string, number>;
}

export interface RepositoryStatus {
  repository_id: string;
  repository_name: string;
  source: string;
  status: 'ready' | 'ingesting' | 'failed' | 'not_found';
  current_step?: string;
  progress_pct?: number;
  total_files: number;
  total_chunks: number;
  languages: Record<string, number>;
  ingestion_duration_sec: number;
  error?: string;
}

export interface SearchResultItem {
  file_path: string;
  symbol?: string;
  language: string;
  chunk_type: string;
  start_line: number;
  end_line: number;
  similarity: number;
  code: string;
  docstring?: string;
  context_prefix?: string;
  rank: number;
}

export interface SearchResponse {
  query: string;
  repository_id: string;
  mode: SearchMode;
  alpha: number;
  latency_ms: number;
  total_results: number;
  results: SearchResultItem[];
}

export interface RepositoryStats {
  repository_id: string;
  repository_name: string;
  source: string;
  indexed_at: string;
  total_files: number;
  total_chunks: number;
  total_lines_of_code: number;
  languages: Record<string, number>;
  chunk_types: Record<string, number>;
  embedding_model: string;
  embedding_dimension: number;
  ingestion_time_sec: number;
  parsing_time_sec: number;
  embedding_time_sec: number;
  indexing_time_sec: number;
  total_pipeline_time_sec: number;
  avg_search_latency_ms?: number;
  p95_search_latency_ms?: number;
}

export interface FileItem {
  path: string;
  name: string;
  language: string;
  symbols: Array<{
    symbol: string;
    type: string;
    start_line: number;
    end_line: number;
  }>;
  total_chunks: number;
  min_line: number;
  max_line: number;
}

export interface FileContent {
  file_path: string;
  code: string;
  total_lines: number;
  language: string;
  size_bytes?: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'file' | 'external_package' | 'module';
  language?: string;
  path: string;
  size_bytes?: number;
  in_degree: number;
  out_degree: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship_type: 'import_relationship' | 'external_import' | 'containment' | 'inferred_relationship';
  is_static: boolean;
  raw_import?: string;
}

export interface GraphResponse {
  repository_id: string;
  total_nodes: number;
  total_edges: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ModelComparisonResult {
  mode: string;
  alpha: number;
  recall_at_1: number;
  recall_at_3: number;
  recall_at_5: number;
  mean_reciprocal_rank: number;
  avg_latency_ms: number;
}

export interface EvaluationResponse {
  repository_id: string;
  total_queries: number;
  comparisons: ModelComparisonResult[];
  query_breakdown: Array<{
    query: string;
    expected_file: string;
    expected_symbol?: string;
    found_rank?: number;
    latency_ms: number;
    top_result: string;
  }>;
}

/* --- Phase 4 Types --- */

export interface CitationSource {
  file_path: string;
  symbol_name?: string;
  chunk_type: string;
  start_line: number;
  end_line: number;
  similarity: number;
  code_preview: string;
  rank: number;
}

export interface DecisionFactor {
  label: string;
  factor_type: string;
  description: string;
}

export interface AskResponse {
  query: string;
  repository_id: string;
  category: string;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';
  confidence_score: number;
  answer: string;
  sources: CitationSource[];
  reasoning_evidence: DecisionFactor[];
  latency_ms: number;
  is_sufficient_evidence: boolean;
}

export interface FlowStep {
  caller_symbol: string;
  callee_symbol: string;
  caller_file: string;
  callee_file?: string;
  caller_line: number;
  relationship_type: 'confirmed_static' | 'inferred';
  explanation: string;
}

export interface FunctionFlowResult {
  target_symbol: string;
  target_file: string;
  target_line: number;
  callers: Array<{
    symbol: string;
    file_path: string;
    start_line: number;
    end_line?: number;
    relationship: string;
  }>;
  callees: Array<{
    symbol: string;
    file_path?: string;
    start_line: number;
    relationship: string;
    is_internal: boolean;
  }>;
  imported_modules: string[];
  flow_steps: FlowStep[];
  disclaimer: string;
}

export interface ImpactItem {
  file_path: string;
  impact_level: 'HIGH' | 'MEDIUM' | 'LOW';
  relationship_type: string;
  confidence_score: number;
  reason: string;
  affected_symbols: string[];
}

export interface ImpactAnalysisResult {
  target: string;
  target_type: 'file' | 'symbol';
  total_affected_files: number;
  high_impact_count: number;
  medium_impact_count: number;
  low_impact_count: number;
  impacted_files: ImpactItem[];
  disclaimer: string;
}

export interface ArchitectureLayer {
  name: string;
  inferred_type: string;
  files: string[];
  file_count: number;
  symbol_count: number;
  primary_languages: string[];
  description: string;
  confidence: number;
}

export interface SubsystemModule {
  module_name: string;
  layer_name: string;
  files: string[];
  dependencies: string[];
  in_degree: number;
  out_degree: number;
}

export interface ArchitectureReport {
  repository_id: string;
  inferred_pattern: string;
  status: string;
  layers: ArchitectureLayer[];
  modules: SubsystemModule[];
  directional_flow: string[];
  disclaimer: string;
}

export interface FunctionComplexity {
  symbol: string;
  file_path: string;
  start_line: number;
  end_line: number;
  lines_of_code: number;
  cyclomatic_complexity: number;
  nesting_depth: number;
  parameter_count: number;
  rating: 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH';
}

export interface RepositoryQualityMetrics {
  repository_id: string;
  total_lines_of_code: number;
  total_functions: number;
  total_classes: number;
  avg_cyclomatic_complexity: number;
  max_cyclomatic_complexity: number;
  avg_function_length: number;
  complexity_distribution: Record<string, number>;
  top_complex_functions: FunctionComplexity[];
  overall_maintainability: 'HIGH' | 'MEDIUM' | 'LOW';
  coupling_level: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface CodeSmellFinding {
  id: string;
  file_path: string;
  symbol_name?: string;
  start_line: number;
  end_line: number;
  rule_name: string;
  issue_title: string;
  metric_value: string;
  threshold: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  recommendation: string;
}

export interface CodeSmellReport {
  repository_id: string;
  total_findings: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  findings: CodeSmellFinding[];
}

export interface SecurityFinding {
  id: string;
  file_path: string;
  symbol_name?: string;
  start_line: number;
  rule_id: string;
  rule_name: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: number;
  matched_snippet: string;
  explanation: string;
  recommendation: string;
}

export interface SecurityScanReport {
  repository_id: string;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  findings: SecurityFinding[];
  disclaimer: string;
}

export interface RepoComparisonResult {
  repo_a_id: string;
  repo_b_id: string;
  repo_a: Record<string, any>;
  repo_b: Record<string, any>;
}

export interface IncrementalUpdateSummary {
  repository_id: string;
  added_files: string[];
  modified_files: string[];
  deleted_files: string[];
  total_reindexed_chunks: number;
  duration_sec: number;
  status: string;
}

/* --- Phase 5 ML Studio Types --- */

export interface MLBaselineComparison {
  method: string;
  total_queries: number;
  recall_at_1: number;
  recall_at_3: number;
  recall_at_5: number;
  recall_at_10: number;
  mrr: number;
  ndcg_at_5: number;
  ndcg_at_10: number;
  avg_latency_ms: number;
}

export interface MLAblationResult {
  feature_group: string;
  features_used: string[];
  feature_count: number;
  recall_at_1: number;
  recall_at_3: number;
  recall_at_5: number;
  mrr: number;
  ndcg_at_5: number;
  avg_latency_ms: number;
}

export interface MaintainabilityMetricsResponse {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  confusion_matrix: number[][];
  class_metrics: Record<string, { precision: number; recall: number; f1_score: number; support: number }>;
  total_test_samples: number;
  feature_importances: Record<string, number>;
}

export interface MLExperimentRecord {
  experiment_id: string;
  timestamp: string;
  model_name: string;
  model_version: string;
  hyperparameters: Record<string, any>;
  dataset_info: Record<string, any>;
  metrics: Record<string, any>;
  git_commit: string;
  notes: string;
}

export interface MLFailureAnalysisResponse {
  ranking_failures: Array<{
    query: string;
    repository_id: string;
    language: string;
    expected_file: string;
    expected_symbol?: string;
    achieved_rank: number | string;
    top_retrieved_file: string;
    top_retrieved_symbol?: string;
    diagnostic_reason: string;
  }>;
  maintainability_failures: Array<{
    chunk_id: string;
    repository_id: string;
    file_path: string;
    symbol_name?: string;
    language: string;
    actual_label: string;
    predicted_label: string;
    cyclomatic_complexity: number;
    loc: number;
    nesting_depth: number;
    diagnostic_reason: string;
  }>;
}

export interface MLDatasetStatsResponse {
  ranking_dataset: Record<string, any>;
  maintainability_dataset: Record<string, any>;
  repositories: {
    train: string[];
    validation: string[];
    test: string[];
  };
}

