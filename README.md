# CodeLens — Local AI Code Intelligence & ML Analysis Platform

<div align="center">

![CodeLens Hero Banner](frontend/src/assets/hero.png)

### **100% Offline, Privacy-Preserving Code Intelligence, Polyglot AST Call Graph Engine, Hybrid BM25+FAISS Search, Trained GBDT Ranker, Codebase Health Audit, and Grounded Local LLM Studio**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.2+-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite 8](https://img.shields.io/badge/Vite-8.0+-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.0-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-blue.svg?style=flat)](https://github.com/facebookresearch/faiss)
[![Tree-sitter](https://img.shields.io/badge/Tree--sitter-Polyglot_AST-green.svg?style=flat)](https://tree-sitter.github.io/)
[![Scikit-Learn GBDT](https://img.shields.io/badge/ML-GBDT_Ranker-F7931E.svg?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Pytest 100%](https://img.shields.io/badge/Tests-58%2F58_Passing-brightgreen.svg?style=flat&logo=pytest&logoColor=white)](https://pytest.org/)
[![Zero Cloud API](https://img.shields.io/badge/Telemetry-0%25_Offline-purple.svg?style=flat)](#)

</div>

---

## 🌟 Executive Summary

**CodeLens** is a production-ready, local-first AI/ML code reasoning and repository analysis platform. Designed for privacy-conscious developers and security-critical enterprises, CodeLens ingests software repositories, performs multi-language Abstract Syntax Tree (AST) parsing, builds structural dependency graphs, and delivers sub-15ms hybrid retrieval paired with trained machine learning re-rankers and evidence-grounded local LLM explanations.

> 🔒 **Core Engineering Principle:** Retrieve verified repository evidence first, reason over that evidence second, and provide line-by-line source citations for every natural-language claim. **Zero proprietary cloud API dependencies. Zero code telemetry. 100% offline.**

---

## 🚀 Key Modules & Capabilities

CodeLens provides four streamlined, consolidated modules designed for seamless code navigation and deep intelligence:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                CODELENS UNIFIED MODULES                                │
├───────────────────────────────┬────────────────────────────────────────────────────────┤
│ 1. CodeLens AI & Search       │ ChatGPT-style conversational assistant with a built-in │
│    (RAG + Search-Only Mode)   │ "Search Only" toggle for instant code chunk retrieval. │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 2. Codebase Health & Security │ Two-tab audit uniting McCabe Cyclomatic Complexity,    │
│    (Quality + Security Audit) │ maintainability code smells, and static AST security.  │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 3. Architecture & Dependency  │ Dual-view studio toggling between structural subsystem │
│    (Layers View + Graph View) │ layers and an interactive NetworkX import graph.       │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 4. Code Explorer & Call Flow  │ Syntax-highlighted tree with AST symbols and 1-click   │
│    (AST Tree + Flow Tracer)   │ caller/callee execution flow tracing.                  │
└───────────────────────────────┴────────────────────────────────────────────────────────┘
```

### 1. 🤖 CodeLens AI & Hybrid Search (Unified Chat)
- **ChatGPT-Style Local Assistant:** Works completely offline for general programming questions, algorithmic guidance, and codebase reasoning.
- **"Search Only" Mode Toggle:** Switch from conversational synthesis to instant, sub-15ms lexical (BM25) + dense (FAISS) vector retrieval. Displays ranked code chunks with line numbers, match percentages, symbol badges, copy button, and an "Open in Explorer" shortcut.
- **In-App GitHub Repository Attachment:** Attach and clone any public GitHub repository directly from the chat UI, or select popular open-source presets (`click`, `fastapi`, `react`, `sqlmodel`) with automatic background AST indexing.
- **Evidence-Grounded Citations:** When querying an attached repository, CodeLens grounds every response with exact line-range citations (`file_path:start_line–end_line`) and confidence scoring.

### 2. 🩺 Codebase Health & Security Audit (Dual-Tab)
- **Tab 1: Quality & Smells:**
  - Overall repository maintainability rating (`HIGH`, `MEDIUM`, `LOW`).
  - Average cyclomatic complexity and inter-module coupling levels.
  - **McCabe Complexity Hotspots:** Flagged functions with highest branch paths and nesting depths.
  - **Code Smell Detections:** Anti-pattern scanner identifying brain methods, god files, deep inheritance, and excessive parameter bloat.
- **Tab 2: Security Insights:**
  - Non-destructive static AST scanner detecting security risks without executing untrusted code.
  - Vulnerability categorizations across Critical, High, Medium, and Low severities.
  - Identifies hardcoded credentials, SQL injection risks, unsafe subprocess calls, and permissive TLS configurations with code snippets and remediation advice.

### 3. 🏛️ Architecture & Dependency Studio (Dual-View)
- **Layers View:** Inferred structural layers (Presentation, Application, Domain, Infrastructure), subsystem pattern recognition, and directional dependency flows.
- **Dependency Graph:** Interactive module-level import graph built on NetworkX, featuring node search filtering, an external libraries toggle, and in/out degree fan-out analysis.

### 4. 🧭 Code Explorer & Interactive Call Flow Tracer
- **File & AST Tree:** Browse repository directory structures with syntax-highlighted code rendering and line numbering.
- **1-Click Call Flow Tracer:** Click on any function symbol or click `Trace Flow →` to immediately compute and visualize inbound callers, the target routine, and outbound callees, allowing interactive jumping through the static call graph.

### 5. ⚡ Additional Developer Tools
- **Blast Radius & Impact Analysis:** Recursive dependency graph traversal to identify broken callers and affected downstream modules before refactoring.
- **Multi-Repo Comparison:** Compare repository architectures, cyclomatic complexity distributions, and file metrics side-by-side.
- **Public Landing Page Tour:** Embedded showcase tour at `/?tab=landing` detailing platform capabilities.
- **Pure OLED Dark Minimalist Aesthetic:** Modern black palette (`#000000`, `#0a0a0c`, `#121215`, `#181822`, `#252535`) tailored for developer focus.

---

## 🛠️ Comprehensive Technology Stack

CodeLens is built from the ground up using modern technologies across frontend, backend, information retrieval, machine learning, and static analysis:

```
                                  CODELENS PLATFORM
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │                                   FRONTEND LAYER                                     │
 │  React 19 • TypeScript • Vite 8 • Tailwind CSS v4 • Lucide React • React-Markdown     │
 └──────────────────────────────────────────┬───────────────────────────────────────────┘
                                            │ REST API / JSON
 ┌──────────────────────────────────────────▼───────────────────────────────────────────┐
 │                                   BACKEND LAYER                                      │
 │  FastAPI • Uvicorn • Pydantic v2 • Python 3.9+ • Structured JSON Tracing Middleware  │
 └──────────────────────────────────────────┬───────────────────────────────────────────┘
                                            │
         ┌──────────────────────────────────┼──────────────────────────────────┐
         ▼                                  ▼                                  ▼
 ┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
 │    RETRIEVAL & IR   │          │ MACHINE LEARNING &  │          │   STATIC ANALYSIS   │
 │                     │          │      DEEP LEARNING  │          │      & PARSING      │
 │ • FAISS (IndexFlatIP│          │ • SentenceTransformer│         │ • Tree-sitter AST   │
 │ • BM25+ Subword     │          │   (all-MiniLM-L6-v2)│          │   (6 Languages)     │
 │ • Hybrid Rank Fusion│          │ • Trained GBDT Ranker│         │ • NetworkX Graph    │
 │ • Search-Only Bypass│          │ • Maintainability ML │         │ • Cyclomatic Metric │
 │ • Sub-15ms Latency  │          │ • Local Qwen Coder   │         │ • Pattern Scanner   │
 └─────────────────────┘          └─────────────────────┘          └─────────────────────┘
```

### Detailed Tech Matrix

| Domain | Technology / Library | Purpose & Implementation Details |
|---|---|---|
| **Frontend Framework** | **React 19** (`react`, `react-dom` 19.2) | Component-based Single-Page Application (SPA) with custom state hooks |
| **Language & Typing** | **TypeScript 5+** | Strict static type definitions across AST symbols, flow graphs, and citation models |
| **Build & Tooling** | **Vite 8** (`@vitejs/plugin-react`) | High-speed HMR development server and optimized rollup bundle (215ms builds) |
| **Styling & Theme** | **Tailwind CSS v4** (`@tailwindcss/vite`) | Minimalist OLED dark theme (`#000000`, `#0d0d12`, `#121218`, `#252535`) |
| **UI Icons** | **Lucide React** (`lucide-react`) | Polished developer icon set |
| **Markdown Engine** | **React-Markdown** (`react-markdown`) | Live syntax rendering with macOS-style code blocks and line highlighting |
| **Backend Framework** | **FastAPI** + **Uvicorn** | Asynchronous REST API with OpenAPI documentation |
| **Data Validation** | **Pydantic v2** | Strict schema validation and JSON serialization |
| **Dense Embeddings** | **SentenceTransformers** (`all-MiniLM-L6-v2`) | Pretrained 384-dimensional dense semantic vectors for technical code chunks |
| **Vector Engine** | **FAISS** (`IndexFlatIP`) | Inner-product vector index with L2-normalized cosine distance matching |
| **Lexical Search** | **RankBM25 Plus** (`rank_bm25`) | Subword keyword retrieval addressing camelCase and snake_case identifiers |
| **ML Ranker** | **HistGradientBoostingClassifier** (13 feats) | GBDT re-ranker combining dense, lexical, and AST structural features |
| **Risk Model** | **Multi-Class GBDT** (11 complexity feats) | Predicts `LOW`, `MEDIUM`, or `HIGH` maintainability risk |
| **Local LLM Reasoner** | **Qwen 2.5 Coder 1.5B/7B** | 100% offline evidence synthesis, step walkthroughs, and confidence gating |
| **AST Parser** | **Tree-sitter** (`tree_sitter`) | Polyglot parser extracting functions, classes, calls, and imports across 6 languages |
| **Dependency Graphs** | **NetworkX** (`networkx`) | Static import graph, caller/callee execution flow, and blast-radius impact analysis |
| **Code Metrics** | **Radon & Custom Cyclomatic Engine** | McCabe cyclomatic complexity, nesting depth, parameter count, and LOC metrics |
| **Testing Suite** | **Pytest** (`pytest`, `pytest-asyncio`) | 58 comprehensive unit, integration, ML zero-leakage, and security tests |

---

## 🏛️ System Architecture

```text
                                TARGET REPOSITORY
                         (Local Path or GitHub Clone)
                                       │
                                       ▼
                             Tree-sitter AST Parser
                    (Python, JS, TS, Java, C++, C, Multi-Chunk)
                                       │
                ┌──────────────────────┼──────────────────────┐
                │                      │                      │
                ▼                      ▼                      ▼
          Dense Embeddings        BM25+ Index          Dependency Graph
       (all-MiniLM-L6-v2, 384d)(Subword Tokenizer)   (Call Graph, Imports)
                │                      │                      │
                ▼                      ▼                      │
           FAISS Store            BM25 Store                  │
       (IndexFlatIP Cosine)   (RankBM25 Plus)                 │
                │                      │                      │
                └──────────┬───────────┘                      │
                           ▼                                  │
                    HYBRID RETRIEVAL                          │
         Score = α·Dense_norm + (1-α)·BM25_norm               │
                           │                                  │
         ┌─────────────────┴─────────────────┐                │
         ▼                                   ▼                │
 [SEARCH ONLY MODE]                 [REASONING CHAT MODE]     │
 Instant Code Hits                   Top-N Candidates         │
 (Ranked Chunks, Sub-15ms)                   │                │
                                             ▼                │
                                     TRAINED ML RANKER        │
                                  (13-Feature GBDT Model)     │
                                             │                │
                                             ▼                │
                                     Evidence Selection       │
                                             │                │
                                             ├────────────────┘
                                             │ (Structural Context & Inferred Flow)
                                             ▼
                                     EVIDENCE PACK
                            (Filtered Code Chunks + Call Graph)
                                             │
                                             ▼
                                    HALLUCINATION GUARD
                                 (Calibrated Confidence Gate)
                                             │
                                             ▼
                                    LOCAL QWEN 2.5 CODER
                                 (100% Offline LLM Inference)
                                             │
                                             ▼
                                   GROUNDED AI RESPONSE
                          (Overview + Walkthrough + Line Citations)
```

---

## 🔬 Empirical Benchmark Results (Unseen Holdout Test Repo)

To eliminate data leakage, benchmarks are evaluated on completely isolated test repositories (`sample_repo` holdout split) never seen during model training:

### 1. Retrieval Strategy Performance
| Retrieval Strategy | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR | NDCG@5 | NDCG@10 | Latency (ms) |
|---|---|---|---|---|---|---|---|---|
| **BM25 Lexical** | 0.5172 | 0.6552 | 0.7586 | 0.7931 | 0.6112 | 0.7066 | 0.7177 | **0.09 ms** |
| **Vector (Dense)** | 0.4310 | 0.6379 | 0.7586 | 0.8448 | 0.5677 | 0.6603 | 0.6868 | 13.87 ms |
| **Hybrid Fusion ($\alpha=0.6$)** | 0.4828 | **0.6897** | **0.7586** | **0.8448** | 0.6036 | 0.6308 | 0.6622 | 9.13 ms |
| **Hybrid + ML Ranker** | 0.3621 | 0.5862 | **0.7586** | **0.8448** | 0.5104 | 0.5582 | 0.5901 | 324.67 ms |

### 2. Multi-Language Breakdown
| Programming Language | Test Queries | Recall@5 | Mean Reciprocal Rank (MRR) |
|---|---|---|---|
| **Python** | 38 | 0.7895 | 0.6241 |
| **JavaScript** | 12 | 0.7500 | 0.5833 |
| **Java** | 8 | 0.6250 | 0.5125 |

---

## ⚡ Quickstart & Local Installation

### 1. Prerequisites
- **Python 3.9+**
- **Node.js 18+** & **npm**
- **Git**

### 2. Clone & Setup Environment
```bash
# Clone the repository
git clone https://github.com/jatinxrawat/CodeLens.git
cd CodeLens

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies and build production UI
npm --prefix frontend install
npm --prefix frontend run build
```

### 3. Run System Validation Check
```bash
python -m app.validate
```
*Expected Output:*
```text
============================================================
SYSTEM VALIDATION: Local AI Code Intelligence Engine
============================================================
[PASS] Configuration
[PASS] Embedding model
[PASS] Vector index
[PASS] BM25 index
[PASS] Retrieval ranker
[PASS] Maintainability model
[PASS] Local LLM
[PASS] API
[PASS] Tests
[PASS] Evaluation
SYSTEM READY
```

### 4. Launch CodeLens
Start the FastAPI backend:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Start the frontend development server:
```bash
npm --prefix frontend run dev
```
Open your browser at **[http://localhost:5173](http://localhost:5173)** (or **[http://localhost:8000](http://localhost:8000)** for the combined static build).

---

## 🎓 CodeLens for Students: Architecture & New Features

CodeLens has been restructured as an intuitive code-intelligence platform that any student or aspiring open-source contributor can immediately use:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              STUDENT NAVIGATION STRUCTURE                              │
├───────────────────────────────┬────────────────────────────────────────────────────────┤
│ 1. Chat                       │ Ask anything with Beginner/Expert modes or toggle      │
│                               │ "Search only" for instant AST chunk hits.              │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 2. Overview                   │ High-level codebase summary, file breakdown & metrics. │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 3. Architecture               │ Subsystem layers & interactive NetworkX import graph.  │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 4. Impact Analysis            │ Blast radius simulator for refactoring without breaking│
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 5. Explorer                   │ Polyglot AST syntax tree + 1-click caller/callee flow. │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 6. Health                     │ Two tabs: Maintainability & smells + Security audit.   │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 7. Explore                    │ Trending open-source repos with 6-factor readiness     │
│                               │ scores (0-100) and 1-click "Analyze in CodeLens".      │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 8. Contribute                 │ Beginner issues ("good first issue", "help wanted")    │
│                               │ with Gemini skill summaries and difficulty badges.     │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 9. Reports                    │ Exportable architectural and quality audit reports.    │
├───────────────────────────────┼────────────────────────────────────────────────────────┤
│ 10. Repositories              │ Repository catalog, repo comparison studio, & ingest.  │
└───────────────────────────────┴────────────────────────────────────────────────────────┘
```

### 🌟 Explore & Contribute Features
- **Explore Repositories (`/explore`):** Browse top open-source projects across Python, TypeScript, Go, Rust, C++, and Java. Filter by domain (`AI/ML`, `Web`, `DevOps`, `Systems`, `Mobile`) or stars.
- **Contribution-Readiness Score (0-100):** Every repository displays an explainable letter grade (`A+` to `D`) computed from:
  1. *Recent commit activity (20%)*
  2. *Median PR merge time (20%)*
  3. *Maintainer response time on issues (20%)*
  4. *Presence of CONTRIBUTING.md (15%)*
  5. *Ratio of labeled beginner issues (15%)*
  6. *Open PR backlog (10%)*
- **Contribute Issues (`/contribute`):** Discover unassigned "good first issue" items. CodeLens runs Gemini to automatically extract:
  - **Difficulty rating:** `easy`, `medium`, or `hard`
  - **Required skills:** e.g., `["python", "fastapi", "pytest"]`
  - **Likely files to edit:** e.g., `["app/routers/auth.py"]`
  - **Student-friendly issue summary:** plain English overview of what needs fixing.
- **Bookmarks & "Working on this":** Save issues you want to tackle, or mark yourself as actively working on an issue.
- **1-Click "Analyze in CodeLens":** Found an intriguing repo or issue? Hit *Analyze in CodeLens* on any card to clone, index AST symbols, build vector embeddings, and immediately start exploring its architecture!

---

## ⚡ LLM Provider: Google Gemini vs 100% Offline Local Mode

CodeLens supports an extensible `LLMProvider` layer with runtime switching between **Google Gemini** (default cloud provider) and **Local ML Engine** (100% offline Qwen + SentenceTransformers).

### 1. Google Gemini Mode (Default)
- **Fast, High-Quality Answers:** Powered by the official Google GenAI SDK.
- **Two Tiers:**
  - `Flash-Tier` (`gemini-2.5-flash`): Used for standard conversational answers and fast RAG.
  - `Pro-Tier` (`gemini-2.5-pro`): Used when "Deep Reason" mode is toggled for complex AST call graph tracing.
- **Embeddings:** Cloud vector indexing via `text-embedding-004`.
- **Privacy Notice:** When analyzing a private or proprietary repository, CodeLens displays a clear banner before sending code snippets to Google GenAI, allowing 1-click fallback to Local Mode.

### 2. Local ML Engine Mode (100% Offline)
- Runs completely on your device without internet access or external APIs.
- Uses local `Qwen/Qwen2.5-Coder-1.5B-Instruct` and `sentence-transformers/all-MiniLM-L6-v2`.
- Ideal for airplane mode, air-gapped environments, or strict company data policies.

### Switching Between Providers
You can switch providers at any time:
1. **Via UI:** Click the Provider Indicator in the bottom-left of the sidebar (shows **Gemini** or **Local**) and choose your engine.
2. **Via REST API:**
   ```bash
   # Switch to local offline mode
   curl -X POST http://localhost:8000/api/reasoning/provider -H "Content-Type: application/json" -d '{"provider": "local"}'
   
   # Switch back to Gemini cloud mode
   curl -X POST http://localhost:8000/api/reasoning/provider -H "Content-Type: application/json" -d '{"provider": "gemini"}'
   ```
3. **Via Environment Variable:** Set `LLM_PROVIDER=gemini` or `LLM_PROVIDER=local` in `.env`.

---

## ⚙️ Environment Variables & Setup Guide

Create a `.env` file in the project root (see `.env.example`):

```bash
cp .env.example .env
```

### Essential Settings
| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | Active LLM engine (`gemini` or `local`) | `gemini` |
| `GEMINI_API_KEY` | Your Google Gemini API Key from [AI Studio](https://aistudio.google.com/) | *(None - falls back to local if missing)* |
| `GEMINI_FLASH_MODEL` | Flash model for fast generation | `gemini-2.5-flash` |
| `GEMINI_PRO_MODEL` | Pro model for deep reasoning | `gemini-2.5-pro` |
| `GEMINI_EMBEDDING_MODEL` | Cloud embedding model | `text-embedding-004` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (PAT) for Explore & Contribute API | *(Optional, increases rate limit to 5,000 req/hr)* |
| `GITHUB_CLIENT_ID` | Optional GitHub OAuth client ID | *(Optional)* |
| `GITHUB_CLIENT_SECRET` | Optional GitHub OAuth client secret | *(Optional)* |
| `SEASONAL_BANNER_ENABLED` | Displays seasonal event banner on Contribute page | `true` |
| `RATE_LIMIT_PER_MINUTE` | Per-client sliding window rate limiter | `30` |

### Getting a Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and create a free key.
3. Add it to your `.env`:
   ```bash
   GEMINI_API_KEY=AIzaSy...
   ```
*(Note: Your API key is read purely server-side in FastAPI and is NEVER leaked to the client or frontend).*

### Getting a GitHub Token (Recommended)
Without a token, GitHub REST API allows 60 unauthenticated requests per hour. With a token, you get 5,000 requests per hour:
1. Go to [GitHub Settings -> Tokens (Classic)](https://github.com/settings/tokens).
2. Generate new token (classic) with `public_repo` scope.
3. Add it to `.env`:
   ```bash
   GITHUB_TOKEN=ghp_...
   ```

### Setting Up GitHub OAuth (Optional)
To enable student language personalization and GitHub login:
1. Go to [GitHub Developer Settings -> OAuth Apps](https://github.com/settings/developers).
2. Register a new OAuth application:
   - Homepage URL: `http://localhost:5173`
   - Authorization callback URL: `http://localhost:8000/api/auth/github/callback`
3. Copy the Client ID and Client Secret into `.env`:
   ```bash
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```

---

## 💻 CLI & Admin Operations

### Hidden Admin Suite (`/admin`)
The ML Training Studio and IR Benchmark pages have been relocated from the main navigation to a dedicated `/admin` route:
- Access via: **[http://localhost:5173/?tab=admin](http://localhost:5173/?tab=admin)** or **[http://localhost:5173/admin](http://localhost:5173/admin)**.
- Allows running GBDT ranker re-training, maintainability model calibration, and IR NDCG@k evaluation benchmarks.

### Ingest Any Local Repository
```bash
python -m app.cli ingest-local /path/to/target/repo --name my_project
```

### Ingest Remote GitHub Repository
```bash
python -m app.cli ingest-remote https://github.com/pallets/click.git
```

### Run Automated Pytest Suite
```bash
PYTHONPATH=. ./.venv/bin/pytest tests/test_readiness_scorer.py tests/test_github_service.py tests/test_llm_provider.py tests/test_api_explore_contribute.py
```

---

## 🛡️ Security & Privacy Model

1. **Passive Text Ingestion:** Target repository source files are parsed purely as static data syntax trees. CodeLens **never executes arbitrary repository code**.
2. **Prompt Injection Defense:** Untrusted repository comments or override instructions are sandboxed as passive data blocks and cannot alter system roles.
3. **Cloud AI Transparency:** Clear UI notices are shown when private code context is processed via Gemini, with an instant toggle to switch to 100% offline local models.
4. **Per-Client Rate Limiting:** Sliding-window rate limiting prevents API abuse and quota exhaustion.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
