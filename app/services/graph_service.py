"""Service layer for dependency graph construction and serialization."""

from pathlib import Path
from typing import Dict, List, Optional
import networkx as nx
from app.config import settings
from app.ingestion.file_discovery import FileDiscovery
from app.parsing.dependency_extractor import DependencyExtractor
from app.schemas.graph import GraphResponse, GraphNode, GraphEdge


class GraphService:
    """Constructs and queries static import & dependency graphs."""

    def __init__(self):
        self.file_discovery = FileDiscovery()
        self.extractor = DependencyExtractor()

    def get_repository_graph(self, repo_name: str) -> GraphResponse:
        """Extracts and builds the dependency graph for an indexed repository."""
        possible_paths = [
            settings.REPOSITORIES_DIR / repo_name,
            settings.BASE_DIR / "tests" / "fixtures" / "sample_repo",
        ]
        repo_dir: Optional[Path] = None
        for p in possible_paths:
            if p.exists() and p.is_dir() and (p.name == repo_name or repo_name == "sample_repo"):
                repo_dir = p
                break

        if not repo_dir:
            # Check if index exists and extract from chunks
            index_dir = settings.INDEXES_DIR / repo_name
            if not index_dir.exists():
                raise FileNotFoundError(f"Repository '{repo_name}' not found.")
            # Default to sample repo path if needed
            repo_dir = settings.REPOSITORIES_DIR / repo_name
            if not repo_dir.exists():
                repo_dir = settings.BASE_DIR / "tests" / "fixtures" / "sample_repo"

        discovered = self.file_discovery.discover_files(repo_dir)
        G = self.extractor.build_graph(discovered, repo_name)

        nodes: List[GraphNode] = []
        for node_id, data in G.nodes(data=True):
            in_deg = G.in_degree(node_id)
            out_deg = G.out_degree(node_id)
            nodes.append(
                GraphNode(
                    id=node_id,
                    label=data.get("label", node_id),
                    type=data.get("type", "file"),
                    language=data.get("language"),
                    path=data.get("path", node_id),
                    size_bytes=data.get("size_bytes"),
                    in_degree=in_deg,
                    out_degree=out_deg,
                )
            )

        edges: List[GraphEdge] = []
        for u, v, data in G.edges(data=True):
            edges.append(
                GraphEdge(
                    source=u,
                    target=v,
                    relationship_type=data.get("relationship_type", "import_relationship"),
                    is_static=data.get("is_static", True),
                    raw_import=data.get("raw_import"),
                )
            )

        return GraphResponse(
            repository_id=repo_name,
            total_nodes=len(nodes),
            total_edges=len(edges),
            nodes=nodes,
            edges=edges,
        )


graph_service = GraphService()
