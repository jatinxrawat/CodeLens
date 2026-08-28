"""Repository Analysis Report Generator.

Compiles comprehensive intelligence reports including architecture, code metrics,
complexity hotspots, smell findings, and static security patterns.
"""

from typing import Dict, Any, Optional
from app.services.repository_service import repository_service
from app.analysis.architecture_engine import ArchitectureEngine
from app.analysis.quality_metrics import QualityMetricsCalculator
from app.analysis.code_smells import CodeSmellDetector
from app.analysis.security_scanner import SecurityScanner


class ReportService:
    """Compiles structured analysis reports exportable as Markdown or JSON."""

    def __init__(self):
        self.arch_engine = ArchitectureEngine()
        self.quality_calc = QualityMetricsCalculator()
        self.smell_detector = CodeSmellDetector()
        self.security_scanner = SecurityScanner()
        self._report_cache: Dict[str, Dict[str, Any]] = {}
        self._markdown_cache: Dict[str, str] = {}

    def clear_cache(self, repo_name: Optional[str] = None):
        """Clears report cache for a repository or all repositories."""
        if repo_name:
            self._report_cache.pop(repo_name, None)
            self._markdown_cache.pop(repo_name, None)
        else:
            self._report_cache.clear()
            self._markdown_cache.clear()

    def generate_report_data(self, repo_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Generates comprehensive analytical data for the repository."""
        if not force_refresh and repo_name in self._report_cache:
            return self._report_cache[repo_name]

        stats = repository_service.get_repository_stats(repo_name)
        arch = self.arch_engine.infer_architecture(repo_name)
        quality = self.quality_calc.analyze_repository(repo_name)
        smells = self.smell_detector.detect_smells(repo_name)
        security = self.security_scanner.scan_repository(repo_name)

        def _dump(m: Any) -> Dict[str, Any]:
            return m.model_dump() if hasattr(m, "model_dump") else m.dict()

        report_data = {
            "repository_id": repo_name,
            "source": stats.source,
            "indexed_at": stats.indexed_at,
            "stats": _dump(stats),
            "architecture": _dump(arch),
            "quality": _dump(quality),
            "code_smells": _dump(smells),
            "security": _dump(security),
        }
        self._report_cache[repo_name] = report_data
        return report_data

    def generate_markdown_report(self, repo_name: str, force_refresh: bool = False) -> str:
        """Formats the repository analysis report into a clean, GitHub-Flavored Markdown document."""
        if not force_refresh and repo_name in self._markdown_cache:
            return self._markdown_cache[repo_name]

        data = self.generate_report_data(repo_name, force_refresh=force_refresh)
        stats = data["stats"]
        arch = data["architecture"]
        quality = data["quality"]
        smells = data["code_smells"]
        security = data["security"]

        md_lines = [
            f"# Code Intelligence Report: {repo_name}",
            f"> **Source:** `{stats['source']}`  ",
            f"> **Generated:** `{stats['indexed_at']}` • **Engine:** Local AI Code Intelligence Engine v0.4.0",
            "",
            "---",
            "",
            "## 1. Executive Summary & Telemetry",
            "",
            f"- **Total Source Files:** {stats['total_files']}",
            f"- **Total AST Chunks:** {stats['total_chunks']}",
            f"- **Total Lines of Code:** {stats['total_lines_of_code']}",
            f"- **Overall Maintainability:** `{quality['overall_maintainability']}`",
            f"- **Coupling Rating:** `{quality['coupling_level']}`",
            f"- **Embedding Model:** `{stats['embedding_model']}` ({stats['embedding_dimension']}d)",
            "",
            "### Language Breakdown",
            "| Language | AST Chunks |",
            "|---|---|",
        ]

        for lang, count in stats.get("languages", {}).items():
            md_lines.append(f"| **{lang.capitalize()}** | {count} |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 2. Inferred Architecture & Layer Topology",
            f"> **Pattern:** `{arch['inferred_pattern']}` ({arch['status']})",
            "",
            "### Architectural Subsystem Layers",
            "| Layer Name | Files Count | Symbols Count | Languages |",
            "|---|---|---|---|",
        ])

        for layer in arch.get("layers", []):
            langs_str = ", ".join(layer["primary_languages"])
            md_lines.append(f"| **{layer['name']}** | {layer['file_count']} | {layer['symbol_count']} | {langs_str} |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 3. Code Complexity & Quality Metrics",
            f"- **Average Cyclomatic Complexity:** {quality['avg_cyclomatic_complexity']}",
            f"- **Maximum Cyclomatic Complexity:** {quality['max_cyclomatic_complexity']}",
            f"- **Average Function Length:** {quality['avg_function_length']} lines",
            "",
            "### Top Complexity Hotspots",
            "| Symbol | File | Lines | McCabe CC | Rating |",
            "|---|---|---|---|---|",
        ])

        for fn in quality.get("top_complex_functions", [])[:5]:
            md_lines.append(f"| `{fn['symbol']}` | `{fn['file_path']}` | {fn['start_line']}–{fn['end_line']} | {fn['cyclomatic_complexity']} | `{fn['rating']}` |")

        md_lines.extend([
            "",
            "---",
            "",
            f"## 4. Code Smells & Maintainability Risks ({smells['total_findings']} Detected)",
            f"- **Critical:** {smells['critical_count']} • **Warning:** {smells['warning_count']} • **Info:** {smells['info_count']}",
            "",
        ])

        if smells.get("findings"):
            md_lines.extend([
                "| Issue | Location | Metric | Recommendation |",
                "|---|---|---|---|",
            ])
            for s in smells["findings"][:10]:
                loc = f"`{s['file_path']}:{s['start_line']}`"
                sym = f" ({s['symbol_name']})" if s.get("symbol_name") else ""
                md_lines.append(f"| **{s['issue_title']}** | {loc}{sym} | {s['metric_value']} | {s['recommendation']} |")
        else:
            md_lines.append("No critical code smells detected.")

        md_lines.extend([
            "",
            "---",
            "",
            f"## 5. Security Insights & Pattern Analysis ({security['total_findings']} Detected)",
            f"- **Critical:** {security['critical_count']} • **High:** {security['high_count']} • **Medium:** {security['medium_count']}",
            "",
        ])

        if security.get("findings"):
            md_lines.extend([
                "| Severity | Rule | Location | Explanation |",
                "|---|---|---|---|",
            ])
            for sec in security["findings"]:
                loc = f"`{sec['file_path']}:{sec['start_line']}`"
                md_lines.append(f"| `{sec['severity']}` | **{sec['rule_name']}** | {loc} | {sec['explanation']} |")
        else:
            md_lines.append("No static pattern security risks detected.")

        md_lines.extend([
            "",
            "---",
            "",
            "*Report generated 100% locally via Local AI Code Intelligence Engine without external API dependencies.*",
        ])

        result = "\n".join(md_lines)
        self._markdown_cache[repo_name] = result
        return result


report_service = ReportService()
