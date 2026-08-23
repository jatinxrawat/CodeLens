import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Navbar } from './components/layout/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { SearchPage } from './pages/SearchPage';
import { AskCodebasePage } from './pages/AskCodebasePage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { ImpactAnalysisPage } from './pages/ImpactAnalysisPage';
import { CodeFlowPage } from './pages/CodeFlowPage';
import { CodeQualityPage } from './pages/CodeQualityPage';
import { SecurityPage } from './pages/SecurityPage';
import { ExplorerPage } from './pages/ExplorerPage';
import { GraphPage } from './pages/GraphPage';
import { ReportsPage } from './pages/ReportsPage';
import { ComparisonPage } from './pages/ComparisonPage';
import { RepositoriesPage } from './pages/RepositoriesPage';
import { MetricsPage } from './pages/MetricsPage';
import { MLStudioPage } from './pages/MLStudioPage';
import type { RepositorySummary } from './types';
import { fetchRepositories } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const [searchInitialQuery, setSearchInitialQuery] = useState<string>('');
  const [explorerTargetFile, setExplorerTargetFile] = useState<string>('');

  const loadRepositories = async () => {
    try {
      const repos = await fetchRepositories();
      setRepositories(repos);
      if (repos.length > 0 && !selectedRepo) {
        setSelectedRepo(repos[0].repository_id);
      }
    } catch (err) {
      console.error('Failed to load repositories', err);
    }
  };

  useEffect(() => {
    loadRepositories();
  }, []);

  const handleNavigateToSearch = (query?: string) => {
    if (query) {
      setSearchInitialQuery(query);
    }
    setCurrentTab('search');
  };

  const handleOpenFileInExplorer = (filePath: string) => {
    setExplorerTargetFile(filePath);
    setCurrentTab('explorer');
  };

  return (
    <div className="flex h-screen bg-[#0b0f14] text-[#e6edf3] font-sans antialiased overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        repositories={repositories}
        selectedRepo={selectedRepo}
        setSelectedRepo={setSelectedRepo}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar
          currentTab={currentTab}
          selectedRepo={selectedRepo}
          onQuickSearch={() => setCurrentTab('search')}
        />

        <main className="flex-1 overflow-y-auto bg-[#0b0f14]">
          {currentTab === 'dashboard' && (
            <DashboardPage
              selectedRepo={selectedRepo}
              onNavigateToSearch={handleNavigateToSearch}
              onNavigateToRepositories={() => setCurrentTab('repositories')}
              onNavigateToExplorer={() => setCurrentTab('explorer')}
            />
          )}

          {currentTab === 'search' && (
            <SearchPage
              selectedRepo={selectedRepo}
              initialQuery={searchInitialQuery}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {currentTab === 'ask' && (
            <AskCodebasePage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {currentTab === 'architecture' && (
            <ArchitecturePage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {currentTab === 'impact' && (
            <ImpactAnalysisPage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {currentTab === 'flow' && (
            <CodeFlowPage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {currentTab === 'quality' && (
            <CodeQualityPage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {currentTab === 'security' && (
            <SecurityPage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {currentTab === 'explorer' && (
            <ExplorerPage
              selectedRepo={selectedRepo}
              initialFilePath={explorerTargetFile}
            />
          )}

          {currentTab === 'graph' && (
            <GraphPage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {currentTab === 'reports' && (
            <ReportsPage selectedRepo={selectedRepo} />
          )}

          {currentTab === 'comparison' && (
            <ComparisonPage repositories={repositories} />
          )}

          {currentTab === 'repositories' && (
            <RepositoriesPage
              repositories={repositories}
              selectedRepo={selectedRepo}
              onSelectRepo={setSelectedRepo}
              onRefreshRepositories={loadRepositories}
            />
          )}

          {currentTab === 'mlstudio' && (
            <MLStudioPage />
          )}

          {currentTab === 'evaluation' && (
            <MetricsPage selectedRepo={selectedRepo} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
