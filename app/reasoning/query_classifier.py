"""Structured Query Classification Engine.

Categorizes user questions into distinct architectural & code intelligence categories:
Architecture, Dependency, Code Flow, Symbol Search, Security, Complexity, Documentation, General QA.
"""

import re
from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field


class QueryClassification(BaseModel):
    category: str = Field(..., description="'Architecture', 'Dependency', 'Code Flow', 'Symbol Search', 'Security', 'Complexity', 'Documentation', 'General QA'")
    confidence: float
    detected_entities: list[str] = []
    recommended_mode: str = Field(..., description="'hybrid', 'graph', 'static_scan', 'flow_trace'")


class QueryClassifier:
    """Classifies user queries to direct them to the appropriate evidence pipeline."""

    def __init__(self):
        self.rules = [
            (
                "Security",
                re.compile(r"\b(security|vulnerabilit|injection|secret|credential|unsafe|eval|exec|risk|cve|auth pattern|flaw)\b", re.IGNORECASE),
                "static_scan",
                0.90,
            ),
            (
                "Complexity",
                re.compile(r"\b(complex|cyclomatic|nesting|maintainab|smell|refactor|god class|long function|lines of code|loc)\b", re.IGNORECASE),
                "static_scan",
                0.90,
            ),
            (
                "Code Flow",
                re.compile(r"\b(flow|caller|callee|trace|what happens when|step by step|execution path|call graph|invokes)\b", re.IGNORECASE),
                "flow_trace",
                0.88,
            ),
            (
                "Dependency",
                re.compile(r"\b(depend|import|imported by|who imports|depends on|downstream|upstream|blast radius|coupling)\b", re.IGNORECASE),
                "graph",
                0.88,
            ),
            (
                "Symbol Search",
                re.compile(r"\b(where is|defined|declaration|definition|find function|find class|symbol)\b", re.IGNORECASE),
                "hybrid",
                0.85,
            ),
            (
                "Architecture",
                re.compile(r"\b(architecture|layer|pattern|tier|overview|subsystem|modular|components|high level|structure)\b", re.IGNORECASE),
                "graph",
                0.85,
            ),
            (
                "Documentation",
                re.compile(r"\b(explain|document|how does|what is the purpose of|summary of|module explanation)\b", re.IGNORECASE),
                "hybrid",
                0.80,
            ),
        ]

    def classify(self, query: str) -> QueryClassification:
        """Classifies the given user query using regex rules and entity extraction."""
        query_text = query.strip()

        # Extract potential file or symbol entities: words with extensions or CamelCase/snake_case
        entities = []
        for word in re.findall(r"\b[a-zA-Z0-9_\-\./]+\b", query_text):
            if "." in word or "_" in word or (word[0].isupper() and any(c.islower() for c in word)):
                if len(word) > 2 and word.lower() not in ("what", "where", "how", "when", "why"):
                    entities.append(word)

        for category, pattern, rec_mode, conf in self.rules:
            if pattern.search(query_text):
                return QueryClassification(
                    category=category,
                    confidence=conf,
                    detected_entities=list(set(entities)),
                    recommended_mode=rec_mode,
                )

        return QueryClassification(
            category="General QA",
            confidence=0.70,
            detected_entities=list(set(entities)),
            recommended_mode="hybrid",
        )
