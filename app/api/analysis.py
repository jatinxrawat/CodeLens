"""Static Code Intelligence & Analysis API router."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas.analysis import ImpactRequest
from app.analysis.flow_tracer import CodeFlowTracer, FunctionFlowResult
from app.analysis.impact_analyzer import ImpactAnalyzer, ImpactAnalysisResult
from app.analysis.architecture_engine import ArchitectureEngine, ArchitectureReport
from app.analysis.quality_metrics import QualityMetricsCalculator, RepositoryQualityMetrics
from app.analysis.code_smells import CodeSmellDetector, CodeSmellReport
from app.analysis.security_scanner import SecurityScanner, SecurityScanReport

router = APIRouter()

flow_tracer = CodeFlowTracer()
impact_analyzer = ImpactAnalyzer()
arch_engine = ArchitectureEngine()
quality_calc = QualityMetricsCalculator()
smell_detector = CodeSmellDetector()
security_scanner = SecurityScanner()


@router.get("/{repository_id}/architecture", response_model=ArchitectureReport)
async def get_architecture_analysis(repository_id: str):
    """Infers architectural layers and subsystem topology for a repository."""
    try:
        return arch_engine.infer_architecture(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Architecture analysis failed: {e}")


@router.get("/{repository_id}/flow", response_model=FunctionFlowResult)
async def get_function_flow(
    repository_id: str,
    symbol: str = Query(..., description="Function/method name"),
    file_path: Optional[str] = Query(None, description="Optional target file path"),
):
    """Traces static caller/callee execution pathways and dependency flow."""
    try:
        return flow_tracer.trace_function_flow(repository_id, symbol, file_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flow tracing failed: {e}")


@router.post("/{repository_id}/impact", response_model=ImpactAnalysisResult)
async def get_impact_analysis(repository_id: str, request: ImpactRequest):
    """Calculates potential blast radius and affected files for a file/symbol change."""
    try:
        return impact_analyzer.analyze_impact(repository_id, request.target)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impact analysis failed: {e}")


@router.get("/{repository_id}/quality", response_model=RepositoryQualityMetrics)
async def get_quality_metrics(repository_id: str):
    """Computes cyclomatic complexity, nesting depth, and maintainability metrics."""
    try:
        return quality_calc.analyze_repository(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality analysis failed: {e}")


@router.get("/{repository_id}/smells", response_model=CodeSmellReport)
async def get_code_smells(repository_id: str):
    """Detects rule-based maintainability risks and code smells."""
    try:
        return smell_detector.detect_smells(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code smell scan failed: {e}")


@router.get("/{repository_id}/security", response_model=SecurityScanReport)
async def get_security_scan(repository_id: str):
    """Scans for static security patterns and risk indicators."""
    try:
        return security_scanner.scan_repository(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security scan failed: {e}")
