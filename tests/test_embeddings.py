"""Unit tests for local embedding generation."""

import numpy as np
from app.embeddings.embedding_model import SentenceTransformerEmbeddingModel


def test_embedding_dimension_and_normalization():
    model = SentenceTransformerEmbeddingModel()
    assert model.dimension == 384
    assert "MiniLM" in model.model_name

    texts = [
        "def authenticate_user(username, password): pass",
        "class OrderService { void process() {} }",
    ]
    embeddings = model.encode(texts, batch_size=2)

    assert embeddings.shape == (2, 384)
    assert embeddings.dtype == np.float32

    # Verify L2 normalization (norm should equal 1.0)
    for vec in embeddings:
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-4


def test_encode_single():
    model = SentenceTransformerEmbeddingModel()
    vec = model.encode_single("void* pool_allocate(size_t size);")
    assert vec.shape == (384,)
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-4
