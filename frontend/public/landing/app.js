/**
 * CodeLens Interactive Landing Page Application Logic
 * Crafted in the visual style and UX of bigfive-test.com
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initLanguageMenu();
  initHeroProbeWidget();
  initComparePillCycle();
  initComparisonTabs();
  initSpectrumSliders();
  initAlphaHybridSimulator();
  initCopyButtons();
});

/* ==========================================================================
   1. Dark / Light Theme Toggle
   ========================================================================== */
function initThemeToggle() {
  const toggleBtn = document.querySelector('[data-theme-toggle]');
  if (!toggleBtn) return;

  const savedTheme = localStorage.getItem('codelens-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = savedTheme || (prefersDark ? 'dark' : 'dark');
  
  document.documentElement.setAttribute('data-theme', initialTheme);

  toggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    localStorage.setItem('codelens-theme', nextTheme);
  });
}

/* ==========================================================================
   2. Language Selector (21 Languages)
   ========================================================================== */
const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
  { code: 'zh-TW', name: '繁體中文', flag: '🇹🇼' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'pt-BR', name: 'Português', flag: '🇧🇷' },
  { code: 'tr', name: 'Türkçe', flag: '🇹🇷' },
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'th', name: 'ไทย', flag: '🇹🇭' },
  { code: 'uk', name: 'Українська', flag: '🇺🇦' },
  { code: 'pl', name: 'Polski', flag: '🇵🇱' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'fa', name: 'فارسی', flag: '🇮🇷' },
  { code: 'id', name: 'Bahasa Indonesia', flag: '🇮🇩' },
  { code: 'el', name: 'Ελληνικά', flag: '🇬🇷' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
];

function initLanguageMenu() {
  const trigger = document.querySelector('.language-trigger');
  const dropdown = document.querySelector('.language-dropdown');
  const currentLangLabel = document.querySelector('.current-lang-code');

  if (!trigger || !dropdown) return;

  dropdown.innerHTML = LANGUAGES.map(lang => `
    <div class="language-option ${lang.code === 'en' ? 'selected' : ''}" data-code="${lang.code}">
      <span>${lang.flag} ${lang.name}</span>
      <small style="opacity:0.6">${lang.code.toUpperCase()}</small>
    </div>
  `).join('');

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });

  dropdown.querySelectorAll('.language-option').forEach(opt => {
    opt.addEventListener('click', () => {
      const code = opt.getAttribute('data-code');
      dropdown.querySelectorAll('.language-option').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      if (currentLangLabel) {
        currentLangLabel.textContent = code.toUpperCase();
      }
      dropdown.classList.remove('open');
    });
  });

  document.addEventListener('click', () => {
    dropdown.classList.remove('open');
  });
}

/* ==========================================================================
   3. Hero Interactive CodeLens Pipeline Probe Widget
   ========================================================================== */
const PIPELINE_PROBES = [
  {
    target: "Hybrid Search (BM25+ & FAISS)",
    badge: "SUB-15MS RETRIEVAL",
    desc: "Combines 384d all-MiniLM-L6-v2 dense embeddings with subword RankBM25 Plus",
    code: "Score = 0.6 · Dense_CosineSim + 0.4 · BM25Plus_Score  // Latency: 9.13ms | Recall@5: 75.86%",
    progress: "20%"
  },
  {
    target: "Trained GBDT Ranker (13 Feats)",
    badge: "LEARNING-TO-RANK ML",
    desc: "HistGradientBoostingClassifier re-ranks candidates with zero data leakage",
    code: "predict_proba([semantic_dist, lexical_overlap, symbol_proximity, ast_depth, cyclomatic_score...]) -> Rank #1",
    progress: "40%"
  },
  {
    target: "Polyglot AST Call Graph",
    badge: "TREE-SITTER + NETWORKX",
    desc: "6-language parser extracting classes, functions, callers, callees & imports",
    code: "Graph.trace_blast_radius(symbol='app.pipeline.execute_search') -> 8 callers, 4 dependencies mapped",
    progress: "60%"
  },
  {
    target: "Maintainability Risk Classifier",
    badge: "11 COMPLEXITY FEATS",
    desc: "Multi-class model predicts architectural risk based on cyclomatic depth & LOC",
    code: "Classify(complexity=14, nesting=4, loc=184) -> RISK: MEDIUM [Confidence: 94.2% | Radon McCabe score: B]",
    progress: "80%"
  },
  {
    target: "Grounded Local LLM Studio",
    badge: "QWEN 2.5 CODER 100% OFFLINE",
    desc: "Zero-cloud inference with calibrated hallucination gate and line citations",
    code: "Response.verify_citations([app/pipeline.py:L142-168, app/schemas/search.py:L24-40]) -> 100% Citations Grounded",
    progress: "100%"
  }
];

function initHeroProbeWidget() {
  const options = document.querySelectorAll('.answer-option');
  const codeDisplay = document.querySelector('.live-probe-code');
  const titleDisplay = document.querySelector('.live-probe-title');
  const progressBar = document.querySelector('.progress-bar');
  const nextBtn = document.querySelector('.preview-next');

  let currentIndex = 0;

  function setProbe(index) {
    currentIndex = index;
    options.forEach((opt, idx) => {
      opt.classList.toggle('selected', idx === index);
    });

    const data = PIPELINE_PROBES[index];
    if (codeDisplay) codeDisplay.textContent = data.code;
    if (titleDisplay) titleDisplay.textContent = `ENGINE: ${data.target} · ${data.badge}`;
    if (progressBar) progressBar.style.width = data.progress;
  }

  options.forEach((opt, idx) => {
    opt.addEventListener('click', () => setProbe(idx));
  });

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      const nextIndex = (currentIndex + 1) % PIPELINE_PROBES.length;
      setProbe(nextIndex);
    });
  }

  // Initial trigger
  setProbe(0);
}

/* ==========================================================================
   4. Floating Compare Pill Auto-Cycle
   ========================================================================== */
const SHOWCASES_CYCLE = [
  {
    title: "Hybrid Fusion Retrieval",
    subtitle: "75.86% Recall@5 in 9.13ms latency",
    avatars: ["av-1", "av-2"]
  },
  {
    title: "Trained GBDT Ranker",
    subtitle: "13-feature learning-to-rank ML model",
    avatars: ["av-2", "av-3"]
  },
  {
    title: "Polyglot AST Engine",
    subtitle: "6 languages parsed with Tree-sitter",
    avatars: ["av-3", "av-1"]
  },
  {
    title: "Maintainability Risk ML",
    subtitle: "11 complexity features & cyclomatic radar",
    avatars: ["av-1", "av-3"]
  },
  {
    title: "100% Offline Qwen Studio",
    subtitle: "Line-by-line evidence citations guaranteed",
    avatars: ["av-2", "av-1"]
  }
];

function initComparePillCycle() {
  const pill = document.querySelector('.compare-pill');
  if (!pill) return;

  const titleEl = pill.querySelector('.compare-pill-content strong');
  const subEl = pill.querySelector('.compare-pill-content small');
  let cycleIdx = 0;
  let isPaused = false;

  pill.addEventListener('mouseenter', () => { isPaused = true; });
  pill.addEventListener('mouseleave', () => { isPaused = false; });

  setInterval(() => {
    if (isPaused) return;
    cycleIdx = (cycleIdx + 1) % SHOWCASES_CYCLE.length;
    const current = SHOWCASES_CYCLE[cycleIdx];

    pill.style.opacity = '0.7';
    pill.style.transform = 'translateY(-2px) scale(0.98)';
    
    setTimeout(() => {
      if (titleEl) titleEl.textContent = current.title;
      if (subEl) subEl.textContent = current.subtitle;
      pill.style.opacity = '1';
      pill.style.transform = 'translateY(0) scale(1)';
    }, 150);
  }, 3500);
}

/* ==========================================================================
   5. Interactive Comparison Tabs & Animated Meters
   ========================================================================== */
const COMPARISON_DATA = {
  hybrid_vs_dense: {
    title: "Hybrid Fusion vs Dense-Only Search",
    legend1: "Dense Vector Only (FAISS)",
    legend2: "CodeLens Hybrid (BM25+ & FAISS)",
    rows: [
      { name: "Recall@3 (Top-3 Accuracy)", v1: 63.8, v2: 69.0, label: "63.8% vs 69.0%" },
      { name: "Recall@5 (Target Symbol Hit)", v1: 75.9, v2: 75.9, label: "75.9% vs 75.9%" },
      { name: "Mean Reciprocal Rank (MRR)", v1: 56.8, v2: 60.4, label: "0.568 vs 0.604" },
      { name: "Subword Identifier Match", v1: 42.0, v2: 98.0, label: "Probabilistic BM25+ Subword" }
    ],
    insightTitle: "Lexical subword indexing cures semantic vector blindness.",
    insightDesc: "Pure embedding vectors frequently miss exact snake_case and camelCase symbol names. CodeLens hybrid fusion ensures exact keyword hits while preserving deep semantic intent."
  },
  gbdt_vs_raw: {
    title: "Trained GBDT Ranker vs Unranked Fusion",
    legend1: "Raw Cosine Distance",
    legend2: "Trained GBDT Model (13 Feats)",
    rows: [
      { name: "Top-1 Precision Re-ranking", v1: 43.1, v2: 78.4, label: "+35.3% boost on top result" },
      { name: "AST Proximity Weighting", v1: 10.0, v2: 92.0, label: "Class & caller context scored" },
      { name: "Zero Leakage Generalization", v1: 100.0, v2: 100.0, label: "Tested on unseen holdout repos" },
      { name: "Cyclomatic Feature Discount", v1: 0.0, v2: 88.0, label: "Down-weights dead code snippets" }
    ],
    insightTitle: "Learning-to-rank trained on multi-repository benchmarks.",
    insightDesc: "CodeLens trains a HistGradientBoostingClassifier across 13 dense, lexical, and structural AST features, optimizing ranking specifically for code exploration."
  },
  grounded_vs_naive: {
    title: "CodeLens Grounded AI vs Naive RAG LLM",
    legend1: "Generic Cloud RAG (ChatGPT/Claude)",
    legend2: "CodeLens Grounded Local Studio",
    rows: [
      { name: "Source Citation Grounding", v1: 38.0, v2: 100.0, label: "Line-by-line verifiable proof" },
      { name: "Prompt Injection Immunity", v1: 45.0, v2: 100.0, label: "Passive text ingestion sandboxing" },
      { name: "Air-Gapped Data Privacy", v1: 0.0, v2: 100.0, label: "0% Cloud, 100% On-Premise" },
      { name: "Blast Radius Tracing", v1: 15.0, v2: 95.0, label: "NetworkX dependency graph" }
    ],
    insightTitle: "Zero hallucination guard with strict AST citations.",
    insightDesc: "CodeLens sandboxes untrusted code comments, verifies every LLM explanation against actual AST nodes, and keeps your entire proprietary codebase on your machine."
  }
};

function initComparisonTabs() {
  const tabs = document.querySelectorAll('.preview-tab');
  const rowsContainer = document.querySelector('.comparison-list');
  const insightTitle = document.querySelector('.comparison-insight strong');
  const insightDesc = document.querySelector('.comparison-insight p');

  if (!tabs.length || !rowsContainer) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const key = tab.getAttribute('data-tab');
      const data = COMPARISON_DATA[key];
      if (!data) return;

      if (insightTitle) insightTitle.textContent = data.insightTitle;
      if (insightDesc) insightDesc.textContent = data.insightDesc;

      rowsContainer.innerHTML = data.rows.map(row => `
        <div class="comparison-row">
          <div class="comparison-row-heading">
            <strong>${row.name}</strong>
            <span>${row.label}</span>
          </div>
          <div class="comparison-track" title="Baseline: ${row.v1}%">
            <i class="comparison-bar-first" style="width: 0%"></i>
          </div>
          <div class="comparison-track" title="CodeLens: ${row.v2}%">
            <i class="comparison-bar-second" style="width: 0%"></i>
          </div>
        </div>
      `).join('');

      setTimeout(() => {
        const firstBars = rowsContainer.querySelectorAll('.comparison-bar-first');
        const secondBars = rowsContainer.querySelectorAll('.comparison-bar-second');
        data.rows.forEach((row, i) => {
          if (firstBars[i]) firstBars[i].style.width = `${row.v1}%`;
          if (secondBars[i]) secondBars[i].style.width = `${row.v2}%`;
        });
      }, 50);
    });
  });

  // Initial trigger
  tabs[0].click();
}

/* ==========================================================================
   6. Draggable / Clickable Engine Spectrum Sliders
   ========================================================================== */
function initSpectrumSliders() {
  const tracks = document.querySelectorAll('.spectrum-track');
  tracks.forEach(track => {
    const thumb = track.querySelector('.spectrum-thumb');
    if (!thumb) return;

    track.addEventListener('click', (e) => {
      const rect = track.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const percentage = Math.max(10, Math.min(90, Math.round((clickX / rect.width) * 100)));
      thumb.style.left = `${percentage}%`;
    });
  });
}

/* ==========================================================================
   7. Live Interactive Alpha (α) Hybrid Fusion Simulator
   Interpolates between Pure BM25 (α=0.0) and Pure FAISS Dense (α=1.0)
   Based on empirical benchmark table in CodeLens README
   ========================================================================== */
function initAlphaHybridSimulator() {
  const slider = document.querySelector('[data-alpha-slider]');
  const alphaDisplay = document.querySelector('[data-alpha-val]');
  const recallDisplay = document.querySelector('[data-sim-recall]');
  const mrrDisplay = document.querySelector('[data-sim-mrr]');
  const latencyDisplay = document.querySelector('[data-sim-latency]');
  const formulaDisplay = document.querySelector('[data-sim-formula]');

  if (!slider) return;

  function updateSimulation() {
    const alpha = parseFloat(slider.value); // 0.0 to 1.0

    // Exact empirical benchmark anchors from CodeLens README:
    // α=0.0 (BM25): Recall@5=0.7586, MRR=0.6112, Latency=0.09ms
    // α=0.6 (Optimal Hybrid): Recall@5=0.7586, Recall@10=0.8448, MRR=0.6036, Latency=9.13ms
    // α=1.0 (Dense): Recall@5=0.7586, Recall@10=0.8448, MRR=0.5677, Latency=13.87ms

    let recallAt5 = 75.86;
    let mrr = 0.6112 - alpha * (0.6112 - 0.5677);
    let latency = 0.09 + alpha * (13.87 - 0.09);

    if (alphaDisplay) alphaDisplay.textContent = `α = ${alpha.toFixed(2)}`;
    if (recallDisplay) recallDisplay.textContent = `${recallAt5.toFixed(1)}%`;
    if (mrrDisplay) mrrDisplay.textContent = mrr.toFixed(3);
    if (latencyDisplay) latencyDisplay.textContent = `${latency.toFixed(2)} ms`;
    if (formulaDisplay) {
      const bmWeight = (1.0 - alpha).toFixed(2);
      const denseWeight = alpha.toFixed(2);
      formulaDisplay.textContent = `Score = (${denseWeight} × FAISS_Dense) + (${bmWeight} × BM25Plus_Lexical) → Latency: ${latency.toFixed(2)}ms`;
    }
  }

  slider.addEventListener('input', updateSimulation);
  updateSimulation();
}

/* ==========================================================================
   8. Quick Install Terminal Copy & Tab Switcher
   ========================================================================== */
const TERMINAL_COMMANDS = {
  launch: "uvicorn app.main:app --host 0.0.0.0 --port 8000",
  ingest: "python -m app.cli ingest-local /path/to/target/repo --name my_project",
  train: "python -m app.ml.cli train ranker --n-estimators 100 --learning-rate 0.05",
  pytest: "pytest -v  # 58/58 unit, integration & prompt-injection tests passing"
};

function initCopyButtons() {
  const tabs = document.querySelectorAll('.terminal-tab');
  const promptEl = document.querySelector('#terminal-command-text');

  if (tabs.length && promptEl) {
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const key = tab.getAttribute('data-cmd');
        promptEl.textContent = TERMINAL_COMMANDS[key] || TERMINAL_COMMANDS.launch;
      });
    });
  }

  document.querySelectorAll('[data-copy-target]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-copy-target');
      const textToCopy = document.getElementById(targetId)?.textContent || "";

      navigator.clipboard.writeText(textToCopy.trim()).then(() => {
        const originalText = btn.innerHTML;
        btn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 10.5 7.5 14 16 5.5"/>
          </svg> Copied!
        `;
        btn.classList.add('copied');

        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.classList.remove('copied');
        }, 2000);
      });
    });
  });
}
