import React, { useState, useEffect, useMemo } from 'react';
import { Network, Search, ArrowRight, ArrowLeft, ExternalLink, ShieldCheck, Box } from 'lucide-react';
import { GraphResponse, GraphNode, GraphEdge } from '../types';
import { fetchDependencyGraph } from '../services/api';

interface GraphPageProps {
  selectedRepo: string;
  onOpenFileInExplorer: (filePath: string) => void;
}

export const GraphPage: React.FC<GraphPageProps> = ({ selectedRepo, onOpenFileInExplorer }) => {
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [filterExternal, setFilterExternal] = useState(false);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoading(true);
    fetchDependencyGraph(selectedRepo)
      .then(setGraphData)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedRepo]);

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

  // Incoming edges (files that import this node)
  const incomingEdges = useMemo(() => {
    if (!graphData || !selectedNodeId) return [];
    return graphData.edges.filter((e) => e.target === selectedNodeId);
  }, [graphData, selectedNodeId]);

  // Outgoing edges (files/packages imported by this node)
  const outgoingEdges = useMemo(() => {
    if (!graphData || !selectedNodeId) return [];
    return graphData.edges.filter((e) => e.source === selectedNodeId);
  }, [graphData, selectedNodeId]);

  return (
    <div className="flex h-[calc(100vh-3.5rem)] bg-[#0b0f14] overflow-hidden">
      {/* Node Search & Filter Sidebar */}
      <div className="w-80 bg-[#0d1117] border-r border-[#30363d] flex flex-col shrink-0">
        <div className="p-3 border-b border-[#30363d] space-y-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#8b949e] absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search module or package..."
              className="w-full bg-[#161b22] border border-[#30363d] rounded-md pl-8 pr-2 py-1.5 text-xs text-[#e6edf3] placeholder-[#8b949e] focus:outline-none focus:border-[#58a6ff] font-mono"
            />
          </div>
          <div className="flex items-center justify-between text-xs text-[#8b949e]">
            <label className="flex items-center space-x-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={filterExternal}
                onChange={(e) => setFilterExternal(e.target.checked)}
                className="rounded bg-[#161b22] border-[#30363d] accent-[#1f6feb]"
              />
              <span className="text-[11px]">Hide external libs</span>
            </label>
            <span className="font-mono text-[11px]">
              {filteredNodes.length} / {graphData?.total_nodes || 0} nodes
            </span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loading && <div className="p-4 text-xs text-[#8b949e] text-center">Loading graph...</div>}
          {!loading && filteredNodes.map((node) => {
            const isSelected = selectedNodeId === node.id;
            return (
              <button
                key={node.id}
                onClick={() => setSelectedNodeId(node.id)}
                className={`w-full text-left px-2.5 py-2 rounded-md text-xs font-mono transition-colors ${
                  isSelected
                    ? 'bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/30'
                    : 'text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#161b22]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="truncate font-semibold text-[#e6edf3]">{node.label}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded font-sans ${
                      node.type === 'file'
                        ? 'bg-emerald-950 text-emerald-400'
                        : 'bg-purple-950 text-purple-400'
                    }`}
                  >
                    {node.type === 'file' ? node.language || 'file' : 'external'}
                  </span>
                </div>
                <div className="text-[10px] text-[#8b949e] truncate mt-0.5">{node.path}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Graph Visualization Area */}
      <div className="flex-1 flex flex-col bg-[#0b0f14] overflow-hidden">
        {/* Graph Header */}
        <div className="h-11 bg-[#161b22] border-b border-[#30363d] px-4 flex items-center justify-between shrink-0 text-xs">
          <div className="flex items-center space-x-2 text-[#e6edf3]">
            <Network className="w-4 h-4 text-[#58a6ff]" />
            <span className="font-semibold">Static AST Dependency Network</span>
            <span className="text-[#8b949e] font-mono">
              ({graphData?.total_nodes || 0} nodes • {graphData?.total_edges || 0} edges)
            </span>
          </div>
          <div className="flex items-center space-x-4 text-[11px] text-[#8b949e]">
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Local Source File</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
              <span>External Package</span>
            </span>
          </div>
        </div>

        {/* Visual Graph Grid Layout */}
        <div className="flex-1 p-6 overflow-auto bg-[#090d12] flex flex-wrap content-start gap-4">
          {filteredNodes.map((node) => {
            const isSelected = selectedNodeId === node.id;
            return (
              <div
                key={node.id}
                onClick={() => setSelectedNodeId(node.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-all w-60 shadow-sm ${
                  isSelected
                    ? 'bg-[#1f6feb]/15 border-[#58a6ff] ring-1 ring-[#58a6ff]'
                    : 'bg-[#161b22] border-[#30363d] hover:border-[#484f58]'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-mono font-semibold text-[#e6edf3] truncate">
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

                <div className="text-[11px] text-[#8b949e] font-mono truncate">{node.path}</div>

                <div className="mt-3 pt-2 border-t border-[#30363d]/60 flex items-center justify-between text-[10px] text-[#8b949e] font-mono">
                  <span>In: {node.in_degree}</span>
                  <span>Out: {node.out_degree}</span>
                  {node.type === 'file' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenFileInExplorer(node.path);
                      }}
                      className="text-[#58a6ff] hover:underline"
                    >
                      View
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="w-80 bg-[#0d1117] border-l border-[#30363d] p-4 overflow-y-auto shrink-0 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-[#e6edf3] font-mono truncate">{selectedNode.label}</h3>
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                selectedNode.type === 'file'
                  ? 'bg-emerald-950 text-emerald-400'
                  : 'bg-purple-950 text-purple-400'
              }`}
            >
              {selectedNode.type}
            </span>
          </div>

          <div className="text-xs font-mono text-[#8b949e] break-all bg-[#161b22] p-2 rounded border border-[#30363d]">
            {selectedNode.path}
          </div>

          {selectedNode.type === 'file' && (
            <button
              onClick={() => onOpenFileInExplorer(selectedNode.path)}
              className="w-full flex items-center justify-center space-x-1.5 py-1.5 bg-[#1f6feb] hover:bg-[#388bfd] text-white rounded text-xs font-medium transition-colors"
            >
              <span>Inspect Source in Explorer</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Outgoing Imports */}
          <div>
            <h4 className="text-[11px] font-semibold text-[#8b949e] uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />
              <span>Imports & Dependencies ({outgoingEdges.length})</span>
            </h4>
            {outgoingEdges.length === 0 ? (
              <p className="text-[11px] text-[#8b949e] italic">No detected imports.</p>
            ) : (
              <div className="space-y-1">
                {outgoingEdges.map((e, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedNodeId(e.target)}
                    className="p-2 rounded bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-xs font-mono cursor-pointer transition-colors"
                  >
                    <div className="text-[#e6edf3] font-medium truncate">{e.target}</div>
                    {e.raw_import && (
                      <div className="text-[10px] text-[#8b949e] truncate">raw: {e.raw_import}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Incoming Imports */}
          <div>
            <h4 className="text-[11px] font-semibold text-[#8b949e] uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <ArrowLeft className="w-3.5 h-3.5 text-blue-400" />
              <span>Imported By ({incomingEdges.length})</span>
            </h4>
            {incomingEdges.length === 0 ? (
              <p className="text-[11px] text-[#8b949e] italic">No local files import this module.</p>
            ) : (
              <div className="space-y-1">
                {incomingEdges.map((e, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedNodeId(e.source)}
                    className="p-2 rounded bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-xs font-mono cursor-pointer transition-colors"
                  >
                    <div className="text-[#e6edf3] font-medium truncate">{e.source}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
