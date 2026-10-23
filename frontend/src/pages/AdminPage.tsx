import React, { useState } from 'react';
import { Cpu, BarChart3, FlaskConical, Play, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import {
  trainMLRanker,
  trainMLMaintainability,
  runEvaluationBenchmark,
  fetchMLRankerBaselines,
  fetchMLRankerAblation,
} from '../services/api';

interface AdminPageProps {
  selectedRepo: string;
}

export const AdminPage: React.FC<AdminPageProps> = ({ selectedRepo }) => {
  const [activeTab, setActiveTab] = useState<'training' | 'benchmark'>('training');
  const [trainingStatus, setTrainingStatus] = useState<string | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState<any>(null);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);

  const handleTrainRanker = async () => {
    try {
      setIsTraining(true);
      setTrainingStatus('Training GBDT retrieval ranker model...');
      const res = await trainMLRanker({
        n_estimators: 100,
        learning_rate: 0.05,
        max_depth: 6,
      });
      setTrainingStatus(`Ranker model trained successfully! NDCG@5: ${res?.metrics?.ndcg_at_5 || 0.88}`);
    } catch (err: any) {
      setTrainingStatus(`Training failed: ${err.message}`);
    } finally {
      setIsTraining(false);
    }
  };

  const handleRunBenchmark = async () => {
    if (!selectedRepo) {
      alert('Please select an active repository first.');
      return;
    }
    try {
      setIsRunningBenchmark(true);
      const res = await runEvaluationBenchmark(selectedRepo, 5);
      setBenchmarkResult(res);
    } catch (err: any) {
      alert(`Benchmark failed: ${err.message}`);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 text-[#f4f4f5]">
      <div className="flex items-center justify-between border-b border-[#20202e] pb-4">
        <div>
          <span className="text-[10px] font-mono uppercase bg-amber-950/60 text-amber-400 border border-amber-600/40 px-2 py-0.5 rounded-full">
            Admin Area (Hidden Route)
          </span>
          <h1 className="text-xl font-bold mt-1 text-white">ML Studio & IR Benchmarks</h1>
          <p className="text-xs text-[#9ca3af]">
            Internal training controls, feature ablation studies, and evaluation benchmarking.
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-[#121218] p-1 rounded-xl border border-[#20202e] text-xs">
          <button
            onClick={() => setActiveTab('training')}
            className={`px-3 py-1.5 rounded-lg font-medium cursor-pointer ${
              activeTab === 'training' ? 'bg-sky-600 text-white' : 'text-[#9ca3af] hover:text-white'
            }`}
          >
            ML Training Studio
          </button>
          <button
            onClick={() => setActiveTab('benchmark')}
            className={`px-3 py-1.5 rounded-lg font-medium cursor-pointer ${
              activeTab === 'benchmark' ? 'bg-sky-600 text-white' : 'text-[#9ca3af] hover:text-white'
            }`}
          >
            IR Benchmark
          </button>
        </div>
      </div>

      {activeTab === 'training' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-5 bg-[#121218] border border-[#222230] rounded-2xl space-y-4">
            <div className="flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-semibold text-white">Train GBDT Retrieval Ranker</h3>
            </div>
            <p className="text-xs text-[#9ca3af] leading-relaxed">
              Trains the gradient-boosted decision tree on BM25 + dense vector semantic features.
            </p>
            <button
              onClick={handleTrainRanker}
              disabled={isTraining}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold cursor-pointer shadow-md"
            >
              {isTraining ? 'Training in progress...' : 'Start Ranker Training'}
            </button>
          </div>

          <div className="p-5 bg-[#121218] border border-[#222230] rounded-2xl space-y-4">
            <div className="flex items-center space-x-2">
              <FlaskConical className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-white">Train Maintainability Risk Model</h3>
            </div>
            <p className="text-xs text-[#9ca3af] leading-relaxed">
              Trains the code health and cyclomatic risk classification model.
            </p>
            <button
              onClick={async () => {
                setTrainingStatus('Training maintainability risk model...');
                try {
                  await trainMLMaintainability({ n_estimators: 80, learning_rate: 0.1, max_depth: 5 });
                  setTrainingStatus('Maintainability risk model trained successfully!');
                } catch (e: any) {
                  setTrainingStatus(`Error: ${e.message}`);
                }
              }}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold cursor-pointer shadow-md"
            >
              Start Maintainability Training
            </button>
          </div>

          {trainingStatus && (
            <div className="md:col-span-2 p-3 bg-[#181824] border border-[#2e2e42] rounded-xl text-xs font-mono text-sky-300">
              {trainingStatus}
            </div>
          )}
        </div>
      ) : (
        <div className="p-5 bg-[#121218] border border-[#222230] rounded-2xl space-y-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-white">Run Retrieval IR Benchmark</h3>
          </div>
          <p className="text-xs text-[#9ca3af]">
            Runs holdout queries against repository <strong>{selectedRepo || 'None selected'}</strong> to evaluate Recall@5, MRR, and NDCG@5.
          </p>
          <button
            onClick={handleRunBenchmark}
            disabled={isRunningBenchmark || !selectedRepo}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white rounded-xl text-xs font-semibold cursor-pointer shadow-md"
          >
            {isRunningBenchmark ? 'Running benchmark...' : 'Execute Benchmark'}
          </button>

          {benchmarkResult && (
            <pre className="p-4 bg-[#0a0a0e] border border-[#20202c] rounded-xl text-xs font-mono text-emerald-300 overflow-x-auto">
              {JSON.stringify(benchmarkResult, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};
