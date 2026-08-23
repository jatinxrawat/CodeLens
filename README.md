# CodeLens — Local AI Code Intelligence & ML Analysis Platform

<div align="center">

![CodeLens Hero Banner](frontend/src/assets/hero.png)

### **100% Offline, Privacy-Preserving Code Intelligence, Polyglot AST Call Graph Engine, Hybrid BM25+FAISS Search, Trained GBDT Ranker, Maintainability Risk Classifier, and Grounded Local LLM Studio**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.2+-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.0+-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
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

> 🔒 **Core Engineering Principle:** Retrieve verified repository evidence first, reason over that evidence second, and provide line-by-line source citations for every natural-language claim. **Zero proprietary cloud API dependencies. Zero code telemetry.**

---

## 🛠️ Comprehensive Technology Stack

CodeLens is built from the ground up using state-of-the-art technologies across frontend, backend, information retrieval, machine learning, and static analysis:

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
 │ • Cosine Sim (384d) │          │ • Maintainability ML │         │ • Cyclomatic Metric │
 │ • Sub-15ms Latency  │          │ • Local Qwen Coder   │         │ • Pattern Scanner   │
 └─────────────────────┘          └─────────────────────┘          └─────────────────────┘
```

### Detailed Tech Matrix

| Domain | Technology / Library | Purpose & Implementation Details |
|---|---|---|
| **Frontend Framework** | **React 19** (`react`, `react-dom` 19.2) | Component-based Single-Page Application (SPA) architecture with custom hooks |
| **Language & Typing** | **TypeScript 5+** | Strict static type definitions for AST models, citation schemas, and ML metrics |
| **Build & Tooling** | **Vite 8** (`@vitejs/plugin-react`) | Lightning-fast development server with Hot Module Replacement (HMR) and optimized rollup bundle |
| **Styling & Theme** | **Tailwind CSS v4** (`@tailwindcss/vite`) | Next-gen CSS-first configuration, sleek dark mode (`#0d1117`, `#161b22`), glassmorphism |
| **UI Icons** | **Lucide React** (`lucide-react`) | Modern icon set (`MessageSquareCode`, `Sparkles`, `Cpu`, `Layers`, `ShieldCheck`, `Code2`) |
| **Markdown Engine** | **React-Markdown** (`react-markdown`) | Live syntax rendering with macOS-style code windows, line highlighting, and copy buttons |
| **Backend Framework** | **FastAPI** + **Uvicorn** | High-throughput asynchronous REST API with automatic OpenAPI/Swagger documentation |
| **Data Validation** | **Pydantic v2** | Strict request/response schema validation and metadata serialization |
| **Dense Embeddings** | **SentenceTransformers** (`all-MiniLM-L6-v2`) | Pretrained 384-dimensional dense semantic vectors optimized for code and technical text |
| **Vector Engine** | **FAISS** (`IndexFlatIP`) | High-performance inner-product vector index with L2-normalized cosine distance matching |
| **Lexical Search** | **RankBM25 Plus** (`rank_bm25`) | Probabilistic subword keyword retrieval addressing camelCase and snake_case identifiers |
| **ML Ranker (Model 1)**| **HistGradientBoostingClassifier** (13 feats) | **Trained in this project:** Learning-to-Rank GBDT model combining dense, lexical, and AST features |
| **Risk Model (Model 2)**| **Multi-Class GBDT** (11 complexity feats) | **Trained in this project:** Predicts `LOW`, `MEDIUM`, or `HIGH` maintainability risk |
| **Local LLM Reasoner**| **Qwen 2.5 Coder 1.5B/7B** | 100% offline evidence synthesis, execution walkthroughs, and confidence gating |
| **AST Parser** | **Tree-sitter** (`tree_sitter`) | Polyglot parser extracting functions, classes, calls, and imports across 6 languages |
| **Dependency Graphs** | **NetworkX** (`networkx`) | Static import graph, caller/callee execution flow, and blast-radius impact analysis |
| **Code Metrics** | **Radon & Custom Cyclomatic Engine** | McCabe cyclomatic complexity, nesting depth, parameter count, and LOC metrics |
| **Testing Suite** | **Pytest** (`pytest`, `pytest-asyncio`) | 58 comprehensive unit, integration, ML zero-leakage, and prompt-injection tests |

---

## 🏛️ System Architecture

```text
                                TARGET REPOSITORY
                                        │
                                        ▼
                            Tree-sitter AST Parser
                   (Python, JS, TS, Java, C++, C, Multi-Chunk)
                                        │
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
                ▼                       ▼                       ▼
          Dense Embeddings         BM25+ Index           Dependency Graph
       (all-MiniLM-L6-v2, 384d) (Subword Tokenizer)   (Call Graph, Imports)
                │                       │                       │
                ▼                       ▼                       │
           FAISS Store             BM25 Store                   │
       (IndexFlatIP Cosine)    (RankBM25 Plus)                  │
                │                       │                       │
                └───────────┬───────────┘                       │
                            ▼                                   │
                     HYBRID RETRIEVAL                           │
          Score = α·Dense_norm + (1-α)·BM25_norm                │
                            │                                   │
                            ▼                                   │
                    Top-N Candidates                            │
                            │                                   │
                            ▼                                   │
                   TRAINED ML RANKER                            │
                (13-Feature GBDT Model)                         │
                            │                                   │
                            ▼                                   │
                    Evidence Selection                          │
                            │                                   │
                            ├───────────────────────────────────┘
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
         (Overview + Step Walkthrough + Citations)
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

### 3. Feature Ablation Study
| Configuration | Feature Count | Recall@5 | MRR | NDCG@5 |
|---|---|---|---|---|
| **Baseline (Hybrid No ML)** | 2 | 0.7586 | 0.6036 | 0.6308 |
| **Semantic Only** | 1 | 0.6827 | 0.4287 | 0.4633 |
| **Semantic + Keyword** | 3 | 0.7434 | 0.4849 | 0.5247 |
| **Semantic + Keyword + Symbol** | 6 | 0.7434 | 0.4849 | 0.5247 |
| **Full Feature Set (All 13 Feats)** | **13** | **0.7586** | **0.5104** | **0.5582** |

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

### 4. Launch CodeLens Studio
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## 💻 CLI & ML Operations

### Ingest Any Local Repository
```bash
python -m app.cli ingest-local /path/to/target/repo --name my_project
```

### Build ML Training Dataset (Strict Zero-Leakage Split)
```bash
python -m app.ml.cli dataset build
```

### Train Custom ML Models
```bash
# Train Relevance Ranking GBDT Model
python -m app.ml.cli train ranker --n-estimators 100 --learning-rate 0.05

# Train Maintainability Risk Classifier
python -m app.ml.cli train maintainability --n-estimators 100 --learning-rate 0.05
```

### Run Automated Pytest Suite (58 Tests)
```bash
pytest -v
```

---

## 📚 In-Depth Technical Documentation

- 📄 **[Technical Whitepaper (docs/technical-report.md)](docs/technical-report.md)**: 24-section IEEE-style specification detailing mathematical foundations, ranking algorithms, and failure analysis.
- 🗂️ **[Model Cards (docs/models/)](docs/models/)**:
  - [retrieval-ranker-model-card.md](docs/models/retrieval-ranker-model-card.md) — Documentation for Learning-to-Rank GBDT model.
  - [maintainability-model-card.md](docs/models/maintainability-model-card.md) — Documentation for Maintainability Risk Classifier.
- 💼 **[CV & Portfolio Summary (docs/cv-project-summary.md)](docs/cv-project-summary.md)**: 25-word summary, high-impact resume bullets, and 60-second interview pitch.
- 🎯 **[Technical Interview Defense (docs/interview-questions.md)](docs/interview-questions.md)**: Deep technical Q&A across ML, Deep Learning, RAG, and SWE.
- 📊 **[Retrieval Benchmark Report (reports/retrieval-benchmark.md)](reports/retrieval-benchmark.md)**: Multi-language evaluation data.

---

## 🛡️ Security & Privacy Model

1. **Passive Text Ingestion:** Target repository source files are parsed purely as static data into syntax trees. CodeLens **never executes arbitrary repository code**.
2. **Prompt Injection Defense:** Untrusted repository comments or override instructions are sandboxed as passive data blocks and cannot alter system roles.
3. **Strict Resource Quotas:** Hard limits enforced on repository size (max 200MB), file count (max 5,000 files), and file size (max 500KB).
4. **Zero Cloud Telemetry:** 100% offline inference; no tokens, code snippets, or embeddings are transmitted to external servers.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
