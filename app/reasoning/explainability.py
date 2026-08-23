"""Explainability and Decision Factors Generator.

Exposes user-facing reasoning evidence explaining why specific code chunks,
symbols, or files were selected by the retrieval and reasoning pipeline.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.code_chunk import SearchResult, CodeChunk


class DecisionFactor(BaseModel):
    label: str
    factor_type: str  # 'similarity', 'symbol_match', 'import_graph', 'lexical_overlap', 'architectural_layer'
    description: str


class ExplainabilityEngine:
    """Generates transparent, user-facing rationale for retrieval and reasoning outputs."""

    def __init__(self):
        pass

    def extract_decision_factors(
        self,
        query: str,
        result: SearchResult,
        in_degree: int = 0,
        layer_name: Optional[str] = None,
    ) -> List[DecisionFactor]:
        """Generates structured decision factors for a retrieved result item."""
        factors: List[DecisionFactor] = []
        chunk = result.chunk
        query_words = set(query.lower().split())

        # 1. Similarity Factor
        factors.append(
            DecisionFactor(
                label=f"Semantic / Hybrid score: {round(result.score, 3)}",
                factor_type="similarity",
                description=f"Dense embedding & BM25 fused relevance score of {round(result.score * 100, 1)}%",
            )
        )

        # 2. Symbol Match Factor
        if chunk.symbol_name and any(w in chunk.symbol_name.lower() for w in query_words):
            factors.append(
                DecisionFactor(
                    label=f"AST symbol match: `{chunk.symbol_name}`",
                    factor_type="symbol_match",
                    description=f"Direct query keyword match with declared {chunk.chunk_type.value} identifier",
                )
            )

        # 3. Import Graph Centrality
        if in_degree > 0:
            factors.append(
                DecisionFactor(
                    label=f"Imported by {in_degree} module(s)",
                    factor_type="import_graph",
                    description=f"High static graph centrality in the repository import network",
                )
            )

        # 4. Architectural Layer
        if layer_name:
            factors.append(
                DecisionFactor(
                    label=f"Located in `{layer_name}` layer",
                    factor_type="architectural_layer",
                    description=f"File belongs to the inferred {layer_name} subsystem",
                )
            )

        return factors
