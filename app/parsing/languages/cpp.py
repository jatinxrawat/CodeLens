"""Tree-sitter AST parser for C++ source code."""

from typing import List, Optional
from tree_sitter import Node, Tree
from app.models.code_chunk import CodeChunk, ChunkType
from app.parsing.languages.base import BaseLanguageParser


class CppParser(BaseLanguageParser):
    """AST parser for C++ extracting functions, classes, structs, and methods."""

    def __init__(self):
        super().__init__("cpp")

    def _get_identifier_from_declarator(self, declarator_node: Optional[Node], source_bytes: bytes) -> Optional[str]:
        if not declarator_node:
            return None
        if declarator_node.type in {"identifier", "field_identifier", "type_identifier", "qualified_identifier", "destructor_name"}:
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

        def traverse(node: Node, parent_scope: Optional[str] = None):
            # 1. Functions and Methods
            if node.type == "function_definition":
                declarator = None
                for child in node.children:
                    if child.type in {"function_declarator", "declarator"}:
                        declarator = child
                        break

                func_name = self._get_identifier_from_declarator(declarator, source_bytes) or "anonymous_function"
                docstring = self.get_preceding_comment(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                symbol = f"{parent_scope}::{func_name}" if parent_scope else func_name

                chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, symbol)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        repo_name=repo_name,
                        file_path=file_path,
                        language=self.language_name,
                        chunk_type=ChunkType.METHOD if parent_scope else ChunkType.FUNCTION,
                        symbol_name=symbol,
                        start_line=start_line,
                        end_line=end_line,
                        code=code_text,
                        docstring=docstring,
                        context_prefix=f"Scope: {parent_scope}" if parent_scope else None,
                    )
                )

            # 2. Class and Struct Specifiers
            elif node.type in {"class_specifier", "struct_specifier"}:
                name_node = None
                for child in node.children:
                    if child.type == "type_identifier":
                        name_node = child
                        break

                type_name = self.get_node_text(name_node, source_bytes) if name_node else "AnonymousType"
                docstring = self.get_preceding_comment(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                symbol = f"{parent_scope}::{type_name}" if parent_scope else type_name

                chunk_type = ChunkType.CLASS if node.type == "class_specifier" else ChunkType.STRUCT
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
                        context_prefix=f"Parent: {parent_scope}" if parent_scope else None,
                    )
                )

                field_list = None
                for child in node.children:
                    if child.type == "field_declaration_list":
                        field_list = child
                        break
                if field_list:
                    for child in field_list.children:
                        traverse(child, parent_scope=symbol)
                return

            # 3. Namespace Definitions
            elif node.type == "namespace_definition":
                ns_name = None
                for child in node.children:
                    if child.type == "namespace_identifier":
                        ns_name = self.get_node_text(child, source_bytes)
                        break
                new_scope = f"{parent_scope}::{ns_name}" if (parent_scope and ns_name) else (ns_name or parent_scope)
                for child in node.children:
                    traverse(child, parent_scope=new_scope)
                return

            for child in node.children:
                traverse(child, parent_scope=parent_scope)

        traverse(tree.root_node)

        if not chunks:
            chunks = self.create_fallback_chunks(source_bytes, file_path, repo_name)

        return chunks
