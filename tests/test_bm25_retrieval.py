"""Unit tests for BM25 code tokenization and lexical retrieval."""

from app.models.code_chunk import CodeChunk, ChunkType
from app.retrieval.bm25_store import BM25Store, BM25CodeTokenizer


def test_code_tokenizer_camel_snake_case():
    tokens = BM25CodeTokenizer.tokenize("def loginUser_account(auth_token): pass")
    assert "login" in tokens
    assert "user" in tokens
    assert "account" in tokens
    assert "auth" in tokens
    assert "token" in tokens


def test_bm25_store_search():
    chunks = [
        CodeChunk(
            chunk_id="c1",
            repo_name="demo",
            file_path="src/auth.py",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            symbol_name="login_user",
            start_line=1,
            end_line=10,
            code="def login_user(username, password):\n    validate_credentials()",
        ),
        CodeChunk(
            chunk_id="c2",
            repo_name="demo",
            file_path="src/payment.py",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            symbol_name="process_card_payment",
            start_line=1,
            end_line=10,
            code="def process_card_payment(card_number, amount):\n    stripe_charge()",
        ),
    ]

    store = BM25Store()
    store.add_chunks(chunks)

    # Search for login
    results = store.search("login_user username", top_k=2)
    assert len(results) >= 1
    assert results[0].chunk.symbol_name == "login_user"

    # Search for card payment
    results = store.search("process_card_payment stripe", top_k=2)
    assert len(results) >= 1
    assert results[0].chunk.symbol_name == "process_card_payment"
