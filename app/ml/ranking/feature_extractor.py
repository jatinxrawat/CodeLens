"""Code Ranking Feature Extractor.

Extracts semantic, lexical, structural AST, and metadata features from a (query, code_chunk) pair.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
import re

from app.models.code_chunk import CodeChunk
from app.embeddings import SentenceTransformerEmbeddingModel
from app.retrieval.bm25_store import BM25CodeTokenizer


class RankingFeatureExtractor:
    """Extracts multidimensional ranking features for ML re-ranking models."""

    FEATURE_NAMES = [
        "dense_cosine_similarity",     # Semantic similarity from SentenceTransformers
        "query_len_words",             # Number of words in query
        "code_loc",                    # Lines of code in candidate
        "query_term_overlap_ratio",    # Fraction of query words appearing in code
        "symbol_exact_match",          # 1.0 if chunk symbol explicitly appears in query
        "symbol_subword_overlap",      # Fraction of subwords in symbol matching query
        "docstring_match_ratio",       # Term overlap with docstring
        "is_function",                 # 1.0 if chunk_type == function or method
        "is_class",                    # 1.0 if chunk_type == class
        "has_docstring",               # 1.0 if docstring exists
        "file_name_match",             # 1.0 if file name appears in query
        "path_depth",                  # Directory nesting depth of file
        "code_avg_line_length",        # Average length of code lines
    ]

    def __init__(self, embedding_model: Optional[SentenceTransformerEmbeddingModel] = None):
        self.embedding_model = embedding_model or SentenceTransformerEmbeddingModel()
        self.tokenizer = BM25CodeTokenizer()

    def extract_features(
        self,
        query: str,
        chunk: CodeChunk,
        query_embedding: Optional[np.ndarray] = None,
        chunk_embedding: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Computes all numerical ranking features for a single (query, chunk) pair."""
        # 1. Semantic Cosine Similarity
        if query_embedding is None:
            query_embedding = self.embedding_model.encode_single(query)
        if chunk_embedding is None:
            chunk_embedding = self.embedding_model.encode_single(chunk.get_embeddable_text())

        # Cosine similarity for normalized vectors = dot product
        cosine_sim = float(np.dot(query_embedding, chunk_embedding))
        cosine_sim = max(-1.0, min(1.0, cosine_sim))

        # 2. Token overlap features
        query_tokens = set(self.tokenizer.tokenize(query))
        code_tokens = set(self.tokenizer.tokenize(chunk.code))
        query_len = max(1, len(query.split()))

        overlap_tokens = query_tokens.intersection(code_tokens)
        overlap_ratio = len(overlap_tokens) / max(1, len(query_tokens))

        # 3. Symbol Matching
        symbol_exact = 0.0
        symbol_overlap = 0.0
        if chunk.symbol_name:
            if chunk.symbol_name.lower() in query.lower():
                symbol_exact = 1.0
            sym_tokens = set(self.tokenizer.tokenize(chunk.symbol_name))
            sym_overlap = sym_tokens.intersection(query_tokens)
            symbol_overlap = len(sym_overlap) / max(1, len(sym_tokens))

        # 4. Docstring Matching
        docstring_ratio = 0.0
        if chunk.docstring:
            doc_tokens = set(self.tokenizer.tokenize(chunk.docstring))
            doc_overlap = doc_tokens.intersection(query_tokens)
            docstring_ratio = len(doc_overlap) / max(1, len(query_tokens))

        # 5. Filename & Path
        file_name = Path(chunk.file_path).stem.lower()
        file_match = 1.0 if file_name in query.lower() else 0.0
        path_depth = float(len(Path(chunk.file_path).parts))

        # 6. Code Structure
        lines = chunk.code.splitlines()
        loc = float(len([l for l in lines if l.strip()]))
        avg_line_len = float(sum(len(l) for l in lines) / max(1, len(lines)))

        is_fn = 1.0 if chunk.chunk_type.value in ("function", "method") else 0.0
        is_cls = 1.0 if chunk.chunk_type.value in ("class", "struct", "interface") else 0.0

        return {
            "dense_cosine_similarity": round(cosine_sim, 4),
            "query_len_words": float(query_len),
            "code_loc": loc,
            "query_term_overlap_ratio": round(overlap_ratio, 4),
            "symbol_exact_match": symbol_exact,
            "symbol_subword_overlap": round(symbol_overlap, 4),
            "docstring_match_ratio": round(docstring_ratio, 4),
            "is_function": is_fn,
            "is_class": is_cls,
            "has_docstring": 1.0 if chunk.docstring else 0.0,
            "file_name_match": file_match,
            "path_depth": path_depth,
            "code_avg_line_length": round(avg_line_len, 2),
        }

    def extract_feature_vector(self, query: str, chunk: CodeChunk) -> np.ndarray:
        """Returns feature vector as 1D float numpy array in canonical order."""
        feats = self.extract_features(query, chunk)
        return np.array([feats[name] for name in self.FEATURE_NAMES], dtype=np.float32)
