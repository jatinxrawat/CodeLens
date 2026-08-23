"""Tree-sitter AST parser for Python source code."""

from typing import List, Optional
from tree_sitter import Node, Tree
from app.models.code_chunk import CodeChunk, ChunkType
from app.parsing.languages.base import BaseLanguageParser


class PythonParser(BaseLanguageParser):
    """AST parser for Python extracting functions, methods, classes, and docstrings."""

    def __init__(self):
        super().__init__("python")

    def _extract_docstring(self, body_node: Optional[Node], source_bytes: bytes) -> Optional[str]:
        """Extracts the first string expression statement within a function or class body as docstring."""
        if not body_node:
            return None
        for child in body_node.children:
            if child.type == "expression_statement":
                for expr in child.children:
                    if expr.type == "string":
                        doc = self.get_node_text(expr, source_bytes)
                        # Strip triple quotes if present
                        if doc.startswith(('"""', "'''")) and len(doc) >= 6:
                            return doc[3:-3].strip()
                        elif doc.startswith(('"', "'")) and len(doc) >= 2:
                            return doc[1:-1].strip()
                        return doc.strip()
            elif child.type not in {"comment", "newline", "indent"}:
                break
        return None

    def _get_identifier(self, node: Node, source_bytes: bytes) -> Optional[str]:
        """Finds the identifier node name."""
        for child in node.children:
            if child.type == "identifier":
                return self.get_node_text(child, source_bytes)
        return None

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
            # Handle decorated definitions (@decorator\ndef foo(): ...)
            if node.type == "decorated_definition":
                for child in node.children:
                    if child.type in {"function_definition", "async_function_definition", "class_definition"}:
                        actual_node = child
                        break

            if actual_node.type in {"function_definition", "async_function_definition"}:
                name = self._get_identifier(actual_node, source_bytes)
                body = None
                for child in actual_node.children:
                    if child.type == "block":
                        body = child
                        break

                docstring = self._extract_docstring(body, source_bytes) or self.get_preceding_comment(node, source_bytes)
                code_text = self.get_node_text(node, source_bytes)  # includes decorators
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                chunk_type = ChunkType.METHOD if parent_class else ChunkType.FUNCTION
                symbol = f"{parent_class}.{name}" if parent_class and name else (name or "anonymous_function")

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
                        context_prefix=f"Class: {parent_class}" if parent_class else None,
                    )
                )

            elif actual_node.type == "class_definition":
                class_name = self._get_identifier(actual_node, source_bytes) or "AnonymousClass"
                body = None
                for child in actual_node.children:
                    if child.type == "block":
                        body = child
                        break

                docstring = self._extract_docstring(body, source_bytes) or self.get_preceding_comment(node, source_bytes)
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

                # Traverse children inside class body to extract methods
                if body:
                    for child in body.children:
                        traverse(child, parent_class=class_name)
                return

            # Continue traversing children for top-level modules
            for child in node.children:
                traverse(child, parent_class=parent_class)

        traverse(tree.root_node)

        # If no AST symbols found, fallback to chunking
        if not chunks:
            chunks = self.create_fallback_chunks(source_bytes, file_path, repo_name)

        return chunks
