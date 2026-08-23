"""API routes for Trainable ML Retrieval, Maintainability Risk Intelligence, and Experiment Analytics."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.ml.dataset.dataset_generator import RankingDatasetGenerator
from app.ml.dataset.maintainability_dataset import MaintainabilityDatasetGenerator
from app.ml.ranking.trainer import RankerTrainer
from app.ml.ranking.evaluator import RankingEvaluator
from app.ml.ranking.ablation import RankingAblationStudy
from app.ml.maintainability.trainer import MaintainabilityTrainer
from app.ml.maintainability.evaluator import MaintainabilityEvaluator
from app.ml.maintainability.explainer import MaintainabilityExplainer
from app.ml.failure_analysis.failure_analyzer import FailureAnalyzer
from app.ml.tracking.experiment_tracker import experiment_tracker
from app.ml.tracking.model_registry import model_registry
from app.models.code_chunk import CodeChunk
from app.services.repository_service import repository_service

router = APIRouter(prefix="/ml", tags=["Machine Learning & Risk Intelligence"])


class TrainRequest(BaseModel):
    n_estimators: int = 100
    learning_rate: float = 0.05
    max_depth: int = 4
    model_type: str = "hist_gbdt"


class PredictMaintainabilityRequest(BaseModel):
    repository_id: str
    chunk_id: str


@router.get("/dataset/stats")
def get_dataset_statistics() -> Dict[str, Any]:
    """Returns training/test dataset statistics across repositories."""
    rg = RankingDatasetGenerator(random_seed=42)
    ranking_ds = rg.build_dataset()

    mg = MaintainabilityDatasetGenerator(random_seed=42)
    maint_ds = mg.build_dataset()

    return {
        "ranking_dataset": ranking_ds.statistics,
        "maintainability_dataset": maint_ds.statistics,
        "repositories": {
            "train": ranking_ds.train_repositories,
            "validation": ranking_ds.val_repositories,
            "test": ranking_ds.test_repositories,
        },
    }


@router.post("/ranker/train")
def train_ranker_model(request: TrainRequest) -> Dict[str, Any]:
    """Trains the Code Relevance Ranker model."""
    rg = RankingDatasetGenerator(random_seed=42)
    dataset = rg.build_dataset()

    trainer = RankerTrainer(
        model_type=request.model_type,
        n_estimators=request.n_estimators,
        learning_rate=request.learning_rate,
        max_depth=request.max_depth,
        random_seed=42,
    )
    ranker, val_metrics = trainer.train(dataset)

    artifact_path = model_registry.register_ranker_model(
        model=ranker,
        version="v1",
        metrics=val_metrics,
        config=request.model_dump(),
    )

    exp = experiment_tracker.log_experiment(
        model_name="retrieval_ranker",
        model_version="v1",
        hyperparameters=request.model_dump(),
        dataset_info=dataset.statistics,
        metrics=val_metrics,
        notes="GBDT Code Relevance Ranker",
    )

    return {
        "status": "success",
        "model_version": "v1",
        "artifact_path": str(artifact_path),
        "experiment_id": exp["experiment_id"],
        "metrics": val_metrics,
    }


@router.get("/ranker/baselines")
def get_retrieval_baselines() -> List[Dict[str, Any]]:
    """Evaluates and compares BM25, Vector, Hybrid, and Hybrid + ML Ranker."""
    rg = RankingDatasetGenerator(random_seed=42)
    dataset = rg.build_dataset()

    ranker = model_registry.get_active_ranker()
    if not ranker:
        trainer = RankerTrainer()
        ranker, _ = trainer.train(dataset)
        model_registry.register_ranker_model(ranker, "v1")

    evaluator = RankingEvaluator(ranker_model=ranker)
    return evaluator.compare_all_baselines(dataset)


@router.get("/ranker/ablation")
def get_ranker_ablation() -> List[Dict[str, Any]]:
    """Runs feature ablation experiments across feature groups."""
    rg = RankingDatasetGenerator(random_seed=42)
    dataset = rg.build_dataset()

    ablation = RankingAblationStudy()
    return ablation.run_ablation(dataset)


@router.post("/maintainability/train")
def train_maintainability_model(request: TrainRequest) -> Dict[str, Any]:
    """Trains the Code Maintainability Risk Model."""
    mg = MaintainabilityDatasetGenerator(random_seed=42)
    dataset = mg.build_dataset()

    trainer = MaintainabilityTrainer(
        model_type=request.model_type,
        n_estimators=request.n_estimators,
        learning_rate=request.learning_rate,
        max_depth=request.max_depth,
        random_seed=42,
    )
    model, eval_metrics = trainer.train(dataset)

    artifact_path = model_registry.register_maintainability_model(
        model=model,
        version="v1",
        metrics=eval_metrics,
        config=request.model_dump(),
    )

    exp = experiment_tracker.log_experiment(
        model_name="maintainability",
        model_version="v1",
        hyperparameters=request.model_dump(),
        dataset_info=dataset.statistics,
        metrics=eval_metrics,
        notes="Maintainability Risk Classifier",
    )

    return {
        "status": "success",
        "model_version": "v1",
        "artifact_path": str(artifact_path),
        "experiment_id": exp["experiment_id"],
        "metrics": eval_metrics,
    }


@router.get("/maintainability/metrics")
def get_maintainability_metrics() -> Dict[str, Any]:
    """Retrieves active maintainability model test performance and confusion matrix."""
    mg = MaintainabilityDatasetGenerator(random_seed=42)
    dataset = mg.build_dataset()

    model = model_registry.get_active_maintainability()
    if not model:
        trainer = MaintainabilityTrainer()
        model, _ = trainer.train(dataset)
        model_registry.register_maintainability_model(model, "v1")

    evaluator = MaintainabilityEvaluator(model)
    return evaluator.evaluate(dataset)


@router.post("/maintainability/predict")
def predict_chunk_maintainability(request: PredictMaintainabilityRequest) -> Dict[str, Any]:
    """Predicts maintainability risk and explains contributing metrics for a specific code chunk."""
    model = model_registry.get_active_maintainability()
    if not model:
        mg = MaintainabilityDatasetGenerator(random_seed=42)
        dataset = mg.build_dataset()
        trainer = MaintainabilityTrainer()
        model, _ = trainer.train(dataset)
        model_registry.register_maintainability_model(model, "v1")

    raw_chunks = repository_service.get_chunks_for_repository(request.repository_id)
    target_chunk_dict = next((c for c in raw_chunks if c.get("chunk_id") == request.chunk_id), None)
    if not target_chunk_dict:
        raise HTTPException(status_code=404, detail="Code chunk not found")

    chunk = CodeChunk.from_dict(target_chunk_dict)
    explainer = MaintainabilityExplainer(model)
    return explainer.explain_chunk(chunk)


@router.get("/experiments")
def list_experiments(model_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all tracked ML experiments and metrics."""
    return experiment_tracker.list_experiments(model_name=model_name)


@router.get("/failures")
def get_failure_analysis() -> Dict[str, Any]:
    """Returns failure diagnostic reports for ranking and maintainability models."""
    rg = RankingDatasetGenerator(random_seed=42)
    ranking_ds = rg.build_dataset()

    mg = MaintainabilityDatasetGenerator(random_seed=42)
    maint_ds = mg.build_dataset()

    ranker = model_registry.get_active_ranker()
    maint_model = model_registry.get_active_maintainability()

    analyzer = FailureAnalyzer(ranker_model=ranker, maintainability_model=maint_model)
    return {
        "ranking_failures": analyzer.analyze_ranking_failures(ranking_ds),
        "maintainability_failures": analyzer.analyze_maintainability_failures(maint_ds),
    }
