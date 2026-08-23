import React, { useState, useEffect } from 'react';
import { Gauge, Clock, Cpu, Database, Activity, HardDrive, CheckCircle2 } from 'lucide-react';
import { RepositoryStats } from '../types';
import { fetchRepositoryStats } from '../services/api';

interface PerformancePageProps {
  selectedRepo: string;
}

export const PerformancePage: React.FC<PerformancePageProps> = ({ selectedRepo }) => {
  const [stats, setStats] = useState<RepositoryStats | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoading(true);
    fetchRepositoryStats(selectedRepo)
      .then(setStats)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedRepo]);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[#e6edf3]">Pipeline Telemetry & Benchmarks</h1>
        <p className="text-xs text-[#8b949e] mt-0.5">
          Real latency metrics, stage-by-stage pipeline timings, and FAISS indexing telemetry.
        </p>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Pipeline Stage Latencies */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 text-sm font-semibold text-[#e6edf3]">
              <Clock className="w-4 h-4 text-emerald-400" />
              <span>Ingestion Stage Timing Breakdown</span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center p-2 rounded bg-[#0d1117] border border-[#30363d]">
                <span className="text-[#8b949e]">Repository Fetch & Clone:</span>
                <span className="text-[#e6edf3] font-bold">{stats.ingestion_time_sec}s</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-[#0d1117] border border-[#30363d]">
                <span className="text-[#8b949e]">Tree-sitter AST Parsing:</span>
                <span className="text-[#e6edf3] font-bold">{stats.parsing_time_sec}s</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-[#0d1117] border border-[#30363d]">
                <span className="text-[#8b949e]">Local Embeddings Generation:</span>
                <span className="text-[#e6edf3] font-bold">{stats.embedding_time_sec}s</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-[#0d1117] border border-[#30363d]">
                <span className="text-[#8b949e]">FAISS & BM25 Indexing:</span>
                <span className="text-[#e6edf3] font-bold">{stats.indexing_time_sec}s</span>
              </div>
              <div className="flex justify-between items-center p-2.5 rounded bg-emerald-950/30 border border-emerald-800/50 text-emerald-400">
                <span>Total End-to-End Build Time:</span>
                <span className="font-bold text-sm">{stats.total_pipeline_time_sec}s</span>
              </div>
            </div>
          </div>

          {/* Retrieval Engine Specs */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 text-sm font-semibold text-[#e6edf3]">
              <Cpu className="w-4 h-4 text-[#58a6ff]" />
              <span>Retrieval Engine Architecture</span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-2 rounded bg-[#0d1117] border border-[#30363d] space-y-1">
                <div className="text-[11px] text-[#8b949e]">Embedding Model:</div>
                <div className="text-[#58a6ff] font-semibold">{stats.embedding_model}</div>
              </div>
              <div className="p-2 rounded bg-[#0d1117] border border-[#30363d] space-y-1">
                <div className="text-[11px] text-[#8b949e]">Dense Dimension & Index Type:</div>
                <div className="text-[#e6edf3]">
                  {stats.embedding_dimension} dims • <strong className="text-emerald-400">faiss.IndexFlatIP</strong> (Cosine)
                </div>
              </div>
              <div className="p-2 rounded bg-[#0d1117] border border-[#30363d] space-y-1">
                <div className="text-[11px] text-[#8b949e]">Lexical Index:</div>
                <div className="text-[#e6edf3]">BM25Okapi (k1=1.5, b=0.75) with Subword Splitting</div>
              </div>
              <div className="p-2 rounded bg-[#0d1117] border border-[#30363d] space-y-1">
                <div className="text-[11px] text-[#8b949e]">Hardware Acceleration:</div>
                <div className="text-emerald-400">Apple Silicon MPS / CUDA Auto-detected</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
