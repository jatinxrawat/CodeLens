"""Tree-sitter AST parser for TypeScript source code."""

from typing import List, Optional
from tree_sitter import Node, Tree
from app.models.code_chunk import CodeChunk, ChunkType
from app.parsing.languages.base import BaseLanguageParser


class TypeScriptParser(BaseLanguageParser):
    """AST parser for TypeScript extracting functions, interfaces, types, classes, and methods."""

    def __init__(self):
        super().__init__("typescript")

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
            actual_node = node
            if node.type in {"export_statement", "export_default_declaration"}:
                declaration = self._get_node_by_type(node, "declaration")
                if declaration:
                    actual_node = declaration
                else:
                    for child in node.children:
                        if child.type in {
                            "function_declaration",
                            "class_declaration",
                            "interface_declaration",
                            "type_alias_declaration",
                            "enum_declaration",
                            "lexical_declaration",
                            "variable_declaration",
                        }:
                            actual_node = child
                            break

            # 1. Functions
            if actual_node.type in {"function_declaration", "generator_function_declaration"}:
                name_node = self._get_node_by_type(actual_node, "identifier")
                name = self.get_node_text(name_node, source_bytes) if name_node else "anonymous_function"
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
                        chunk_type=ChunkType.METHOD if parent_class else ChunkType.FUNCTION,
                        symbol_name=symbol,
                        start_line=start_line,
                        end_line=end_line,
                        code=code_text,
                        docstring=docstring,
                        context_prefix=f"Class: {parent_class}" if parent_class else None,
                    )
                )

            # 2. Variable Arrow Functions (const calculateTotal = (a, b): number => ...)
            elif actual_node.type in {"lexical_declaration", "variable_declaration"}:
                for declarator in actual_node.children:
                    if declarator.type == "variable_declarator":
                        name_node = self._get_node_by_type(declarator, "identifier")
                        value_node = None
                        for child in declarator.children:
                            if child.type in {"arrow_function", "function"}:
                                value_node = child
                                break

                        if name_node and value_node:
                            name = self.get_node_text(name_node, source_bytes)
                            docstring = self._extract_comments(node, source_bytes)
                            code_text = self.get_node_text(node, source_bytes)
                            start_line = node.start_point[0] + 1
                            end_line = node.end_point[0] + 1

                            chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, name)
                            chunks.append(
                                CodeChunk(
                                    chunk_id=chunk_id,
                                    repo_name=repo_name,
                                    file_path=file_path,
                                    language=self.language_name,
                                    chunk_type=ChunkType.FUNCTION,
                                    symbol_name=name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    code=code_text,
                                    docstring=docstring,
                                    context_prefix=None,
                                )
                            )

            # 3. Interfaces & Type Aliases
            elif actual_node.type in {"interface_declaration", "type_alias_declaration"}:
                name_node = self._get_node_by_type(actual_node, "type_identifier")
                name = self.get_node_text(name_node, source_bytes) if name_node else "AnonymousInterface"
                docstring = self._extract_comments(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, name)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        repo_name=repo_name,
                        file_path=file_path,
                        language=self.language_name,
                        chunk_type=ChunkType.INTERFACE,
                        symbol_name=name,
                        start_line=start_line,
                        end_line=end_line,
                        code=code_text,
                        docstring=docstring,
                        context_prefix=None,
                    )
                )

            # 4. Classes
            elif actual_node.type == "class_declaration":
                name_node = self._get_node_by_type(actual_node, "type_identifier") or self._get_node_by_type(actual_node, "identifier")
                class_name = self.get_node_text(name_node, source_bytes) if name_node else "AnonymousClass"
                docstring = self._extract_comments(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, class_name)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        repo_name=repo_name,
                        file_path=file_path,
                        language=self.language_name,
                        chunk_type=ChunkType.CLASS,
                        symbol_name=class_name,
                        start_line=start_line,
                        end_line=end_line,
                        code=code_text,
                        docstring=docstring,
                        context_prefix=None,
                    )
                )

                class_body = self._get_node_by_type(actual_node, "class_body")
                if class_body:
                    for child in class_body.children:
                        traverse(child, parent_class=class_name)
                return

            # 5. Method Definitions
            elif actual_node.type == "method_definition":
                name_node = self._get_node_by_type(actual_node, "property_identifier")
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
