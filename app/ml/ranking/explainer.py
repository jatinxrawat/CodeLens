"""Ranking Model Explainability Layer.

Computes transparent feature contributions for individual ranked results.
"""

from typing import List, Dict, Any, Optional
from app.models.code_chunk import CodeChunk
from app.ml.ranking.ranker_model import CodeRankerModel
from app.ml.ranking.feature_extractor import RankingFeatureExtractor


class RankingExplainer:
    """Explains why candidate code chunks were ranked by the ML model."""

    def __init__(self, ranker: Optional[CodeRankerModel] = None):
        self.ranker = ranker
        self.extractor = RankingFeatureExtractor()

    def explain_candidate(
        self,
        query: str,
        chunk: CodeChunk,
        relevance_score: float,
    ) -> Dict[str, Any]:
        """Formulates human-interpretable feature contribution factors for a single candidate."""
        feats = self.extractor.extract_features(query, chunk)
        factors = []

        # 1. Semantic Similarity
        sim = feats["dense_cosine_similarity"]
        sim_level = "High" if sim > 0.6 else "Medium" if sim > 0.3 else "Low"
        factors.append({
            "feature": "Semantic Similarity",
            "value": f"{sim * 100:.1f}%",
            "impact": sim_level,
            "description": f"Dense embedding cosine similarity is {sim * 100:.1f}%.",
        })

        # 2. Symbol Match
        if feats["symbol_exact_match"] == 1.0:
            factors.append({
                "feature": "Exact Symbol Match",
                "value": f"`{chunk.symbol_name}`",
                "impact": "Very High",
                "description": f"Function/class identifier `{chunk.symbol_name}` directly matches query keyword.",
            })
        elif feats["symbol_subword_overlap"] > 0:
            factors.append({
                "feature": "Subword Symbol Match",
                "value": f"{feats['symbol_subword_overlap'] * 100:.0f}%",
                "impact": "Medium",
                "description": "Identifier subwords overlap with query terms.",
            })

        # 3. Keyword Overlap
        if feats["query_term_overlap_ratio"] > 0:
            factors.append({
                "feature": "Keyword Overlap",
                "value": f"{feats['query_term_overlap_ratio'] * 100:.0f}%",
                "impact": "High" if feats["query_term_overlap_ratio"] > 0.5 else "Medium",
                "description": f"Overlaps with {feats['query_term_overlap_ratio'] * 100:.0f}% of query terms in code body.",
            })

        # 4. Filename Relevance
        if feats["file_name_match"] == 1.0:
            factors.append({
                "feature": "Filename Relevance",
                "value": chunk.file_path,
                "impact": "High",
                "description": f"Query specifically references file `{chunk.file_path}`.",
            })

        # 5. Docstring Context
        if feats["has_docstring"] == 1.0 and feats["docstring_match_ratio"] > 0:
            factors.append({
                "feature": "Docstring Match",
                "value": f"{feats['docstring_match_ratio'] * 100:.0f}%",
                "impact": "Medium",
                "description": "Documentation comment matches query intent.",
            })

        return {
            "relevance_score": relevance_score,
            "factors": factors,
            "raw_features": feats,
        }
