"""Static Security Pattern Scanner.

Performs non-destructive static pattern analysis to detect potential security
concerns such as hardcoded secrets, SQL injection risks, insecure subprocesses,
and unsafe deserialization.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.code_chunk import CodeChunk
from app.config import settings


class SecurityFinding(BaseModel):
    id: str
    file_path: str
    symbol_name: Optional[str] = None
    start_line: int
    rule_id: str
    rule_name: str
    severity: str = Field(..., description="'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'")
    confidence: float
    matched_snippet: str
    explanation: str
    recommendation: str


class SecurityScanReport(BaseModel):
    repository_id: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[SecurityFinding]
    disclaimer: str = (
        "Potential security concerns detected via static pattern matching. "
        "This scan does not prove exploitability or guarantee the absence of other vulnerabilities."
    )


class SecurityScanner:
    """Detects static code security risk patterns without executing repository code."""

    def __init__(self):
        # Compiled security rules (rule_id, rule_name, pattern, severity, confidence, explanation, recommendation)
        self.rules = [
            (
                "SEC001",
                "Hardcoded Secret / API Key",
                re.compile(r"""(?:api_key|apikey|secret_key|private_key|auth_token|jwt_secret|password)\s*=\s*['"][a-zA-Z0-9_\-\.]{8,}['"]""", re.IGNORECASE),
                "CRITICAL",
                0.90,
                "Potential plaintext credential or secret hardcoded directly in source code.",
                "Store sensitive credentials in environment variables or a secure secret manager (e.g. HashiCorp Vault, AWS Secrets Manager).",
            ),
            (
                "SEC002",
                "Insecure Subprocess Execution (shell=True)",
                re.compile(r"""subprocess\.(?:Popen|call|run|check_output)\s*\([^)]*shell\s*=\s*True""", re.IGNORECASE),
                "HIGH",
                0.92,
                "Subprocess executed with shell=True creates severe command injection risks if unvalidated user input is passed.",
                "Pass arguments as a list of strings and set shell=False (e.g. `subprocess.run(['command', arg1, arg2])`).",
            ),
            (
                "SEC003",
                "Direct String Concatenation in SQL Query",
                re.compile(r"""(?:cursor\.execute|execute|query)\s*\(\s*(?:f['"]|['"].*?%\s*\(|['"].*?\+\s*)""", re.IGNORECASE),
                "HIGH",
                0.85,
                "Constructing SQL queries using dynamic string formatting or concatenation exposes the database to SQL injection.",
                "Use parameterized queries with placeholder bindings (e.g. `cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))`).",
            ),
            (
                "SEC004",
                "Unsafe Deserialization (pickle/yaml)",
                re.compile(r"""(?:pickle\.loads|pickle\.load|_pickle\.load|yaml\.load\([^,)]+\))""", re.IGNORECASE),
                "HIGH",
                0.88,
                "Deserializing untrusted data with pickle or unconstrained yaml.load can lead to arbitrary remote code execution.",
                "Use safe serialization formats like JSON (`json.loads`) or safe YAML (`yaml.safe_load`).",
            ),
            (
                "SEC005",
                "Disabled TLS Certificate Verification",
                re.compile(r"""(?:requests\.(?:get|post|put|delete)|httpx\.(?:get|post))\s*\([^)]*verify\s*=\s*False""", re.IGNORECASE),
                "MEDIUM",
                0.95,
                "Disabling TLS certificate verification (verify=False) exposes HTTP traffic to Man-in-the-Middle (MitM) interception.",
                "Enable standard TLS verification by removing verify=False or supplying a valid trusted CA certificate bundle.",
            ),
            (
                "SEC006",
                "Insecure Dynamic Code Execution (eval/exec)",
                re.compile(r"""\b(?:eval|exec)\s*\(""", re.IGNORECASE),
                "HIGH",
                0.80,
                "Dynamic code evaluation via eval() or exec() allows arbitrary code execution if user inputs reach the argument.",
                "Refactor dynamic expressions to use structured dispatch dictionaries, parsers, or strict mathematical evaluators.",
            ),
        ]

    def scan_repository(self, repo_name: str) -> SecurityScanReport:
        """Scans all indexed repository chunks for static security risk patterns."""
        index_dir = settings.INDEXES_DIR / repo_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            raise FileNotFoundError(f"Repository index for '{repo_name}' not found.")

        with open(chunks_file, "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)
        chunks = [CodeChunk.from_dict(c) for c in raw_chunks]

        findings: List[SecurityFinding] = []
        finding_id_seq = 1

        for c in chunks:
            for rule_id, rule_name, pattern, severity, conf, expl, rec in self.rules:
                match = pattern.search(c.code)
                if match:
                    # Calculate exact line within chunk
                    matched_str = match.group(0)
                    offset_lines = c.code[:match.start()].count("\n")
                    exact_line = c.start_line + offset_lines

                    findings.append(
                        SecurityFinding(
                            id=f"sec_{finding_id_seq}",
                            file_path=c.file_path,
                            symbol_name=c.symbol_name,
                            start_line=exact_line,
                            rule_id=rule_id,
                            rule_name=rule_name,
                            severity=severity,
                            confidence=conf,
                            matched_snippet=matched_str[:80],
                            explanation=expl,
                            recommendation=rec,
                        )
                    )
                    finding_id_seq += 1

        crit = sum(1 for f in findings if f.severity == "CRITICAL")
        high = sum(1 for f in findings if f.severity == "HIGH")
        med = sum(1 for f in findings if f.severity == "MEDIUM")
        low = sum(1 for f in findings if f.severity == "LOW")

        severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_findings = sorted(findings, key=lambda x: severity_rank.get(x.severity, 4))

        return SecurityScanReport(
            repository_id=repo_name,
            total_findings=len(findings),
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            findings=sorted_findings,
        )
