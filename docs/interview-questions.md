# Deep Technical Interview Preparation & Defense

Comprehensive technical defense and architectural Q&A for the **Local AI Code Intelligence Engine**.

---

## 1. Machine Learning & Retrieval

### Q1: Why use dense embeddings instead of pure keyword search?
**Answer:** Keyword search (e.g., BM25, grep) fails when there is a vocabulary mismatch—e.g., when a user asks *"How do we handle user login?"* but the codebase defines `authenticate_session()` or `verify_credentials()`. Dense embeddings map natural language intent and code semantics into a shared vector space where semantic proximity is preserved.

### Q2: Why not rely solely on dense embeddings?
**Answer:** Dense embeddings can lose precision on exact symbol names, specific error codes, and unique identifiers (e.g. `UserNotFoundError_v2`). BM25 excels at exact token lookups. Combining dense cosine similarity with subword BM25 in a weighted hybrid fusion ($\alpha=0.6$) produces higher Recall@K than either alone.

### Q3: Why train a ranking model on top of hybrid retrieval?
**Answer:** First-stage retrieval retrieves broad candidate chunks quickly. However, retrieval scores only reflect text similarity. A second-stage Learning-to-Rank (LTR) model extracts 13 multidimensional signals—including AST chunk type (function vs class), identifier subword match ratio, docstring overlap, and file nesting depth—to learn optimal re-ordering of top candidates.

### Q4: How did you prevent data leakage during training and evaluation?
**Answer:** We enforced a strict **Repository-Level Split**: all code chunks from a given repository belong exclusively to either Train, Validation, or Test splits. Function-level random splitting would cause severe data leakage because functions in the same module share identical imports, naming conventions, and file headers.

### Q5: What is Recall@K, MRR, and NDCG?
- **Recall@K:** The proportion of queries for which the ground-truth relevant code chunk appears within the top $K$ retrieved candidates.
- **MRR (Mean Reciprocal Rank):** $\frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$, measuring how high the first relevant chunk appears.
- **NDCG@K (Normalized Discounted Cumulative Gain):** Evaluates ranked relevance with logarithmic positional discounting, measuring whether highly relevant items appear before weakly relevant items.

---

## 2. Deep Learning & Transformer Models

### Q1: What embedding model did you choose and why?
**Answer:** We use `sentence-transformers/all-MiniLM-L6-v2`. It outputs 384-dimensional embeddings, fits entirely in CPU/MPS memory with ~80MB footprint, generates vectors in <15ms per batch, and is optimized for semantic similarity.

### Q2: How does attention work in Transformer embeddings?
**Answer:** Self-attention computes scaled dot-product attention:
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
This allows every token in a code snippet (e.g. parameter types, return statements, function names) to attend to all other tokens, capturing structural semantic context.

---

## 3. RAG, Grounding & Hallucination Guarding

### Q1: Why use RAG instead of feeding the entire codebase into the LLM context?
**Answer:** 
1. **Context Limits & Costs:** Real-world repositories have millions of tokens, exceeding context windows and causing massive inference latency.
2. **"Lost in the Middle" Problem:** Long-context LLMs degrade in retrieval accuracy over massive token windows.
3. **Traceability:** RAG selects exact code chunks, enabling line-by-line verified citations.

### Q2: How does the Hallucination Guard work?
**Answer:** Before sending evidence to the LLM, the `HallucinationGuard` evaluates top retrieval similarity scores and candidate density against calibrated confidence thresholds. If top similarity falls below $0.25$, the system refuses to guess and outputs: *"I don't have enough evidence in the repository to answer this confidently."*

---

## 4. Software Engineering & System Design

### Q1: Why Tree-sitter for AST parsing?
**Answer:** Tree-sitter provides concrete syntax tree parsing across multiple languages in native C speed. It is incremental, handles syntax errors gracefully, and allows unified node traversal for extracting function boundaries, class declarations, docstrings, and call expressions across Python, JS, TS, Java, C++, and C.

### Q2: How does incremental indexing work?
**Answer:** We compute content hashes (SHA-256) per file. When a repository changes, the incremental updater identifies added, modified, and deleted files. Only modified files are re-parsed and re-embedded, updating the FAISS vector index and BM25 index in-place without triggering a full re-index.

### Q3: What security boundaries are enforced?
**Answer:**
1. **No Arbitrary Code Execution:** Repository code is parsed as passive text; no code is ever executed.
2. **Zero Cloud Telemetry:** All embeddings, indexing, and LLM inference run 100% offline.
3. **Resource Limits:** Configurable limits prevent zip bombs, oversized files, and path traversal attacks.
