"""Unit tests for static code flow and call graph tracer."""

from app.analysis.flow_tracer import CodeFlowTracer
from app.models.code_chunk import CodeChunk, ChunkType


def test_flow_tracer_basic():
    chunks = [
        CodeChunk(
            chunk_id="c1",
            repo_name="demo",
            file_path="src/service.py",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            symbol_name="process_order",
            start_line=10,
            end_line=25,
            code="def process_order(order_id):\n    validate_order(order_id)\n    charge_card(order_id)",
        ),
        CodeChunk(
            chunk_id="c2",
            repo_name="demo",
            file_path="src/validator.py",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            symbol_name="validate_order",
            start_line=1,
            end_line=10,
            code="def validate_order(order_id):\n    check_stock()",
        ),
    ]

    tracer = CodeFlowTracer()
    res = tracer.trace_function_flow("demo", "process_order", chunks=chunks)

    assert res.target_symbol == "process_order"
    assert res.target_file == "src/service.py"
    # Callees should include validate_order and charge_card
    callee_names = [c["symbol"] for c in res.callees]
    assert "validate_order" in callee_names
    assert "charge_card" in callee_names

    # Check caller relationship on validate_order
    res_val = tracer.trace_function_flow("demo", "validate_order", chunks=chunks)
    assert len(res_val.callers) >= 1
    assert res_val.callers[0]["symbol"] == "process_order"
