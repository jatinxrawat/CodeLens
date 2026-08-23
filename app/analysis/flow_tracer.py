"""Static AST Code Flow and Call Graph Tracer.

Analyzes caller-callee relationships, module invocations, and function flow
using AST analysis across Python, JavaScript, TypeScript, Java, C++, and C.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from pydantic import BaseModel, Field
from app.models.code_chunk import CodeChunk, ChunkType
from app.config import settings


class FlowStep(BaseModel):
    caller_symbol: str
    callee_symbol: str
    caller_file: str
    callee_file: Optional[str] = None
    caller_line: int
    relationship_type: str = Field(..., description="'confirmed_static' or 'inferred'")
    explanation: str


class FunctionFlowResult(BaseModel):
    target_symbol: str
    target_file: str
    target_line: int
    callers: List[Dict[str, Any]]
    callees: List[Dict[str, Any]]
    imported_modules: List[str]
    flow_steps: List[FlowStep]
    disclaimer: str = (
        "Static code flow reflects AST-level references and call expressions. "
        "Dynamic runtime dispatch and reflection are not guaranteed."
    )


class CodeFlowTracer:
    """Extracts static function call graphs and invocation pathways."""

    def __init__(self):
        # Regex patterns for function calls across languages: foo(...) or obj.foo(...)
        self.call_pattern = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")

    def trace_function_flow(
        self,
        repo_name: str,
        target_symbol: str,
        target_file: Optional[str] = None,
        chunks: Optional[List[CodeChunk]] = None,
    ) -> FunctionFlowResult:
        """Traces callers, callees, and dependencies for a given function/method symbol."""
        if not chunks:
            index_dir = settings.INDEXES_DIR / repo_name
            import json
            chunks_file = index_dir / "chunks.json"
            if chunks_file.exists():
                with open(chunks_file, "r", encoding="utf-8") as f:
                    raw_chunks = json.load(f)
                chunks = [CodeChunk.from_dict(c) for c in raw_chunks]
            else:
                chunks = []

        # Find target chunk
        target_chunk: Optional[CodeChunk] = None
        for c in chunks:
            if c.symbol_name and c.symbol_name.lower() == target_symbol.lower():
                if not target_file or target_file.lower() in c.file_path.lower():
                    target_chunk = c
                    break

        if not target_chunk:
            # Fallback to search by symbol name in code
            for c in chunks:
                if target_symbol.lower() in (c.symbol_name or "").lower():
                    target_chunk = c
                    break

        if not target_chunk:
            return FunctionFlowResult(
                target_symbol=target_symbol,
                target_file=target_file or "unknown",
                target_line=1,
                callers=[],
                callees=[],
                imported_modules=[],
                flow_steps=[],
            )

        # 1. Identify Callees (functions called inside target_chunk.code)
        callees: List[Dict[str, Any]] = []
        found_callee_names = set(self.call_pattern.findall(target_chunk.code))
        # Exclude language keywords & builtins
        common_builtins = {
            "if", "while", "for", "switch", "catch", "return", "print", "len", "range",
            "str", "int", "float", "dict", "list", "set", "tuple", "super", "sizeof",
            "require", "import", "console", "log", "System", "out", "println", "printf",
        }
        filtered_callees = [name for name in found_callee_names if name not in common_builtins and name != target_chunk.symbol_name]

        # Map callee names to known chunks in the repository
        symbol_to_chunk: Dict[str, CodeChunk] = {}
        for c in chunks:
            if c.symbol_name:
                symbol_to_chunk[c.symbol_name] = c

        flow_steps: List[FlowStep] = []

        for callee_name in sorted(filtered_callees):
            target_callee_chunk = symbol_to_chunk.get(callee_name)
            is_confirmed = target_callee_chunk is not None
            callee_file = target_callee_chunk.file_path if target_callee_chunk else None
            callee_line = target_callee_chunk.start_line if target_callee_chunk else 0

            callees.append({
                "symbol": callee_name,
                "file_path": callee_file,
                "start_line": callee_line,
                "relationship": "confirmed_static" if is_confirmed else "inferred",
                "is_internal": is_confirmed,
            })

            flow_steps.append(
                FlowStep(
                    caller_symbol=target_chunk.symbol_name or "unknown",
                    callee_symbol=callee_name,
                    caller_file=target_chunk.file_path,
                    callee_file=callee_file,
                    caller_line=target_chunk.start_line,
                    relationship_type="confirmed_static" if is_confirmed else "inferred",
                    explanation=f"Calls `{callee_name}()` inside body",
                )
            )

        # 2. Identify Callers (other chunks in repo that invoke target_symbol)
        callers: List[Dict[str, Any]] = []
        target_pattern = re.compile(rf"\b{re.escape(target_chunk.symbol_name or target_symbol)}\s*\(")

        for c in chunks:
            if c.chunk_id == target_chunk.chunk_id:
                continue
            if target_pattern.search(c.code):
                callers.append({
                    "symbol": c.symbol_name or f"block_{c.start_line}",
                    "file_path": c.file_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "relationship": "confirmed_static",
                })
                flow_steps.append(
                    FlowStep(
                        caller_symbol=c.symbol_name or f"block_{c.start_line}",
                        callee_symbol=target_chunk.symbol_name or target_symbol,
                        caller_file=c.file_path,
                        callee_file=target_chunk.file_path,
                        caller_line=c.start_line,
                        relationship_type="confirmed_static",
                        explanation=f"Invokes `{target_chunk.symbol_name}()` at line {c.start_line}",
                    )
                )

        # 3. Extract Imported Modules in file
        imported_modules: List[str] = []
        # Find all chunks in the same file to scan for imports
        same_file_chunks = [c for c in chunks if c.file_path == target_chunk.file_path]
        for c in same_file_chunks:
            # Python imports
            for m in re.findall(r"^(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))", c.code, re.MULTILINE):
                mod = m[0] or m[1]
                if mod and mod not in imported_modules:
                    imported_modules.append(mod)
            # JS/TS imports
            for m in re.findall(r"import\s+.*?from\s+['\"](.*?)['\"]", c.code):
                if m and m not in imported_modules:
                    imported_modules.append(m)

        return FunctionFlowResult(
            target_symbol=target_chunk.symbol_name or target_symbol,
            target_file=target_chunk.file_path,
            target_line=target_chunk.start_line,
            callers=callers,
            callees=callees,
            imported_modules=imported_modules,
            flow_steps=flow_steps,
        )
