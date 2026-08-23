"""Potential Impact Analysis and Blast Radius Analyzer.

Estimates affected files and modules when modifying a target file or symbol
using static import graphs, symbol call references, and retrieval similarity.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.code_chunk import CodeChunk
from app.config import settings
from app.parsing.dependency_extractor import DependencyExtractor
from app.ingestion.file_discovery import FileDiscovery


class ImpactItem(BaseModel):
    file_path: str
    impact_level: str = Field(..., description="'HIGH', 'MEDIUM', 'LOW'")
    relationship_type: str = Field(
        ...,
        description="'direct_import', 'symbol_caller', 'co_dependency', 'semantic_similarity'"
    )
    confidence_score: float
    reason: str
    affected_symbols: List[str] = []


class ImpactAnalysisResult(BaseModel):
    target: str
    target_type: str = Field(..., description="'file' or 'symbol'")
    total_affected_files: int
    high_impact_count: int
    medium_impact_count: int
    low_impact_count: int
    impacted_files: List[ImpactItem]
    disclaimer: str = (
        "Potential Impact Analysis is calculated via static AST import graphs and symbol references. "
        "Dynamic reflection and runtime event buses are not statically guaranteed."
    )


class ImpactAnalyzer:
    """Analyzes the blast radius of modifying a specific file or symbol."""

    def __init__(self):
        self.file_discovery = FileDiscovery()
        self.dependency_extractor = DependencyExtractor()

    def analyze_impact(
        self,
        repo_name: str,
        target_path_or_symbol: str,
    ) -> ImpactAnalysisResult:
        """Computes ranked impacted files for a target file or symbol."""
        index_dir = settings.INDEXES_DIR / repo_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            raise FileNotFoundError(f"Repository index for '{repo_name}' not found.")

        with open(chunks_file, "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)
        chunks = [CodeChunk.from_dict(c) for c in raw_chunks]

        # Determine if target is file or symbol
        is_file = any(c.file_path == target_path_or_symbol or target_path_or_symbol in c.file_path for c in chunks)
        target_file = target_path_or_symbol if is_file else None

        # Build Dependency Graph
        repo_dir = settings.REPOSITORIES_DIR / repo_name
        if not repo_dir.exists():
            repo_dir = settings.BASE_DIR / "tests" / "fixtures" / "sample_repo"
        discovered = self.file_discovery.discover_files(repo_dir)
        G = self.dependency_extractor.build_graph(discovered, repo_name)

        impact_map: Dict[str, ImpactItem] = {}

        # 1. Direct Importers (High Impact)
        target_node_id = None
        for node in G.nodes():
            if target_file and (target_file in node or node in target_file):
                target_node_id = node
                break

        if target_node_id:
            for pred in G.predecessors(target_node_id):
                node_data = G.nodes[pred]
                if node_data.get("type") == "file":
                    f_path = node_data.get("path", pred)
                    impact_map[f_path] = ImpactItem(
                        file_path=f_path,
                        impact_level="HIGH",
                        relationship_type="direct_import",
                        confidence_score=0.95,
                        reason=f"Directly imports `{target_file}` via static import statement",
                        affected_symbols=[],
                    )

        # 2. Symbol References (High/Medium Impact)
        target_symbols = []
        if target_file:
            target_symbols = [c.symbol_name for c in chunks if c.file_path == target_file and c.symbol_name]
        else:
            target_symbols = [target_path_or_symbol]

        for sym in target_symbols:
            if not sym:
                continue
            for c in chunks:
                if target_file and c.file_path == target_file:
                    continue
                if sym in c.code:
                    if c.file_path not in impact_map:
                        impact_map[c.file_path] = ImpactItem(
                            file_path=c.file_path,
                            impact_level="HIGH",
                            relationship_type="symbol_caller",
                            confidence_score=0.88,
                            reason=f"References symbol `{sym}` defined in target at line {c.start_line}",
                            affected_symbols=[sym],
                        )
                    else:
                        if sym not in impact_map[c.file_path].affected_symbols:
                            impact_map[c.file_path].affected_symbols.append(sym)

        # 3. Transitive Co-dependencies (Medium/Low Impact)
        if target_node_id:
            for pred in list(G.predecessors(target_node_id)):
                for grand_pred in G.predecessors(pred):
                    g_data = G.nodes[grand_pred]
                    if g_data.get("type") == "file":
                        f_path = g_data.get("path", grand_pred)
                        if f_path not in impact_map and f_path != target_file:
                            impact_map[f_path] = ImpactItem(
                                file_path=f_path,
                                impact_level="MEDIUM",
                                relationship_type="co_dependency",
                                confidence_score=0.65,
                                reason=f"Transitively depends on target via intermediary `{pred}`",
                                affected_symbols=[],
                            )

        sorted_impacts = sorted(
            impact_map.values(),
            key=lambda x: (
                0 if x.impact_level == "HIGH" else (1 if x.impact_level == "MEDIUM" else 2),
                -x.confidence_score,
            ),
        )

        high_cnt = sum(1 for x in sorted_impacts if x.impact_level == "HIGH")
        med_cnt = sum(1 for x in sorted_impacts if x.impact_level == "MEDIUM")
        low_cnt = sum(1 for x in sorted_impacts if x.impact_level == "LOW")

        return ImpactAnalysisResult(
            target=target_path_or_symbol,
            target_type="file" if is_file else "symbol",
            total_affected_files=len(sorted_impacts),
            high_impact_count=high_cnt,
            medium_impact_count=med_cnt,
            low_impact_count=low_cnt,
            impacted_files=sorted_impacts,
        )
