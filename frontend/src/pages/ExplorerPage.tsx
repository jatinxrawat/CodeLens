import React, { useState, useEffect } from 'react';
import {
  FileCode,
  Folder,
  ChevronRight,
  ChevronDown,
  Copy,
  Check,
  Code2,
  Layers,
  Search,
} from 'lucide-react';
import { FileItem, FileContent } from '../types';
import { fetchRepositoryFiles, fetchFileContent } from '../services/api';

interface ExplorerPageProps {
  selectedRepo: string;
  initialFilePath?: string;
}

export const ExplorerPage: React.FC<ExplorerPageProps> = ({
  selectedRepo,
  initialFilePath,
}) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [loadingContent, setLoadingContent] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoadingFiles(true);
    fetchRepositoryFiles(selectedRepo)
      .then((items) => {
        setFiles(items);
        const target = initialFilePath || (items.length > 0 ? items[0].path : null);
        if (target) {
          setSelectedFile(target);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setLoadingFiles(false));
  }, [selectedRepo]);

  useEffect(() => {
    if (!selectedRepo || !selectedFile) return;
    setLoadingContent(true);
    fetchFileContent(selectedRepo, selectedFile)
      .then(setFileContent)
      .catch((err) => console.error(err))
      .finally(() => setLoadingContent(false));
  }, [selectedRepo, selectedFile]);

  const handleCopy = () => {
    if (fileContent?.code) {
      navigator.clipboard.writeText(fileContent.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const filteredFiles = files.filter((f) =>
    f.path.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const activeFileInfo = files.find((f) => f.path === selectedFile);

  return (
    <div className="flex h-[calc(100vh-3.5rem)] bg-[#0b0f14] overflow-hidden">
      {/* File Tree Sidebar */}
      <div className="w-80 bg-[#0d1117] border-r border-[#30363d] flex flex-col shrink-0">
        <div className="p-3 border-b border-[#30363d]">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#8b949e] absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Filter files..."
              className="w-full bg-[#161b22] border border-[#30363d] rounded-md pl-8 pr-2 py-1.5 text-xs text-[#e6edf3] placeholder-[#8b949e] focus:outline-none focus:border-[#58a6ff] font-mono"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {loadingFiles && (
            <div className="p-4 text-xs text-[#8b949e] text-center">Loading files...</div>
          )}
          {!loadingFiles && filteredFiles.length === 0 && (
            <div className="p-4 text-xs text-[#8b949e] text-center">No matching files found.</div>
          )}
          {filteredFiles.map((file) => {
            const isSelected = selectedFile === file.path;
            return (
              <button
                key={file.path}
                onClick={() => setSelectedFile(file.path)}
                className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-mono flex items-center justify-between transition-colors ${
                  isSelected
                    ? 'bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/30'
                    : 'text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#161b22]'
                }`}
              >
                <div className="flex items-center space-x-2 truncate pr-2">
                  <FileCode className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-[#58a6ff]' : 'text-emerald-400'}`} />
                  <span className="truncate">{file.path}</span>
                </div>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#161b22] text-[#8b949e] shrink-0">
                  {file.total_chunks}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Code Viewer */}
      <div className="flex-1 flex flex-col bg-[#0b0f14] overflow-hidden">
        {selectedFile && (
          <div className="h-11 bg-[#161b22] border-b border-[#30363d] px-4 flex items-center justify-between shrink-0">
            <div className="flex items-center space-x-2 font-mono text-xs text-[#e6edf3]">
              <FileCode className="w-4 h-4 text-emerald-400" />
              <span>{selectedFile}</span>
              {fileContent && (
                <span className="text-[#8b949e] text-[11px]">
                  ({fileContent.total_lines} lines • {fileContent.language})
                </span>
              )}
            </div>
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-2.5 py-1 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] rounded text-xs transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Code'}</span>
            </button>
          </div>
        )}

        <div className="flex-1 flex overflow-hidden">
          {/* Source Code View */}
          <div className="flex-1 overflow-auto p-4 font-mono text-xs text-[#e6edf3] bg-[#0d1117] leading-relaxed select-text">
            {loadingContent && (
              <div className="p-8 text-center text-[#8b949e]">Loading file content...</div>
            )}
            {!loadingContent && fileContent && (
              <pre className="table w-full">
                {fileContent.code.split('\n').map((line, idx) => (
                  <div key={idx} className="table-row hover:bg-[#161b22]/50">
                    <span className="table-cell select-none text-[#8b949e] pr-4 text-right opacity-50 w-10">
                      {idx + 1}
                    </span>
                    <span className="table-cell whitespace-pre">{line}</span>
                  </div>
                ))}
              </pre>
            )}
          </div>

          {/* Detected Symbols Outline Panel */}
          {activeFileInfo && activeFileInfo.symbols.length > 0 && (
            <div className="w-64 bg-[#0d1117] border-l border-[#30363d] p-3 overflow-y-auto shrink-0 space-y-2">
              <h4 className="text-[11px] font-semibold text-[#8b949e] uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                <Code2 className="w-3.5 h-3.5 text-[#58a6ff]" />
                <span>Detected AST Symbols</span>
              </h4>
              <div className="space-y-1">
                {activeFileInfo.symbols.map((sym, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded bg-[#161b22] border border-[#30363d] text-xs font-mono space-y-0.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[#58a6ff] font-medium truncate">{sym.symbol}</span>
                      <span className="text-[10px] text-emerald-400 bg-emerald-950/40 px-1 rounded">
                        {sym.type}
                      </span>
                    </div>
                    <div className="text-[10px] text-[#8b949e]">
                      Lines {sym.start_line}–{sym.end_line}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
