"""BM25 Lexical search index for source code keyword retrieval."""

import re
import pickle
from pathlib import Path
from typing import List, Optional
from rank_bm25 import BM25Plus
from app.models.code_chunk import CodeChunk, SearchResult
from app.config import settings


class BM25CodeTokenizer:
    """Specialized code tokenizer that splits identifiers, camelCase, snake_case, and symbols."""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenizes code text into normalized subwords and identifiers."""
        # Split on non-alphanumeric characters first
        raw_tokens = re.findall(r"[a-zA-Z0-9_]+", text)
        sub_tokens: List[str] = []

        for token in raw_tokens:
            token_lower = token.lower()
            if len(token_lower) > 1:
                sub_tokens.append(token_lower)

            # Split camelCase: 'loginUser' -> ['login', 'user']
            camel_parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", token)
            if len(camel_parts) > 1:
                for part in camel_parts:
                    p_lower = part.lower()
                    if len(p_lower) > 1 and p_lower != token_lower:
                        sub_tokens.append(p_lower)

            # Split snake_case: 'process_order' -> ['process', 'order']
            if "_" in token:
                for part in token.split("_"):
                    p_lower = part.lower()
                    if len(p_lower) > 1 and p_lower != token_lower:
                        sub_tokens.append(p_lower)

        return sub_tokens


class BM25Store:
    """Manages BM25 lexical index for code chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.tokenizer = BM25CodeTokenizer()
        self.bm25: Optional[BM25Plus] = None
        self.chunks: List[CodeChunk] = []
        self.tokenized_corpus: List[List[str]] = []

    def add_chunks(self, chunks: List[CodeChunk]):
        """Tokenizes code chunks and constructs the BM25Plus index."""
        self.chunks = list(chunks)
        self.tokenized_corpus = []

        for chunk in chunks:
            text = chunk.get_embeddable_text()
            tokens = self.tokenizer.tokenize(text)
            self.tokenized_corpus.append(tokens)

        if self.tokenized_corpus:
            self.bm25 = BM25Plus(self.tokenized_corpus, k1=self.k1, b=self.b)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Searches BM25 index using tokenized query and returns ranked SearchResults."""
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = self.tokenizer.tokenize(query)
        if not query_tokens:
            return []

        doc_scores = self.bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]

        results: List[SearchResult] = []
        rank = 1
        for idx in top_indices:
            score = float(doc_scores[idx])
            if score <= 0:
                continue
            results.append(
                SearchResult(
                    chunk=self.chunks[idx],
                    score=score,
                    rank=rank,
                )
            )
            rank += 1

        return results

    def save(self, index_dir: Path):
        """Persists the BM25 tokenized corpus and chunk references to disk."""
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        bm25_file = index_dir / "bm25.pkl"

        data = {
            "tokenized_corpus": self.tokenized_corpus,
            "k1": self.k1,
            "b": self.b,
        }
        with open(bm25_file, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, index_dir: Path, chunks: List[CodeChunk]) -> "BM25Store":
        """Loads persisted BM25 index from disk."""
        index_dir = Path(index_dir)
        bm25_file = index_dir / "bm25.pkl"

        if not bm25_file.exists():
            # If not yet persisted, build on-the-fly from chunks
            store = cls(k1=settings.BM25_K1, b=settings.BM25_B)
            store.add_chunks(chunks)
            return store

        with open(bm25_file, "rb") as f:
            data = pickle.load(f)

        store = cls(k1=data.get("k1", settings.BM25_K1), b=data.get("b", settings.BM25_B))
        store.chunks = chunks
        store.tokenized_corpus = data["tokenized_corpus"]
        if store.tokenized_corpus:
            store.bm25 = BM25Plus(store.tokenized_corpus, k1=store.k1, b=store.b)
        return store
