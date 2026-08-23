import React, { useState, useEffect } from 'react';
import {
  Layers,
  ArrowDown,
  FileCode,
  Box,
  FolderTree,
  ShieldCheck,
  ExternalLink,
} from 'lucide-react';
import type { ArchitectureReport, ArchitectureLayer } from '../types';
import { fetchArchitectureAnalysis } from '../services/api';

interface ArchitecturePageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
}

export const ArchitecturePage: React.FC<ArchitecturePageProps> = ({
  selectedRepo,
  onOpenFileInExplorer,
}) => {
  const [report, setReport] = useState<ArchitectureReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoading(true);
    fetchArchitectureAnalysis(selectedRepo)
      .then((data) => {
        setReport(data);
        if (data.layers.length > 0) {
          setSelectedLayer(data.layers[0].name);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedRepo]);

  const activeLayerData = report?.layers.find((l) => l.name === selectedLayer);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div>
        <h1 className="text-lg font-semibold text-[#e6edf3]">Inferred Architecture & Structural Layers</h1>
        <p className="text-xs text-[#8b949e] mt-0.5">
          Infers subsystem boundaries, architectural patterns, and layer topologies from static AST imports and directory conventions.
        </p>
      </div>

      {report && (
        <div className="space-y-6">
          {/* Pattern Banner */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#8b949e]">
                Inferred Architectural Pattern
              </span>
              <h2 className="text-base font-bold text-[#e6edf3] font-mono mt-0.5">
                {report.inferred_pattern}
              </h2>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono bg-emerald-950 text-emerald-400 border border-emerald-800 px-2.5 py-1 rounded">
                Status: {report.status}
              </span>
            </div>
          </div>

          {/* Directional Layer Stack */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Left: Interactive Layer Stack */}
            <div className="md:col-span-1 bg-[#161b22] border border-[#30363d] rounded-xl p-4 space-y-2">
              <h3 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-3 px-1">
                Subsystem Layer Stack
              </h3>

              <div className="space-y-2">
                {report.layers.map((layer: ArchitectureLayer, idx: number) => {
                  const isSelected = selectedLayer === layer.name;
                  return (
                    <React.Fragment key={layer.name}>
                      <button
                        onClick={() => setSelectedLayer(layer.name)}
                        className={`w-full text-left p-3 rounded-lg border text-xs font-mono transition-all ${
                          isSelected
                            ? 'bg-[#1f6feb]/15 border-[#58a6ff] text-[#58a6ff] ring-1 ring-[#58a6ff]'
                            : 'bg-[#0d1117] border-[#30363d] text-[#e6edf3] hover:border-[#484f58]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold">{layer.name}</span>
                          <span className="text-[10px] text-[#8b949e]">
                            {layer.file_count} file(s)
                          </span>
                        </div>
                        <div className="text-[11px] text-[#8b949e] truncate">
                          {layer.primary_languages.join(', ')} • {layer.symbol_count} symbols
                        </div>
                      </button>

                      {idx < report.layers.length - 1 && (
                        <div className="flex justify-center py-0.5">
                          <ArrowDown className="w-3.5 h-3.5 text-[#30363d]" />
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>

            {/* Right: Layer Inspector Detail */}
            <div className="md:col-span-2 bg-[#161b22] border border-[#30363d] rounded-xl p-5 space-y-4">
              {activeLayerData ? (
                <>
                  <div className="flex items-center justify-between pb-3 border-b border-[#30363d]">
                    <div>
                      <h3 className="text-sm font-bold text-[#e6edf3] font-mono">
                        {activeLayerData.name}
                      </h3>
                      <p className="text-xs text-[#8b949e] mt-0.5">{activeLayerData.description}</p>
                    </div>
                    <span className="text-xs font-mono bg-[#0d1117] border border-[#30363d] px-2.5 py-1 rounded text-emerald-400">
                      Confidence: {(activeLayerData.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  {/* Files in Layer */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center space-x-1.5">
                      <FileCode className="w-3.5 h-3.5 text-[#58a6ff]" />
                      <span>Associated Source Files ({activeLayerData.files.length})</span>
                    </h4>

                    <div className="space-y-1.5 max-h-80 overflow-y-auto">
                      {activeLayerData.files.map((file) => (
                        <div
                          key={file}
                          className="flex items-center justify-between p-2 rounded bg-[#0d1117] border border-[#30363d] text-xs font-mono hover:border-[#484f58] transition-colors"
                        >
                          <span className="text-[#e6edf3] truncate pr-2">{file}</span>
                          <button
                            onClick={() => onOpenFileInExplorer(file)}
                            className="flex items-center space-x-1 text-[#58a6ff] hover:underline text-[11px] shrink-0"
                          >
                            <span>Inspect</span>
                            <ExternalLink className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-[#8b949e]">Select a layer to view details.</div>
              )}
            </div>
          </div>

          {/* Disclaimer */}
          <div className="p-3 bg-[#0d1117] border border-[#30363d] rounded-lg text-[11px] text-[#8b949e]">
            {report.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
