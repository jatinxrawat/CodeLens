"""CLI tool for training, evaluating, and tracking ML models in the Code Intelligence Engine."""

import argparse
import sys
import json
from pathlib import Path

from app.ml.dataset.dataset_generator import RankingDatasetGenerator
from app.ml.dataset.maintainability_dataset import MaintainabilityDatasetGenerator
from app.ml.ranking.trainer import RankerTrainer
from app.ml.ranking.evaluator import RankingEvaluator
from app.ml.ranking.ablation import RankingAblationStudy
from app.ml.maintainability.trainer import MaintainabilityTrainer
from app.ml.maintainability.evaluator import MaintainabilityEvaluator
from app.ml.tracking.experiment_tracker import experiment_tracker
from app.ml.tracking.model_registry import model_registry
from app.ml.failure_analysis.failure_analyzer import FailureAnalyzer
from app.services.repository_service import repository_service


def handle_dataset_build(args):
    print("=== Building ML Datasets with Strict Repository Splits ===")
    
    # 1. Ranking Dataset
    print("\n1. Generating Code Retrieval Ranking Dataset...")
    rg = RankingDatasetGenerator(random_seed=42)
    ranking_ds = rg.build_dataset()
    r_path = rg.save_dataset(ranking_ds)
    print(f"✓ Saved Ranking Dataset: {r_path}")
    print(f"  Total samples: {ranking_ds.total_samples}")
    print(f"  Train repos: {ranking_ds.train_repositories}")
    print(f"  Val repos:   {ranking_ds.val_repositories}")
    print(f"  Test repos:  {ranking_ds.test_repositories}")

    # 2. Maintainability Dataset
    print("\n2. Generating Code Maintainability Dataset...")
    mg = MaintainabilityDatasetGenerator(random_seed=42)
    maint_ds = mg.build_dataset()
    m_path = mg.save_dataset(maint_ds)
    print(f"✓ Saved Maintainability Dataset: {m_path}")
    print(f"  Total samples: {maint_ds.total_samples}")
    print(f"  Class distribution: {maint_ds.statistics.get('class_distribution')}")


def handle_train_ranker(args):
    print("=== Training Code Relevance Ranker Model ===")
    rg = RankingDatasetGenerator(random_seed=42)
    dataset = rg.build_dataset()

    trainer = RankerTrainer(
        model_type="hist_gbdt",
        n_estimators=100,
        learning_rate=0.05,
        max_depth=4,
        random_seed=42,
    )
    ranker, val_metrics = trainer.train(dataset)

    # Save to registry
    artifact_path = model_registry.register_ranker_model(
        model=ranker,
        version="v1",
        metrics=val_metrics,
        config={"n_estimators": 100, "learning_rate": 0.05, "max_depth": 4},
    )
    print(f"✓ Model registered at: {artifact_path}")

    # Log experiment
    exp = experiment_tracker.log_experiment(
        model_name="retrieval_ranker",
        model_version="v1",
        hyperparameters={"n_estimators": 100, "learning_rate": 0.05, "max_depth": 4},
        dataset_info=dataset.statistics,
        metrics=val_metrics,
        notes="GBDT Code Relevance Ranker with 13 features",
    )
    print(f"✓ Logged Experiment: {exp['experiment_id']}")
    print("\nValidation Metrics:")
    print(json.dumps(val_metrics, indent=2))


def handle_train_maintainability(args):
    print("=== Training Code Maintainability Risk Model ===")
    mg = MaintainabilityDatasetGenerator(random_seed=42)
    dataset = mg.build_dataset()

    trainer = MaintainabilityTrainer(
        model_type="hist_gbdt",
        n_estimators=100,
        learning_rate=0.05,
        max_depth=4,
        random_seed=42,
    )
    model, eval_metrics = trainer.train(dataset)

    artifact_path = model_registry.register_maintainability_model(
        model=model,
        version="v1",
        metrics=eval_metrics,
        config={"n_estimators": 100, "learning_rate": 0.05, "max_depth": 4},
    )
    print(f"✓ Model registered at: {artifact_path}")

    exp = experiment_tracker.log_experiment(
        model_name="maintainability",
        model_version="v1",
        hyperparameters={"n_estimators": 100, "learning_rate": 0.05, "max_depth": 4},
        dataset_info=dataset.statistics,
        metrics=eval_metrics,
        notes="Multi-class Maintainability Risk GBDT Classifier",
    )
    print(f"✓ Logged Experiment: {exp['experiment_id']}")
    print("\nTest Evaluation Metrics:")
    print(json.dumps(eval_metrics, indent=2))


def handle_compare(args):
    print("=== Baseline Retrieval vs Trained ML Ranker Comparison ===")
    rg = RankingDatasetGenerator(random_seed=42)
    dataset = rg.build_dataset()

    ranker = model_registry.get_active_ranker()
    if not ranker:
        print("Training active ranker first...")
        trainer = RankerTrainer()
        ranker, _ = trainer.train(dataset)
        model_registry.register_ranker_model(ranker, "v1")

    evaluator = RankingEvaluator(ranker_model=ranker)
    comparisons = evaluator.compare_all_baselines(dataset)

    print("\n" + "="*80)
    print(f"{'Method':<20} | {'Recall@1':<10} | {'Recall@5':<10} | {'MRR':<10} | {'NDCG@5':<10} | {'Latency':<10}")
    print("-" * 80)
    for c in comparisons:
        print(f"{c['method']:<20} | {c['recall_at_1']:<10.4f} | {c['recall_at_5']:<10.4f} | {c['mrr']:<10.4f} | {c['ndcg_at_5']:<10.4f} | {c['avg_latency_ms']:<8.2f} ms")
    print("="*80)


def handle_ablation(args):
    print("=== Feature Ablation Study ===")
    rg = RankingDatasetGenerator(random_seed=42)
    dataset = rg.build_dataset()

    ablation = RankingAblationStudy()
    results = ablation.run_ablation(dataset)

    print("\n" + "="*80)
    print(f"{'Feature Group':<32} | {'Feat Count':<10} | {'Recall@5':<10} | {'MRR':<10} | {'NDCG@5':<10}")
    print("-" * 80)
    for r in results:
        print(f"{r['feature_group']:<32} | {r['feature_count']:<10} | {r['recall_at_5']:<10.4f} | {r['mrr']:<10.4f} | {r['ndcg_at_5']:<10.4f}")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description="Local AI Code Intelligence Engine - ML CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # dataset build
    ds_parser = subparsers.add_parser("dataset", help="Dataset management")
    ds_sub = ds_parser.add_subparsers(dest="dataset_action")
    ds_build = ds_sub.add_parser("build", help="Build training and test datasets")

    # train
    train_parser = subparsers.add_parser("train", help="Train models")
    train_parser.add_argument("target", choices=["ranker", "maintainability"], help="Model to train")

    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate models")
    eval_parser.add_argument("target", choices=["ranker", "maintainability"], help="Model to evaluate")

    # compare
    subparsers.add_parser("compare", help="Compare baselines against trained ML ranker")

    # ablation
    subparsers.add_parser("ablation", help="Run feature ablation study")

    args = parser.parse_args()

    if args.command == "dataset":
        handle_dataset_build(args)
    elif args.command == "train":
        if args.target == "ranker":
            handle_train_ranker(args)
        elif args.target == "maintainability":
            handle_train_maintainability(args)
    elif args.command == "evaluate":
        if args.target == "ranker":
            handle_compare(args)
        elif args.target == "maintainability":
            handle_train_maintainability(args)
    elif args.command == "compare":
        handle_compare(args)
    elif args.command == "ablation":
        handle_ablation(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
