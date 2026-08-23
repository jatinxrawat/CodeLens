"""Unit tests for Tree-sitter AST parsing across all 6 supported languages."""

from pathlib import Path
from app.parsing.parser import CodeParser
from app.models.code_chunk import ChunkType


def test_parse_python(code_parser: CodeParser, sample_repo_path: Path):
    py_file = sample_repo_path / "python" / "auth.py"
    chunks = code_parser.parse_file(py_file, "sample_repo", "python/auth.py")

    assert len(chunks) >= 3
    symbols = {c.symbol_name: c for c in chunks}

    # Should find class and methods / functions
    assert "UserSessionManager" in symbols
    assert symbols["UserSessionManager"].chunk_type == ChunkType.CLASS

    assert "login_user" in symbols
    assert symbols["login_user"].chunk_type == ChunkType.FUNCTION
    assert symbols["login_user"].start_line > 0
    assert symbols["login_user"].docstring is not None
    assert "Authenticates a user" in symbols["login_user"].docstring

    assert "verify_token" in symbols


def test_parse_javascript(code_parser: CodeParser, sample_repo_path: Path):
    js_file = sample_repo_path / "javascript" / "user.js"
    chunks = code_parser.parse_file(js_file, "sample_repo", "javascript/user.js")

    assert len(chunks) >= 3
    symbols = {c.symbol_name: c for c in chunks}

    assert "UserDatabase" in symbols
    assert "validateEmail" in symbols
    assert "registerUser" in symbols
    assert symbols["registerUser"].docstring is not None


def test_parse_typescript(code_parser: CodeParser, sample_repo_path: Path):
    ts_file = sample_repo_path / "typescript" / "payment.ts"
    chunks = code_parser.parse_file(ts_file, "sample_repo", "typescript/payment.ts")

    assert len(chunks) >= 2
    symbols = {c.symbol_name: c for c in chunks}

    assert "TransactionResult" in symbols or "PaymentGateway" in symbols
    assert "PaymentGateway" in symbols
    assert any(c.chunk_type == ChunkType.CLASS for c in chunks)


def test_parse_java(code_parser: CodeParser, sample_repo_path: Path):
    java_file = sample_repo_path / "java" / "OrderService.java"
    chunks = code_parser.parse_file(java_file, "sample_repo", "java/OrderService.java")

    assert len(chunks) >= 2
    symbols = {c.symbol_name: c for c in chunks}

    assert "OrderService" in symbols
    assert any("processOrder" in s for s in symbols)


def test_parse_cpp(code_parser: CodeParser, sample_repo_path: Path):
    cpp_file = sample_repo_path / "cpp" / "cache.cpp"
    chunks = code_parser.parse_file(cpp_file, "sample_repo", "cpp/cache.cpp")

    assert len(chunks) >= 1
    symbols = {c.symbol_name: c for c in chunks}

    assert "LRUCache" in symbols or any("LRUCache" in s for s in symbols)


def test_parse_c(code_parser: CodeParser, sample_repo_path: Path):
    c_file = sample_repo_path / "c" / "memory.c"
    chunks = code_parser.parse_file(c_file, "sample_repo", "c/memory.c")

    assert len(chunks) >= 2
    symbols = {c.symbol_name: c for c in chunks}

    assert "pool_allocate" in symbols
    assert "pool_free" in symbols


def test_chunk_embeddable_text(code_parser: CodeParser, sample_repo_path: Path):
    py_file = sample_repo_path / "python" / "auth.py"
    chunks = code_parser.parse_file(py_file, "sample_repo", "python/auth.py")
    login_chunk = next(c for c in chunks if c.symbol_name == "login_user")

    embed_text = login_chunk.get_embeddable_text()
    assert "File: python/auth.py" in embed_text
    assert "Function: login_user" in embed_text
    assert "Description:" in embed_text
    assert "def login_user" in embed_text
