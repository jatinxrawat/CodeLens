"""Tree-sitter AST parser for Java source code."""

from typing import List, Optional
from tree_sitter import Node, Tree
from app.models.code_chunk import CodeChunk, ChunkType
from app.parsing.languages.base import BaseLanguageParser


class JavaParser(BaseLanguageParser):
    """AST parser for Java extracting classes, interfaces, records, constructors, and methods."""

    def __init__(self):
        super().__init__("java")

    def _get_node_by_type(self, node: Node, target_type: str) -> Optional[Node]:
        for child in node.children:
            if child.type == target_type:
                return child
        return None

    def _extract_comments(self, node: Node, source_bytes: bytes) -> Optional[str]:
        return self.get_preceding_comment(node, source_bytes)

    def extract_chunks(
        self,
        tree: Tree,
        source_bytes: bytes,
        file_path: str,
        repo_name: str,
    ) -> List[CodeChunk]:
        chunks: List[CodeChunk] = []

        def traverse(node: Node, parent_class: Optional[str] = None):
            # 1. Class, Interface, Enum, Record Declarations
            if node.type in {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration"}:
                name_node = self._get_node_by_type(node, "identifier")
                class_name = self.get_node_text(name_node, source_bytes) if name_node else "AnonymousClass"
                docstring = self._extract_comments(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                chunk_type = ChunkType.INTERFACE if node.type == "interface_declaration" else ChunkType.CLASS
                symbol = f"{parent_class}.{class_name}" if parent_class else class_name

                chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, symbol)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        repo_name=repo_name,
                        file_path=file_path,
                        language=self.language_name,
                        chunk_type=chunk_type,
                        symbol_name=symbol,
                        start_line=start_line,
                        end_line=end_line,
                        code=code_text,
                        docstring=docstring,
                        context_prefix=f"Parent: {parent_class}" if parent_class else None,
                    )
                )

                body_node = self._get_node_by_type(node, "class_body") or self._get_node_by_type(node, "interface_body") or self._get_node_by_type(node, "enum_body")
                if body_node:
                    for child in body_node.children:
                        traverse(child, parent_class=symbol)
                return

            # 2. Methods and Constructors
            elif node.type in {"method_declaration", "constructor_declaration"}:
                name_node = self._get_node_by_type(node, "identifier")
                name = self.get_node_text(name_node, source_bytes) if name_node else "anonymous_method"
                docstring = self._extract_comments(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                symbol = f"{parent_class}.{name}" if parent_class else name

                chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, symbol)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        repo_name=repo_name,
                        file_path=file_path,
                        language=self.language_name,
                        chunk_type=ChunkType.METHOD,
                        symbol_name=symbol,
                        start_line=start_line,
                        end_line=end_line,
                        code=code_text,
                        docstring=docstring,
                        context_prefix=f"Class: {parent_class}" if parent_class else None,
                    )
                )

            for child in node.children:
                traverse(child, parent_class=parent_class)

        traverse(tree.root_node)

        if not chunks:
            chunks = self.create_fallback_chunks(source_bytes, file_path, repo_name)

        return chunks
