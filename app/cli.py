"""Command Line Interface (CLI) for Local AI Code Intelligence Engine."""

import argparse
import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box

from app.config import settings
from app.pipeline import IngestionPipeline
from app.retrieval.search import SearchEngine
from app.retrieval.vector_store import FaissVectorStore
from app.evaluation.evaluator import CodeRetrievalEvaluator

console = Console()


def get_available_indexes() -> list[str]:
    """Returns a list of repository names that have been indexed."""
    if not settings.INDEXES_DIR.exists():
        return []
    return [
        d.name
        for d in settings.INDEXES_DIR.iterdir()
        if d.is_dir() and (d / "index.faiss").exists()
    ]


def handle_ingest(args):
    """Clones and indexes a remote Git repository."""
    pipeline = IngestionPipeline()
    try:
        metadata = pipeline.run_remote(args.git_url, force_reclone=args.force)
        print_index_stats(metadata.repo_name)
    except Exception as e:
        console.print(f"[bold red]Error during ingestion:[/bold red] {e}")
        sys.exit(1)


def handle_ingest_local(args):
    """Indexes a local repository directory."""
    local_path = Path(args.repo_path).resolve()
    if not local_path.exists():
        console.print(f"[bold red]Error:[/bold red] Path does not exist: {local_path}")
        sys.exit(1)

    pipeline = IngestionPipeline()
    try:
        metadata = pipeline.run_local(local_path)
        print_index_stats(metadata.repo_name)
    except Exception as e:
        console.print(f"[bold red]Error during ingestion:[/bold red] {e}")
        sys.exit(1)


def handle_search(args):
    """Performs semantic search across indexed code chunks."""
    indexes = get_available_indexes()
    if not indexes:
        console.print("[bold red]No indexed repositories found.[/bold red] Please run 'ingest' or 'ingest-local' first.")
        sys.exit(1)

    repo_name = args.index
    if not repo_name:
        # Default to first available index if not specified
        repo_name = indexes[0]

    index_dir = settings.INDEXES_DIR / repo_name
    if not index_dir.exists():
        console.print(f"[bold red]Index '{repo_name}' not found.[/bold red] Available indexes: {', '.join(indexes)}")
        sys.exit(1)

    console.print(f"[dim]Searching repository '[bold]{repo_name}[/bold]' for:[/dim] \"[italic cyan]{args.query}[/italic cyan]\"\n")

    try:
        engine = SearchEngine.from_index_dir(index_dir)
        results, latency_ms = engine.search(args.query, top_k=args.top_k)

        if not results:
            console.print("[yellow]No relevant code chunks found.[/yellow]")
            return

        console.print(f"[bold green]Found {len(results)} relevant code chunk(s) in {latency_ms:.1f}ms:[/bold green]\n")

        for r in results:
            chunk = r.chunk
            symbol_info = f" | {chunk.chunk_type.value.capitalize()}: [bold cyan]{chunk.symbol_name}[/bold cyan]" if chunk.symbol_name else ""
            title = f"[bold green]#{r.rank}[/bold green] [bold yellow]{chunk.file_path}[/bold yellow] (Lines {chunk.start_line}-{chunk.end_line}){symbol_info} [dim](Similarity: {r.score:.4f})[/dim]"

            syntax = Syntax(
                chunk.code,
                chunk.language,
                theme="monokai",
                line_numbers=True,
                start_line=chunk.start_line,
            )

            panel = Panel(
                syntax,
                title=title,
                title_align="left",
                border_style="blue" if r.rank == 1 else "dim",
                box=box.ROUNDED,
            )
            console.print(panel)
            console.print()

    except Exception as e:
        console.print(f"[bold red]Error during search:[/bold red] {e}")
        sys.exit(1)


def print_index_stats(repo_name: str):
    """Displays rich table summary of an index."""
    index_dir = settings.INDEXES_DIR / repo_name
    meta_file = index_dir / "metadata.json"
    if not meta_file.exists():
        console.print(f"[yellow]No metadata file found for index '{repo_name}'[/yellow]")
        return

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    table = Table(title=f"Repository Index Stats: {repo_name}", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Source", meta.get("repo_source", "N/A"))
    table.add_row("Indexed At", meta.get("indexed_at", "N/A"))
    table.add_row("Total Files", str(meta.get("total_files", 0)))
    table.add_row("Total Code Chunks", str(meta.get("total_chunks", 0)))
    table.add_row("Embedding Model", meta.get("embedding_model", "N/A"))
    table.add_row("Embedding Dimension", str(meta.get("embedding_dimension", 0)))
    table.add_row("Languages Breakdown", ", ".join(f"{k}: {v}" for k, v in meta.get("languages", {}).items()))
    table.add_row("AST Chunk Types", ", ".join(f"{k}: {v}" for k, v in meta.get("chunk_types", {}).items()))
    table.add_row("Ingestion Time", f"{meta.get('ingestion_time_sec', 0)}s")
    table.add_row("Parsing Time", f"{meta.get('parsing_time_sec', 0)}s")
    table.add_row("Embedding Time", f"{meta.get('embedding_time_sec', 0)}s")
    table.add_row("Indexing Time", f"{meta.get('indexing_time_sec', 0)}s")
    table.add_row("Total Pipeline Time", f"{meta.get('total_time_sec', 0)}s")

    console.print(table)


def handle_stats(args):
    """Prints stats for an indexed repository."""
    indexes = get_available_indexes()
    if not indexes:
        console.print("[yellow]No indexes found.[/yellow]")
        return

    repo_name = args.index or indexes[0]
    print_index_stats(repo_name)


def handle_list(args):
    """Lists all indexed repositories."""
    indexes = get_available_indexes()
    if not indexes:
        console.print("[yellow]No indexed repositories found.[/yellow]")
        return

    table = Table(title="Indexed Repositories", box=box.ROUNDED)
    table.add_column("Repository Name", style="cyan")
    table.add_column("Index Path", style="dim")

    for name in indexes:
        table.add_row(name, str(settings.INDEXES_DIR / name))

    console.print(table)


def handle_evaluate(args):
    """Runs evaluation benchmark on retrieval performance."""
    indexes = get_available_indexes()
    if not indexes:
        console.print("[bold red]No indexed repositories found to evaluate.[/bold red]")
        sys.exit(1)

    repo_name = args.index or indexes[0]
    index_dir = settings.INDEXES_DIR / repo_name

    dataset_path = Path(args.dataset) if args.dataset else (settings.BASE_DIR / "app" / "evaluation" / "benchmark_dataset.json")
    if not dataset_path.exists():
        console.print(f"[bold red]Benchmark dataset not found at:[/bold red] {dataset_path}")
        sys.exit(1)

    console.print(f"[bold cyan]Running Retrieval Benchmark on index:[/bold cyan] {repo_name}")
    console.print(f"[dim]Dataset:[/dim] {dataset_path}\n")

    engine = SearchEngine.from_index_dir(index_dir)
    evaluator = CodeRetrievalEvaluator(engine)
    queries = evaluator.load_benchmark_queries(dataset_path)

    result = evaluator.evaluate(queries, top_k=args.top_k)

    # Display summary table
    table = Table(title="Benchmark Evaluation Results", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Score", style="bold green")

    table.add_row("Total Test Queries", str(result.total_queries))
    table.add_row("Recall@1", f"{result.recall_at_1 * 100:.1f}%")
    table.add_row("Recall@3", f"{result.recall_at_3 * 100:.1f}%")
    table.add_row("Recall@5", f"{result.recall_at_5 * 100:.1f}%")
    table.add_row("Mean Reciprocal Rank (MRR)", f"{result.mean_reciprocal_rank:.4f}")

    console.print(table)

    # Detailed breakdown
    console.print("\n[bold]Query Breakdown:[/bold]")
    for item in result.query_evaluations:
        rank_str = f"[bold green]Rank {item['found_rank']}[/bold green]" if item['found_rank'] else "[bold red]Not in Top K[/bold red]"
        console.print(f" • [italic]\"{item['query']}\"[/italic] -> Expected: [cyan]{item['expected_file']}[/cyan] ({item.get('expected_symbol') or ''}) | {rank_str} ({item['latency_ms']}ms)")


def main():
    parser = argparse.ArgumentParser(
        prog="python -m app",
        description="Local AI Code Intelligence Engine - Phase 1",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Ingest remote Git repo
    parser_ingest = subparsers.add_parser("ingest", help="Clone and index a remote Git repository")
    parser_ingest.add_argument("git_url", type=str, help="GitHub/Git repository URL")
    parser_ingest.add_argument("--force", action="store_true", help="Force re-clone if directory exists")

    # Ingest local repo
    parser_ingest_local = subparsers.add_parser("ingest-local", help="Index a local repository directory")
    parser_ingest_local.add_argument("repo_path", type=str, help="Path to local repository directory")

    # Search
    parser_search = subparsers.add_parser("search", help="Perform semantic code search")
    parser_search.add_argument("query", type=str, help="Natural language or code query")
    parser_search.add_argument("--index", type=str, default=None, help="Target repository index name")
    parser_search.add_argument("--top-k", type=int, default=settings.DEFAULT_TOP_K, help="Number of results to retrieve")

    # Stats
    parser_stats = subparsers.add_parser("stats", help="Show statistics of an indexed repository")
    parser_stats.add_argument("--index", type=str, default=None, help="Target repository index name")

    # List indexes
    subparsers.add_parser("list-indexes", help="List all indexed repositories")

    # Evaluate
    parser_eval = subparsers.add_parser("evaluate", help="Run evaluation benchmark metrics (Recall@K, MRR)")
    parser_eval.add_argument("--index", type=str, default=None, help="Target repository index name")
    parser_eval.add_argument("--dataset", type=str, default=None, help="Path to benchmark JSON dataset")
    parser_eval.add_argument("--top-k", type=int, default=5, help="Top-K cutoff for evaluation")

    args = parser.parse_args()

    if args.command == "ingest":
        handle_ingest(args)
    elif args.command == "ingest-local":
        handle_ingest_local(args)
    elif args.command == "search":
        handle_search(args)
    elif args.command == "stats":
        handle_stats(args)
    elif args.command == "list-indexes":
        handle_list(args)
    elif args.command == "evaluate":
        handle_evaluate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
