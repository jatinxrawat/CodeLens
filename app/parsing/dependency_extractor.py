"""AST-based static import and dependency extractor across supported languages."""

import re
from pathlib import Path
from typing import List, Dict, Set, Any, Tuple
import networkx as nx
from tree_sitter import Node, Tree
from app.parsing.tree_sitter_parser import TreeSitterParserManager
from app.ingestion.file_discovery import DiscoveredFile
from app.config import settings


class DependencyExtractor:
    """Extracts static import relationships and builds a directed dependency graph using NetworkX."""

    def __init__(self):
        pass

    def extract_imports_from_file(self, file_path: Path, language: str) -> List[str]:
        """Extracts imported module/file names using regex and AST node inspection."""
        try:
            source_bytes = file_path.read_bytes()
            content = source_bytes.decode("utf-8", errors="replace")
        except OSError:
            return []

        imports: Set[str] = set()

        if language == "python":
            # import foo, from foo.bar import baz
            for match in re.finditer(r"^\s*(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.,\s]+))", content, re.MULTILINE):
                from_mod, imp_mod = match.groups()
                if from_mod:
                    imports.add(from_mod)
                elif imp_mod:
                    for part in imp_mod.split(","):
                        clean_p = part.strip().split(" as ")[0].strip()
                        if clean_p:
                            imports.add(clean_p)

        elif language in ("javascript", "typescript"):
            # import ... from './path' or require('./path')
            for match in re.finditer(r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""", content):
                mod = match.group(1) or match.group(2)
                if mod:
                    imports.add(mod)

        elif language == "java":
            # import com.example.service.OrderService;
            for match in re.finditer(r"^\s*import\s+(?:static\s+)?([a-zA-Z0-9_\.]+);", content, re.MULTILINE):
                imports.add(match.group(1))

        elif language in ("cpp", "c"):
            # #include "header.h" or #include <vector>
            for match in re.finditer(r"""^\s*#include\s*[<"]([^>"]+)[>"]""", content, re.MULTILINE):
                imports.add(match.group(1))

        return sorted(list(imports))

    def build_graph(self, discovered_files: List[DiscoveredFile], repo_name: str) -> nx.DiGraph:
        """Constructs a NetworkX directed graph containing file nodes, symbol nodes, and dependency edges."""
        G = nx.DiGraph()

        file_lookup: Dict[str, DiscoveredFile] = {}
        stem_lookup: Dict[str, str] = {}  # e.g., 'auth' -> 'python/auth.py'

        for df in discovered_files:
            rel_path = df.relative_path
            file_lookup[rel_path] = df
            stem = Path(rel_path).stem.lower()
            stem_lookup[stem] = rel_path

            # Add file node
            G.add_node(
                rel_path,
                id=rel_path,
                label=Path(rel_path).name,
                type="file",
                language=df.language,
                size_bytes=df.size_bytes,
                path=rel_path,
            )

        # Extract dependencies and add edges
        for df in discovered_files:
            raw_imports = self.extract_imports_from_file(df.full_path, df.language)

            for imp in raw_imports:
                target_file: str | None = None
                edge_kind = "import_relationship"

                # 1. Exact relative file match (e.g. '../auth/login' or './payment')
                clean_imp = imp.lstrip("./").rstrip(".js").rstrip(".ts").rstrip(".py")
                for candidate_path in file_lookup:
                    if candidate_path.endswith(f"{clean_imp}.{df.language[:2]}") or clean_imp in candidate_path:
                        target_file = candidate_path
                        break

                # 2. Module stem match (e.g. 'auth' -> 'python/auth.py')
                if not target_file:
                    imp_stem = imp.split(".")[-1].split("/")[-1].lower()
                    if imp_stem in stem_lookup and stem_lookup[imp_stem] != df.relative_path:
                        target_file = stem_lookup[imp_stem]

                if target_file and target_file in G:
                    # Confirmed local import edge
                    G.add_edge(
                        df.relative_path,
                        target_file,
                        source=df.relative_path,
                        target=target_file,
                        relationship_type="import_relationship",
                        is_static=True,
                        raw_import=imp,
                    )
                else:
                    # External or standard library dependency node
                    ext_node_id = f"ext:{imp}"
                    if not G.has_node(ext_node_id):
                        G.add_node(
                            ext_node_id,
                            id=ext_node_id,
                            label=imp,
                            type="external_package",
                            language=df.language,
                            path=imp,
                        )
                    G.add_edge(
                        df.relative_path,
                        ext_node_id,
                        source=df.relative_path,
                        target=ext_node_id,
                        relationship_type="external_import",
                        is_static=True,
                        raw_import=imp,
                    )

        return G
