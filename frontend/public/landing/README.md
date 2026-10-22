# CodeLens Landing Page (bigfive-test.com Aesthetic)

A landing page for **[CodeLens — Local AI Code Intelligence & ML Analysis Platform](https://github.com/jatinxrawat/CodeLens)**, designed and engineered in the visual style, typography, and interactive UX of **[bigfive-test.com](https://bigfive-test.com/)**.

---

## 🌟 Key Features & Structure

| Section | Description |
|---|---|
| **Sticky Glass Header** | Frosted glass navigation with CodeLens mark, count badges (`Engines 5`, `Benchmarks 4`), 21-language selector dropdown, dark/light theme toggle, and `Launch Studio` CTA button with `FREE` pill badge. |
| **Hero Section** | Bold typography with glowing gradient text ("Code is not just text. **It is a living architecture.**"), value proposition, checkmark guarantees, and action buttons. |
| **Interactive Pipeline Probe Card** | Mimics bigfive-test's 5-point question card with interactive radio pipelines (Hybrid Search, GBDT Ranker, AST Call Graph, Risk Classifier, Grounded Local LLM), animated progress bar, and live disassembly / AST formula preview. |
| **Floating Compare Pill** | Auto-cycling comparison pill with avatar stacks highlighting real CodeLens benchmarks (FAISS + BM25+ Fusion, 13-Feature GBDT Ranker, Polyglot AST Engine, Maintainability Risk ML, Qwen 2.5 Coder Studio). |
| **Glassmorphic Stats Panel** | 4-column frosted glass panel displaying key metrics (`< 15ms Latency`, `6 AST Languages`, `13 ML Features`, `0% Cloud / Zero Telemetry`). |
| **Side-by-Side Verification** | Ground-truth verification section comparing CodeLens against generic cloud RAG and naive vector search, with audience chips, 3-step workflow, and macOS comparison window tabs with dynamic animated progress tracks. |
| **Architecture Spotlight Card** | High-contrast spotlight card with key air-gapped security guarantees and the full CodeLens platform architecture diagram (`assets/hero.png`). |
| **The 5 Core Engines** | Styled after bigfive-test's OCEAN 5-dimension trait cards: Polyglot AST Call Graph `[A]`, Sub-15ms Hybrid Search `[H]`, Trained GBDT Ranker `[M]`, Maintainability Risk Classifier `[R]`, and Grounded Local LLM `[G]` with watermark letters, interactive draggable sliders, and facet tags. |
| **Interactive Alpha ($\alpha$) Simulator** | Live hybrid fusion simulator where dragging the weight slider ($\alpha$ from 0.0 to 1.0) calculates Recall@5, MRR, latency, and the live fusion formula in real time. |
| **Modules & Studio Grid** | 6 rich module cards with authentic figures and metadata (Polyglot Call Graph, Subword BM25+ Search, Trained GBDT Studio, Maintainability Risk Radar, Grounded Qwen Coder, Sandboxed Passive Ingestion). |
| **Operations CLI Box** | Multi-tab command box (`Launch Studio`, `Ingest Repo`, `Train ML`, `Run Pytest`) with one-click copy and instant visual feedback. |
| **Dark & Light Mode** | Fluid theme switching with persistence in `localStorage` and system preference detection. |

---

## 🚀 Running Locally

The landing page is self-contained with Vanilla HTML5, CSS3, and modern JavaScript.

### Using Python:
```bash
cd rea-landing-page
python3 -m http.server 4180
```
Open **[http://127.0.0.1:4180/](http://127.0.0.1:4180/)** in your browser.
