# CodeLens — Local AI Code Intelligence & ML Analysis Platform

> **Production-Grade, 100% Offline Code Intelligence, AST Dependency Graph, Hybrid BM25+FAISS Retrieval Engine, Trained GBDT Ranker, Maintainability Risk Classifier, and Grounded Local LLM Reasoning Dashboard**  
> *Zero External API Calls • Zero Cloud Telemetry • Multi-Language AST Parsing • Learning-to-Rank • Sub-15ms Hybrid Retrieval*

---

## 1. Project Overview

**CodeLens** is a local-first AI/ML code intelligence platform designed to help developers understand, search, analyze, and evaluate software repositories.

Instead of behaving like a conventional code search tool that only returns files and snippets, CodeLens combines:

- Multi-Language Source-Code Parsing (Tree-sitter)
- Abstract Syntax Tree (AST) & Code Chunk Analysis
- Transformer-based Dense Code Embeddings (`all-MiniLM-L6-v2`)
- Semantic Vector Search (FAISS `IndexFlatIP`)
- BM25+ Subword Keyword Retrieval
- Weighted Hybrid Retrieval Fusion
- Dependency Graph & AST Flow Tracer
- Machine-Learning-Based Relevance Ranking (Trained GBDT Model)
- Machine-Learning-Based Maintainability-Risk Prediction (Multi-Class GBDT)
- Retrieval-Augmented Generation (RAG)
- Locally Deployed Open-Source LLM (`Qwen/Qwen2.5-Coder-1.5B-Instruct`)
- Evidence-Grounded Natural-Language Explanations
- Static Code-Quality & McCabe Complexity Metrics
- Pattern-Based Security Vulnerability Scanners
- Evaluation, Benchmarking, Ablation Studies, and Failure Analysis

The central design principle is:

> **Retrieve evidence first, reason over that evidence second, and show the user where the evidence came from.**

CodeLens is intentionally designed so that the core AI pipeline does not require proprietary hosted AI APIs.

---

## 2. Problem Statement

Modern software repositories contain thousands of files, classes, functions, dependencies, and complex call graphs. A developer navigating an unfamiliar repository struggles with questions such as:
- *How does authentication work?*
- *Where is user registration implemented?*
- *What happens when a login request is received?*
- *Which files depend on this module?*
- *What code may be difficult to maintain?*

Traditional keyword search fails when the user asks *"Where is authentication implemented?"* while the codebase uses domain tokens such as `login`, `JWT`, `token`, `authorize`, or `verify_credentials`. 

CodeLens bridges this vocabulary and conceptual gap through hybrid search, learning-to-rank, static call graphs, and evidence-grounded local reasoning.

---

## 3. System Architecture

```text
                         ┌─────────────────────┐
                         │        USER         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   React Frontend    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     FastAPI API     │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │  Query Understanding│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Candidate Retrieval │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
           ┌─────────────┐                     ┌──────────────┐
           │    BM25+    │                     │  Embeddings  │
           │   Search    │                     │ + FAISS      │
           └──────┬──────┘                     └──────┬───────┘
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
                           Hybrid Retrieval
                   (Score = α·Dense + (1-α)·BM25)
                                    │
                                    ▼
                            Candidate Results
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  ML Relevance       │
                         │     Ranker          │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
          Dependency Graph                    Code Metrics
                  │                                   │
                  ▼                                   ▼
        Structural Evidence              Maintainability ML
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
                              Evidence Pack
                                    │
                                    ▼
                          Local Open-Source LLM
                        (Qwen 2.5 Coder 1.5B/7B)
                                    │
                                    ▼
                         Grounded AI Response
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
              Summary                              Sources
         (Flow & Reasoning)                  (Line-by-Line)
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
                              Developer UI
```

---

## 4. End-to-End Workflow

When a developer asks a question, CodeLens follows this process:

```text
Question
   ↓
Intent Classification (Architecture, Flow, Symbol, Security, QA)
   ↓
BM25+ Lexical Retrieval + Dense FAISS Vector Search
   ↓
Hybrid Candidate Set
   ↓
TRAINED ML RELEVANCE RANKER (13 Features)
   ↓
Dependency Graph / AST Call Flow Enrichment
   ↓
Evidence Selection & Hallucination Guard
   ↓
Evidence Pack Construction
   ↓
Local Open-Source LLM (Qwen 2.5 Coder)
   ↓
Grounded Structured Answer
   ↓
Summary + Inferred Flow + Exact Line-Level Citations
```

---

## 5. Measured Empirical Benchmark Results (Test Repository Holdout)

All metrics are measured on completely unseen multi-language test repositories (`sample_repo` holdout split with zero data leakage):

### 5.1 Retrieval Strategy Benchmarks
| Retrieval Strategy | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR | NDCG@5 | NDCG@10 | Latency (ms) |
|---|---|---|---|---|---|---|---|---|
| **BM25 Lexical** | 0.5172 | 0.6552 | 0.7586 | 0.7931 | 0.6112 | 0.7066 | 0.7177 | **0.09 ms** |
| **Vector (Dense)** | 0.4310 | 0.6379 | 0.7586 | 0.8448 | 0.5677 | 0.6603 | 0.6868 | 13.87 ms |
| **Hybrid Fusion ($\alpha=0.6$)** | 0.4828 | **0.6897** | **0.7586** | **0.8448** | 0.6036 | 0.6308 | 0.6622 | 9.13 ms |
| **Hybrid + ML Ranker** | 0.3621 | 0.5862 | **0.7586** | **0.8448** | 0.5104 | 0.5582 | 0.5901 | 324.67 ms |

### 5.2 Performance by Programming Language (Holdout Test Split)
| Language | Test Queries | Recall@5 | Mean Reciprocal Rank (MRR) |
|---|---|---|---|
| **Python** | 38 | 0.7895 | 0.6241 |
| **JavaScript** | 12 | 0.7500 | 0.5833 |
| **Java** | 8 | 0.6250 | 0.5125 |

### 5.3 Feature Ablation Study
| Configuration | Feature Count | Recall@5 | MRR | NDCG@5 |
|---|---|---|---|---|
| **Baseline (Hybrid No ML)** | 2 | 0.7586 | 0.6036 | 0.6308 |
| **Semantic Only** | 1 | 0.6827 | 0.4287 | 0.4633 |
| **Semantic + Keyword** | 3 | 0.7434 | 0.4849 | 0.5247 |
| **Semantic + Keyword + Symbol** | 6 | 0.7434 | 0.4849 | 0.5247 |
| **Full Feature Set (All 13 Feats)** | **13** | **0.7586** | **0.5104** | **0.5582** |

---

## 6. What Is ML vs What Is Not?

| Component | Category | Purpose |
|---|---|---|
| **Tree-sitter Parsing** | Software / Algorithmic | Polyglot concrete AST extraction |
| **BM25+ Subword Index** | Information Retrieval | Exact lexical and subword matching |
| **Transformer Embeddings** | Deep Learning / NLP | 384-dim dense semantic code vectors |
| **FAISS Store** | Vector Search Infrastructure | Efficient inner product cosine search |
| **Dependency Graph** | Graph Algorithms (NetworkX) | Static import and call graph paths |
| **Relevance Ranker** | **Machine Learning (Trained)** | 13-feature Learning-to-Rank GBDT model |
| **Maintainability Model** | **Machine Learning (Trained)** | Multi-class static complexity risk classifier |
| **Local Qwen LLM** | Generative AI / LLM | Evidence synthesis and natural language reasoning |
| **RAG Pipeline** | AI System Architecture | Evidence grounding and hallucination guard |

---

## 7. Quickstart & Installation

### 1. Prerequisites
- Python 3.9+
- Node.js 18+ and npm
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/codelens.git
cd codelens

# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Build the React dashboard
npm --prefix frontend install
npm --prefix frontend run build
```

### 3. Start Application
```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 8. CLI Commands & ML Training

### Ingest a Repository
```bash
python -m app.cli ingest-local /path/to/your/repo --name my_project
```

### Build ML Dataset (Zero-Leakage Repository Split)
```bash
python -m app.ml.cli dataset build
```

### Train Relevance Ranker & Maintainability Models
```bash
# Train Learning-to-Rank GBDT model
python -m app.ml.cli train ranker --n-estimators 100 --learning-rate 0.05

# Train Maintainability Risk Classifier
python -m app.ml.cli train maintainability --n-estimators 100 --learning-rate 0.05
```

### Run Benchmark & Ablation Evaluations
```bash
python -m app.ml.cli compare
python -m app.ml.cli ablation
```

### Production Validation Command
```bash
python -m app.validate
```
Outputs complete health report across all 10 system checks:
```
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

---

## 9. Running the Automated Test Suite

Execute the complete 58-test automated verification suite:
```bash
source .venv/bin/activate
pytest -v
```
All unit, integration, ML, API, hallucination guard, and prompt-injection defense tests run locally with 100% pass rate.

---

## 10. Documentation & Portfolio Assets

- **[Technical Report](docs/technical-report.md)**: Comprehensive 24-section whitepaper detailing mathematical derivations, retrieval theory, ablation findings, and failure analysis.
- **[Model Cards](docs/models/)**:
  - [retrieval-ranker-model-card.md](docs/models/retrieval-ranker-model-card.md)
  - [maintainability-model-card.md](docs/models/maintainability-model-card.md)
- **[CV & Project Summary](docs/cv-project-summary.md)**: 25-word summary, high-impact resume bullets, and 60-second interview pitch.
- **[Interview Preparation](docs/interview-questions.md)**: In-depth technical defense across ML, Deep Learning, RAG, and Systems Engineering.
- **[Retrieval Benchmark Report](reports/retrieval-benchmark.md)**: Detailed empirical retrieval breakdown across programming languages.
