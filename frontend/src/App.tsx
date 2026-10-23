import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Navbar } from './components/layout/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { ChatSearchPage } from './pages/ChatSearchPage';
import { HealthPage } from './pages/HealthPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { ImpactAnalysisPage } from './pages/ImpactAnalysisPage';
import { ExplorerPage } from './pages/ExplorerPage';
import { ReportsPage } from './pages/ReportsPage';
import { ComparisonPage } from './pages/ComparisonPage';
import { RepositoriesPage } from './pages/RepositoriesPage';
import { ExplorePage } from './pages/ExplorePage';
import { ContributePage } from './pages/ContributePage';
import { AdminPage } from './pages/AdminPage';
import type { RepositorySummary } from './types';
import { fetchRepositories } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(() => {
    const path = window.location.pathname.replace(/^\//, '').toLowerCase();
    if (path === 'admin') return 'admin';
    if (path === 'explore') return 'explore';
    if (path === 'contribute') return 'contribute';
    if (path === 'landing') return 'landing';
    const params = new URLSearchParams(window.location.search);
    return params.get('tab') || 'chat';
  });
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const [searchInitialQuery, setSearchInitialQuery] = useState<string>('');
  const [explorerTargetFile, setExplorerTargetFile] = useState<string>('');

  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set('tab', currentTab);
    window.history.replaceState({}, '', url.toString());
  }, [currentTab]);

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
    setCurrentTab('chat');
  };

  const handleOpenFileInExplorer = (filePath: string) => {
    setExplorerTargetFile(filePath);
    setCurrentTab('explorer');
  };

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data && event.data.type === 'CODELENS_NAVIGATE' && event.data.tab) {
        setCurrentTab(event.data.tab);
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  if (currentTab === 'landing') {
    return (
      <div className="w-screen h-screen relative bg-[#0b0f14] overflow-hidden">
        <iframe
          src="/landing/index.html"
          title="CodeLens Public Landing Page"
          className="w-full h-full border-none"
        />
      </div>
    );
  }

  const isChatTab = currentTab === 'chat' || currentTab === 'search' || currentTab === 'ask';

  return (
    <div className="flex h-screen bg-[#000000] text-[#f4f4f5] font-sans antialiased overflow-hidden">
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
        {!isChatTab && (
          <Navbar
            currentTab={currentTab}
            selectedRepo={selectedRepo}
            onQuickSearch={() => setCurrentTab('chat')}
            onSelectTab={setCurrentTab}
          />
        )}

        <main className="flex-1 overflow-y-auto bg-[#000000]">
          {/* 1. Merged Hybrid Search + Ask Codebase (RAG) */}
          {isChatTab && (
            <ChatSearchPage
              selectedRepo={selectedRepo}
              repositories={repositories}
              onSelectRepo={setSelectedRepo}
              onRefreshRepositories={loadRepositories}
              onOpenFileInExplorer={handleOpenFileInExplorer}
              onNavigateToTab={setCurrentTab}
              initialSearchOnly={currentTab === 'search'}
              initialQuery={searchInitialQuery}
            />
          )}

          {currentTab === 'dashboard' && (
            <DashboardPage
              selectedRepo={selectedRepo}
              onNavigateToSearch={handleNavigateToSearch}
              onNavigateToRepositories={() => setCurrentTab('repositories')}
              onNavigateToExplorer={() => setCurrentTab('explorer')}
            />
          )}

          {/* 2. Merged Architecture Layers + Dependency Graph */}
          {(currentTab === 'architecture' || currentTab === 'graph') && (
            <ArchitecturePage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
              defaultView={currentTab === 'graph' ? 'graph' : 'layers'}
            />
          )}

          {/* 3. Merged Code Explorer + Code Flow Tracer */}
          {(currentTab === 'explorer' || currentTab === 'flow') && (
            <ExplorerPage
              selectedRepo={selectedRepo}
              initialFilePath={explorerTargetFile}
            />
          )}

          {/* 4. Merged Quality & Smells + Security Insights */}
          {(currentTab === 'health' || currentTab === 'quality' || currentTab === 'security') && (
            <HealthPage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
              defaultTab={currentTab === 'security' ? 'security' : 'quality'}
            />
          )}

          {currentTab === 'impact' && (
            <ImpactAnalysisPage
              selectedRepo={selectedRepo}
              onOpenFileInExplorer={handleOpenFileInExplorer}
            />
          )}

          {/* 5. Explore Open-Source Repositories */}
          {currentTab === 'explore' && (
            <ExplorePage
              onSelectRepo={setSelectedRepo}
              onNavigateToTab={setCurrentTab}
              onRefreshRepositories={loadRepositories}
            />
          )}

          {/* 6. Contribute to Good First Issues */}
          {currentTab === 'contribute' && (
            <ContributePage
              onSelectRepo={setSelectedRepo}
              onNavigateToTab={setCurrentTab}
              onRefreshRepositories={loadRepositories}
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

          {/* 7. Hidden Admin Route (ML Training Studio + IR Benchmark) */}
          {currentTab === 'admin' && (
            <AdminPage selectedRepo={selectedRepo} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
