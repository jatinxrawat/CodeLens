# CV & Portfolio Project Summary

## 1. One-Line Summary (≤25 Words)
> Built and benchmarked a 100% local code intelligence engine combining tree-sitter AST extraction, dense-lexical hybrid retrieval, trained GBDT re-ranking, and grounded offline LLM reasoning.

---

## 2. Resume / CV Bullet Points

- **Architected 100% Offline Code Intelligence Platform**: Built a production-ready code reasoning engine indexing multi-language repositories (Python, JS, TS, Java, C++, C) via tree-sitter AST parsing and FAISS vector stores without external API dependencies.
- **Engineered Hybrid Retrieval & Learning-to-Rank**: Developed a hybrid search pipeline combining BM25 subword tokenization and SentenceTransformer embeddings, enhanced with a trained GBDT re-ranker evaluating 13 dense, lexical, and structural AST features.
- **Empirical ML Evaluation & Zero-Leakage Splitting**: Generated 21,900+ labeled samples using strict repository-level holdout partitioning; conducted systematic feature ablation studies and benchmarked Recall@K, MRR, NDCG, and 3×3 confusion matrices.
- **Grounded LLM Reasoning & Hallucination Guarding**: Integrated local Qwen 1.5B/7B inference with confidence gating, exact line-by-line source citations, and AST call graph tracing to guarantee verifiable, hallucination-resistant answers.

---

## 3. 60-Second Technical Pitch

> "I built the Local AI Code Intelligence Engine to solve a major enterprise dilemma: developers need deep codebase understanding and architectural question answering, but organizations cannot send proprietary source code to cloud APIs like OpenAI or Anthropic.
> 
> To solve this completely offline, I designed a multi-layer pipeline: First, Tree-sitter extracts multi-language AST code chunks. Next, a hybrid retrieval engine pairs dense SentenceTransformer embeddings in FAISS with subword BM25 keyword search. We then pass candidate chunks through a trained GBDT ranking model that learns relevance from 13 dense, lexical, and structural features.
> 
> Finally, the top evidence passes through a hallucination confidence guard and is synthesized by a local open-source LLM with exact source citations and call graph paths. I evaluated the system across 21,900+ samples using strict repository-level splits to guarantee zero data leakage, and conducted full ablation studies measuring Recall@K, MRR, and NDCG."
