"""Tree-sitter AST parser for C source code."""

from typing import List, Optional
from tree_sitter import Node, Tree
from app.models.code_chunk import CodeChunk, ChunkType
from app.parsing.languages.base import BaseLanguageParser


class CParser(BaseLanguageParser):
    """AST parser for C extracting functions, structs, and type definitions."""

    def __init__(self):
        super().__init__("c")

    def _get_identifier_from_declarator(self, declarator_node: Optional[Node], source_bytes: bytes) -> Optional[str]:
        if not declarator_node:
            return None
        if declarator_node.type in {"identifier", "type_identifier"}:
            return self.get_node_text(declarator_node, source_bytes)
        for child in declarator_node.children:
            res = self._get_identifier_from_declarator(child, source_bytes)
            if res:
                return res
        return None

    def extract_chunks(
        self,
        tree: Tree,
        source_bytes: bytes,
        file_path: str,
        repo_name: str,
    ) -> List[CodeChunk]:
        chunks: List[CodeChunk] = []

        def traverse(node: Node):
            # 1. Function Definition
            if node.type == "function_definition":
                declarator = None
                for child in node.children:
                    if child.type in {"function_declarator", "declarator", "pointer_declarator"}:
                        declarator = child
                        break

                func_name = self._get_identifier_from_declarator(declarator, source_bytes) or "anonymous_function"
                docstring = self.get_preceding_comment(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, func_name)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        repo_name=repo_name,
                        file_path=file_path,
                        language=self.language_name,
                        chunk_type=ChunkType.FUNCTION,
                        symbol_name=func_name,
                        start_line=start_line,
                        end_line=end_line,
                        code=code_text,
                        docstring=docstring,
                        context_prefix=None,
                    )
                )

            # 2. Struct Specifier & Type Definitions
            elif node.type in {"struct_specifier", "type_definition"}:
                name_node = None
                for child in node.children:
                    if child.type in {"type_identifier", "identifier"}:
                        name_node = child
                        break

                type_name = self.get_node_text(name_node, source_bytes) if name_node else "anonymous_struct"
                docstring = self.get_preceding_comment(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, type_name)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        repo_name=repo_name,
                        file_path=file_path,
                        language=self.language_name,
                        chunk_type=ChunkType.STRUCT,
                        symbol_name=type_name,
                        start_line=start_line,
                        end_line=end_line,
                        code=code_text,
                        docstring=docstring,
                        context_prefix=None,
                    )
                )

            for child in node.children:
                traverse(child)

        traverse(tree.root_node)

        if not chunks:
            chunks = self.create_fallback_chunks(source_bytes, file_path, repo_name)

        return chunks
