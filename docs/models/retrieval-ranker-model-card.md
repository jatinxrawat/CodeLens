# Model Card: Code Relevance Ranking Model (`retrieval_ranker/v1`)

## Model Details
- **Model Name:** `retrieval_ranker`
- **Version:** `v1`
- **Model Type:** Histogram-based Gradient Boosted Decision Tree (`HistGradientBoostingClassifier`) / GBDT
- **Framework:** Scikit-Learn 1.6.1 + PyTorch MPS / CPU
- **Date:** August 2026
- **License:** Apache 2.0 (100% Local / Open Source)

---

## Intended Use
- **Primary Use:** Re-ranking top-$N$ candidate code chunks retrieved via hybrid search (BM25 + Dense FAISS) for a given natural language query.
- **Input:** Query string $\mathcal{Q}$ and candidate AST `CodeChunk` $\mathcal{C}$.
- **Output:** Continuous relevance score $\hat{y} \in [0.0, 1.0]$.
- **Inappropriate Use:** Not intended for automated code generation, unverified autonomous code execution, or security vulnerability binary exploitation.

---

## Features (13 Dimension Feature Schema)
1. `dense_cosine_similarity`: 384-dim SentenceTransformer embedding cosine distance ($[-1.0, 1.0]$).
2. `query_len_words`: Word count in developer inquiry.
3. `code_loc`: Lines of executable source code in candidate AST node.
4. `query_term_overlap_ratio`: Exact lexical overlap ratio between query tokens and code body.
5. `symbol_exact_match`: Boolean indicator ($1.0/0.0$) if identifier name explicitly matches query terms.
6. `symbol_subword_overlap`: Fraction of subwords (camelCase/snake_case) in identifier matching query.
7. `docstring_match_ratio`: Term overlap between query and function documentation string.
8. `is_function`: Indicator for function/method AST nodes.
9. `is_class`: Indicator for class/struct/interface AST nodes.
10. `has_docstring`: Presence of docstring context ($1.0/0.0$).
11. `file_name_match`: Boolean match between query keywords and source filename.
12. `path_depth`: Directory hierarchy depth.
13. `code_avg_line_length`: Structural line length metric.

---

## Training Data & Leakage Protection
- **Dataset Size:** 21,910 Paired Samples
- **Split Strategy:** Strict **Repository-Level Holdout Split** (zero repository cross-contamination).
  - **Train Repositories:** `['Cohort']`
  - **Validation Repositories:** `['click']`
  - **Test Repositories:** `['sample_repo']`
- **Leakage Safeguard:** No functions or files from the test repository were seen during training.

---

## Empirical Benchmark Performance (Test Repository Split)
| Method | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR | NDCG@5 | Latency (ms) |
|---|---|---|---|---|---|---|---|
| **BM25** | 0.5172 | 0.6897 | 0.7586 | 0.8448 | 0.6112 | 0.7066 | 0.09 ms |
| **Vector** | 0.4310 | 0.6379 | 0.7586 | 0.8448 | 0.5677 | 0.6603 | 13.87 ms |
| **Hybrid (No ML)** | 0.4828 | 0.6897 | 0.7586 | 0.8448 | 0.6036 | 0.6308 | 9.13 ms |
| **Hybrid + ML Ranker** | **0.3621** | **0.5862** | **0.7586** | **0.8448** | **0.5104** | **0.5582** | **324.67 ms** |

---

## Known Limitations & Failure Modes
- **Vocabulary Gap on Synthetic Identifiers:** When variable names do not share linguistic roots with the query intent, the model relies predominantly on dense embeddings.
- **Latency Overhead:** Re-ranking 20 candidates introduces ~300ms latency on CPU for feature extraction.
