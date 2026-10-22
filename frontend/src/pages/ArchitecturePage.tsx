import React, { useState, useEffect, useMemo } from 'react';
import {
  Layers,
  Network,
  ArrowDown,
  ArrowRight,
  ArrowLeft,
  FileCode,
  Box,
  FolderTree,
  ShieldCheck,
  ExternalLink,
  Search,
} from 'lucide-react';
import type { ArchitectureReport, ArchitectureLayer, GraphResponse, GraphNode, GraphEdge } from '../types';
import { fetchArchitectureAnalysis, fetchDependencyGraph } from '../services/api';

interface ArchitecturePageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
  defaultView?: 'layers' | 'graph';
}

export const ArchitecturePage: React.FC<ArchitecturePageProps> = ({
  selectedRepo,
  onOpenFileInExplorer,
  defaultView = 'layers',
}) => {
  const [viewMode, setViewMode] = useState<'layers' | 'graph'>(defaultView);

  // Layers State
  const [report, setReport] = useState<ArchitectureReport | null>(null);
  const [loadingLayers, setLoadingLayers] = useState(false);
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);

  // Graph State
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [filterExternal, setFilterExternal] = useState(false);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoadingLayers(true);
    fetchArchitectureAnalysis(selectedRepo)
      .then((data) => {
        setReport(data);
        if (data.layers.length > 0) {
          setSelectedLayer(data.layers[0].name);
        }
      })
      .catch((err) => console.error('Failed to load architecture:', err))
      .finally(() => setLoadingLayers(false));

    setLoadingGraph(true);
    fetchDependencyGraph(selectedRepo)
      .then(setGraphData)
      .catch((err) => console.error('Failed to load dependency graph:', err))
      .finally(() => setLoadingGraph(false));
  }, [selectedRepo]);

  const activeLayerData = report?.layers.find((l) => l.name === selectedLayer);

  // Graph filtered nodes
  const filteredNodes = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes.filter((node) => {
      if (filterExternal && node.type === 'external_package') return false;
      if (!searchFilter) return true;
      return (
        node.label.toLowerCase().includes(searchFilter.toLowerCase()) ||
        node.path.toLowerCase().includes(searchFilter.toLowerCase())
      );
    });
  }, [graphData, searchFilter, filterExternal]);

  const selectedNode = graphData?.nodes.find((n) => n.id === selectedNodeId);

  const incomingEdges = useMemo(() => {
    if (!graphData || !selectedNodeId) return [];
    return graphData.edges.filter((e) => e.target === selectedNodeId);
  }, [graphData, selectedNodeId]);

  const outgoingEdges = useMemo(() => {
    if (!graphData || !selectedNodeId) return [];
    return graphData.edges.filter((e) => e.source === selectedNodeId);
  }, [graphData, selectedNodeId]);

  return (
    <div className="flex flex-col h-full bg-[#121215] text-[#ececec] overflow-hidden select-none">
      {/* Top Header & View Mode Switcher */}
      <div className="h-14 px-6 border-b border-[#252532] bg-[#14141a] flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-sm font-semibold text-white flex items-center space-x-2">
            <Layers className="w-4 h-4 text-sky-400" />
            <span>Architecture & Dependency Network</span>
          </h1>
          <p className="text-[11px] text-[#a1a1aa]">
            Inferred subsystem layers, architectural topologies, and interactive static AST import graph.
          </p>
        </div>

        {/* View Switcher Pills */}
        <div className="flex items-center bg-[#1c1c26] p-1 rounded-xl border border-[#2e2e40] space-x-1">
          <button
            onClick={() => setViewMode('layers')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              viewMode === 'layers'
                ? 'bg-sky-500 text-white shadow-md'
                : 'text-[#a1a1aa] hover:text-white hover:bg-[#252535]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Layers View</span>
            {report && (
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${viewMode === 'layers' ? 'bg-sky-700 text-white' : 'bg-[#28283a] text-[#a1a1aa]'}`}>
                {report.layers.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setViewMode('graph')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              viewMode === 'graph'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-[#a1a1aa] hover:text-white hover:bg-[#252535]'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Dependency Graph</span>
            {graphData && (
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${viewMode === 'graph' ? 'bg-indigo-800 text-white' : 'bg-[#28283a] text-[#a1a1aa]'}`}>
                {graphData.total_nodes}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ================= VIEW 1: ARCHITECTURAL LAYERS VIEW ================= */}
      {viewMode === 'layers' && (
        <div className="flex-1 overflow-y-auto p-6 max-w-6xl w-full mx-auto space-y-6 animate-in fade-in duration-200">
          {!selectedRepo && (
            <div className="p-8 text-center bg-[#181822] border border-[#2e2e42] rounded-2xl text-xs text-[#a1a1aa]">
              Please select or attach a repository in the sidebar to inspect architectural layers.
            </div>
          )}

          {loadingLayers && (
            <div className="p-12 text-center text-xs text-[#a1a1aa]">Inferring architectural layer topology...</div>
          )}

          {report && (
            <div className="space-y-6">
              {/* Pattern Banner */}
              <div className="bg-[#181822] border border-[#2e2e42] rounded-2xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-wider text-[#a1a1aa]">
                    Inferred Architectural Pattern
                  </span>
                  <h2 className="text-lg font-bold text-white font-mono mt-0.5">
                    {report.inferred_pattern}
                  </h2>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono bg-emerald-950/50 text-emerald-300 border border-emerald-800/50 px-3 py-1 rounded-lg">
                    Status: {report.status}
                  </span>
                </div>
              </div>

              {/* Directional Layer Stack */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Left: Interactive Layer Stack */}
                <div className="md:col-span-1 bg-[#181822] border border-[#2e2e42] rounded-2xl p-4 space-y-2">
                  <h3 className="text-xs font-semibold text-[#a1a1aa] uppercase tracking-wider mb-3 px-1">
                    Subsystem Layer Stack
                  </h3>

                  <div className="space-y-2">
                    {report.layers.map((layer: ArchitectureLayer, idx: number) => {
                      const isSelected = selectedLayer === layer.name;
                      return (
                        <React.Fragment key={layer.name}>
                          <button
                            onClick={() => setSelectedLayer(layer.name)}
                            className={`w-full text-left p-3 rounded-xl border text-xs font-mono transition-all cursor-pointer ${
                              isSelected
                                ? 'bg-sky-500/15 border-sky-500 text-sky-400 ring-1 ring-sky-500 shadow-sm'
                                : 'bg-[#14141e] border-[#29293d] text-[#ececec] hover:border-[#3e3e58]'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-bold text-sm">{layer.name}</span>
                              <span className="text-[10px] text-[#a1a1aa] bg-[#222230] px-1.5 py-0.5 rounded">
                                {layer.file_count} file(s)
                              </span>
                            </div>
                            <div className="text-[11px] text-[#71717a] truncate">
                              {layer.primary_languages.join(', ')} • {layer.symbol_count} symbols
                            </div>
                          </button>

                          {idx < report.layers.length - 1 && (
                            <div className="flex justify-center py-0.5">
                              <ArrowDown className="w-3.5 h-3.5 text-[#3e3e58]" />
                            </div>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>
                </div>

                {/* Right: Layer Inspector Detail */}
                <div className="md:col-span-2 bg-[#181822] border border-[#2e2e42] rounded-2xl p-5 space-y-4">
                  {activeLayerData ? (
                    <>
                      <div className="flex items-center justify-between pb-3 border-b border-[#29293d]">
                        <div>
                          <h3 className="text-base font-bold text-white font-mono">
                            {activeLayerData.name}
                          </h3>
                          <p className="text-xs text-[#a1a1aa] mt-0.5">{activeLayerData.description}</p>
                        </div>
                        <span className="text-xs font-mono bg-[#14141e] border border-[#29293d] px-2.5 py-1 rounded-lg text-emerald-400">
                          Confidence: {(activeLayerData.confidence * 100).toFixed(0)}%
                        </span>
                      </div>

                      {/* Files in Layer */}
                      <div className="space-y-2">
                        <h4 className="text-xs font-semibold text-[#a1a1aa] uppercase tracking-wider flex items-center space-x-1.5">
                          <FileCode className="w-3.5 h-3.5 text-sky-400" />
                          <span>Associated Source Files ({activeLayerData.files.length})</span>
                        </h4>

                        <div className="space-y-1.5 max-h-96 overflow-y-auto pr-1">
                          {activeLayerData.files.map((file) => (
                            <div
                              key={file}
                              className="flex items-center justify-between p-2.5 rounded-xl bg-[#14141e] border border-[#28283a] text-xs font-mono hover:border-[#3e3e58] transition-colors"
                            >
                              <span className="text-[#ececec] truncate pr-2">{file}</span>
                              <button
                                onClick={() => onOpenFileInExplorer(file)}
                                className="flex items-center space-x-1 text-sky-400 hover:underline text-[11px] shrink-0 cursor-pointer"
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
                    <div className="p-8 text-center text-[#a1a1aa]">Select a layer to view details.</div>
                  )}
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-3 bg-[#14141e] border border-[#28283a] rounded-xl text-[11px] text-[#71717a]">
                {report.disclaimer}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ================= VIEW 2: INTERACTIVE DEPENDENCY GRAPH VIEW ================= */}
      {viewMode === 'graph' && (
        <div className="flex-1 flex overflow-hidden animate-in fade-in duration-200">
          {/* Node Search & Filter Sidebar */}
          <div className="w-80 bg-[#161620] border-r border-[#262635] flex flex-col shrink-0">
            <div className="p-3 border-b border-[#262635] space-y-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-[#a1a1aa] absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder="Search module or package..."
                  className="w-full bg-[#121218] border border-[#2a2a38] rounded-xl pl-8 pr-2.5 py-1.5 text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>
              <div className="flex items-center justify-between text-xs text-[#a1a1aa]">
                <label className="flex items-center space-x-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filterExternal}
                    onChange={(e) => setFilterExternal(e.target.checked)}
                    className="rounded bg-[#121218] border-[#2a2a38] accent-sky-500"
                  />
                  <span className="text-[11px]">Hide external libs</span>
                </label>
                <span className="font-mono text-[11px]">
                  {filteredNodes.length} / {graphData?.total_nodes || 0} nodes
                </span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {loadingGraph && <div className="p-4 text-xs text-[#a1a1aa] text-center">Loading graph...</div>}
              {!loadingGraph &&
                filteredNodes.map((node) => {
                  const isSelected = selectedNodeId === node.id;
                  return (
                    <button
                      key={node.id}
                      onClick={() => setSelectedNodeId(node.id)}
                      className={`w-full text-left px-2.5 py-2 rounded-xl text-xs font-mono transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
                          : 'text-[#a1a1aa] hover:text-white hover:bg-[#1f1f2c]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="truncate font-semibold text-white">{node.label}</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded font-sans ${
                            node.type === 'file'
                              ? 'bg-emerald-950/60 text-emerald-400'
                              : 'bg-purple-950/60 text-purple-400'
                          }`}
                        >
                          {node.type === 'file' ? node.language || 'file' : 'external'}
                        </span>
                      </div>
                      <div className="text-[10px] text-[#71717a] truncate mt-0.5">{node.path}</div>
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Main Visual Graph Node Grid Layout */}
          <div className="flex-1 flex flex-col bg-[#111116] overflow-hidden">
            {/* Header info */}
            <div className="h-11 bg-[#161620] border-b border-[#262635] px-4 flex items-center justify-between shrink-0 text-xs">
              <div className="flex items-center space-x-2 text-white">
                <Network className="w-4 h-4 text-sky-400" />
                <span className="font-semibold">Static AST Dependency Network</span>
                <span className="text-[#71717a] font-mono">
                  ({graphData?.total_nodes || 0} nodes • {graphData?.total_edges || 0} edges)
                </span>
              </div>
              <div className="flex items-center space-x-4 text-[11px] text-[#a1a1aa]">
                <span className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  <span>Local Source File</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                  <span>External Package</span>
                </span>
              </div>
            </div>

            {/* Visual Node Grid */}
            <div className="flex-1 p-6 overflow-auto bg-[#0d0d12] flex flex-wrap content-start gap-3.5">
              {filteredNodes.map((node) => {
                const isSelected = selectedNodeId === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    className={`p-3.5 rounded-2xl border cursor-pointer transition-all w-64 shadow-sm ${
                      isSelected
                        ? 'bg-sky-500/15 border-sky-400 ring-1 ring-sky-400'
                        : 'bg-[#181822] border-[#29293d] hover:border-[#3e3e58]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-mono font-semibold text-white truncate">
                        {node.label}
                      </span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                          node.type === 'file'
                            ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                            : 'bg-purple-950/60 text-purple-400 border border-purple-800/40'
                        }`}
                      >
                        {node.language || node.type}
                      </span>
                    </div>

                    <div className="text-[11px] text-[#71717a] font-mono truncate">{node.path}</div>

                    <div className="mt-3 pt-2 border-t border-[#29293d] flex items-center justify-between text-[10px] text-[#a1a1aa] font-mono">
                      <span>In: {node.in_degree}</span>
                      <span>Out: {node.out_degree}</span>
                      {node.type === 'file' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenFileInExplorer(node.path);
                          }}
                          className="text-sky-400 hover:underline cursor-pointer"
                        >
                          Inspect →
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Bottom Node Detail Drawer when selected */}
            {selectedNode && (
              <div className="h-44 bg-[#161620] border-t border-[#262635] p-4 flex gap-6 overflow-x-auto shrink-0 animate-in slide-in-from-bottom duration-200">
                <div className="w-64 shrink-0">
                  <h4 className="text-xs font-semibold text-white font-mono truncate">{selectedNode.label}</h4>
                  <p className="text-[10px] font-mono text-[#71717a] truncate mt-0.5">{selectedNode.path}</p>
                  <div className="mt-2 text-[11px] text-[#a1a1aa]">
                    Type: <strong className="text-white">{selectedNode.type}</strong>
                  </div>
                  {selectedNode.type === 'file' && (
                    <button
                      onClick={() => onOpenFileInExplorer(selectedNode.path)}
                      className="mt-3 px-3 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-xs font-medium transition-colors cursor-pointer"
                    >
                      Open in Code Explorer
                    </button>
                  )}
                </div>

                {/* Inbound & Outbound Edges */}
                <div className="flex-1 grid grid-cols-2 gap-4 overflow-y-auto">
                  <div>
                    <h5 className="text-[11px] font-semibold text-[#a1a1aa] uppercase tracking-wider mb-1 flex items-center space-x-1">
                      <ArrowLeft className="w-3 h-3 text-sky-400" />
                      <span>Imported by ({incomingEdges.length})</span>
                    </h5>
                    <div className="space-y-1">
                      {incomingEdges.map((e, idx) => (
                        <div key={idx} className="text-xs font-mono text-[#ececec] truncate bg-[#121218] p-1.5 rounded-lg border border-[#242432]">
                          {e.source}
                        </div>
                      ))}
                      {incomingEdges.length === 0 && (
                        <div className="text-[11px] text-[#71717a]">No inbound imports</div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h5 className="text-[11px] font-semibold text-[#a1a1aa] uppercase tracking-wider mb-1 flex items-center space-x-1">
                      <ArrowRight className="w-3 h-3 text-emerald-400" />
                      <span>Imports ({outgoingEdges.length})</span>
                    </h5>
                    <div className="space-y-1">
                      {outgoingEdges.map((e, idx) => (
                        <div key={idx} className="text-xs font-mono text-[#ececec] truncate bg-[#121218] p-1.5 rounded-lg border border-[#242432]">
                          {e.target}
                        </div>
                      ))}
                      {outgoingEdges.length === 0 && (
                        <div className="text-[11px] text-[#71717a]">No outbound imports</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
