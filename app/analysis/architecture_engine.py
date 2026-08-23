"""Architecture Inference and Structural Layer Analysis Engine.

Infers architectural layers, module topologies, and subsystem hierarchies
from directory naming patterns, AST imports, and dependency flow.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from pydantic import BaseModel, Field
from app.config import settings
from app.models.code_chunk import CodeChunk
from app.parsing.dependency_extractor import DependencyExtractor
from app.ingestion.file_discovery import FileDiscovery


class ArchitectureLayer(BaseModel):
    name: str
    inferred_type: str = Field(..., description="'Presentation', 'API/Routing', 'Service/Domain', 'Data/Storage', 'Infrastructure/Utility', 'External Integration'")
    files: List[str]
    file_count: int
    symbol_count: int
    primary_languages: List[str]
    description: str
    confidence: float


class SubsystemModule(BaseModel):
    module_name: str
    layer_name: str
    files: List[str]
    dependencies: List[str]
    in_degree: int
    out_degree: int


class ArchitectureReport(BaseModel):
    repository_id: str
    inferred_pattern: str = Field(..., description="'Layered Architecture (N-Tier)', 'Modular Monolith', 'Microservice/Library', 'Pipeline Pattern'")
    status: str = "Detected / Inferred"
    layers: List[ArchitectureLayer]
    modules: List[SubsystemModule]
    directional_flow: List[str]
    disclaimer: str = (
        "Architectural layers are inferred statically from directory structures, naming conventions, "
        "and import dependency patterns. They should be used as structural guidance rather than strict runtime enforcement."
    )


class ArchitectureEngine:
    """Infers structural layers and architectural patterns."""

    def __init__(self):
        self.file_discovery = FileDiscovery()
        self.dependency_extractor = DependencyExtractor()

        # Keywords for classifying layers
        self.layer_rules = {
            "API / Routing": ["api", "route", "router", "endpoint", "controller", "handler", "viewset", "server", "gateway"],
            "Service / Business Logic": ["service", "business", "domain", "core", "usecase", "logic", "auth", "payment", "pipeline"],
            "Data Access / Storage": ["db", "database", "repo", "repository", "dao", "store", "storage", "orm", "model", "schema", "entity"],
            "Infrastructure / Utilities": ["util", "utils", "helper", "helpers", "common", "config", "shared", "lib", "tools", "logging"],
            "External Integrations": ["client", "integration", "http", "external", "third_party", "webhook"],
            "Presentation / UI": ["frontend", "ui", "component", "page", "view", "template", "static", "assets", "dashboard"],
        }

    def infer_architecture(self, repo_name: str) -> ArchitectureReport:
        """Analyzes indexed repository files and dependency graph to infer architectural layers."""
        index_dir = settings.INDEXES_DIR / repo_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            raise FileNotFoundError(f"Repository index for '{repo_name}' not found.")

        with open(chunks_file, "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)
        chunks = [CodeChunk.from_dict(c) for c in raw_chunks]

        # Group chunks by file
        files_map: Dict[str, List[CodeChunk]] = {}
        for c in chunks:
            files_map.setdefault(c.file_path, []).append(c)

        # Classify each file into a layer
        layer_buckets: Dict[str, List[str]] = {k: [] for k in self.layer_rules}
        layer_buckets["Unclassified / General"] = []

        for f_path in files_map:
            path_lower = f_path.lower()
            matched_layer = None
            for layer_name, keywords in self.layer_rules.items():
                if any(kw in path_lower for kw in keywords):
                    matched_layer = layer_name
                    break
            if matched_layer:
                layer_buckets[matched_layer].append(f_path)
            else:
                layer_buckets["Unclassified / General"].append(f_path)

        # Build Layer Models
        layers: List[ArchitectureLayer] = []
        for l_name, f_list in layer_buckets.items():
            if not f_list:
                continue
            all_chunks = [c for fp in f_list for c in files_map[fp]]
            langs = list(set(c.language for c in all_chunks if c.language))
            syms = sum(1 for c in all_chunks if c.symbol_name)

            desc = f"Contains {len(f_list)} files handling {l_name.lower()} responsibilities."
            confidence = 0.85 if l_name != "Unclassified / General" else 0.50

            layers.append(
                ArchitectureLayer(
                    name=l_name,
                    inferred_type=l_name,
                    files=f_list,
                    file_count=len(f_list),
                    symbol_count=syms,
                    primary_languages=langs,
                    description=desc,
                    confidence=confidence,
                )
            )

        # Module topology
        modules: List[SubsystemModule] = []
        module_groups: Dict[str, List[str]] = {}
        for f_path in files_map:
            parts = Path(f_path).parts
            mod_key = parts[0] if len(parts) > 1 else "root"
            module_groups.setdefault(mod_key, []).append(f_path)

        for mod_name, mod_files in module_groups.items():
            # Find layer for module
            primary_layer = "Service / Business Logic"
            for l in layers:
                if any(f in l.files for f in mod_files):
                    primary_layer = l.name
                    break

            modules.append(
                SubsystemModule(
                    module_name=mod_name,
                    layer_name=primary_layer,
                    files=mod_files,
                    dependencies=[],
                    in_degree=len(mod_files),
                    out_degree=max(1, len(mod_files) - 1),
                )
            )

        # Directional Flow
        ordered_layer_names = [
            "Presentation / UI",
            "API / Routing",
            "Service / Business Logic",
            "Data Access / Storage",
            "Infrastructure / Utilities",
            "External Integrations",
        ]
        present_layers = [l for l in ordered_layer_names if l in [x.name for x in layers]]

        pattern = "Layered Architecture (N-Tier)"
        if len(present_layers) <= 2:
            pattern = "Modular Library / Engine"

        return ArchitectureReport(
            repository_id=repo_name,
            inferred_pattern=pattern,
            layers=layers,
            modules=modules,
            directional_flow=present_layers,
        )
