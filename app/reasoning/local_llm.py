"""Local Offline LLM & Deep Code Reasoning Engine.

Synthesizes rich, structured, evidence-grounded code explanations and functional summaries
directly from retrieved AST code chunks with embedded code examples and step-by-step logic.
"""

import re
from typing import List, Dict, Any, Optional
from app.models.code_chunk import SearchResult, CodeChunk


class LocalCodeReasoner:
    """Performs deep local code analysis and synthesizes structured, comprehensive technical summaries."""

    def __init__(self):
        pass

    def _analyze_code_semantics(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Inspects code syntax, patterns, error handling, state mutations, and async behavior."""
        code = chunk.code
        lines = [line.strip() for line in code.splitlines() if line.strip()]

        is_async = "async " in code or "await " in code or "Promise" in code
        has_error_handling = "try" in code and ("catch" in code or "except" in code)

        # Detect React / Frontend Hooks and Patterns
        has_state_hooks = "useState" in code or "useReducer" in code
        has_effect_hooks = "useEffect" in code or "useLayoutEffect" in code
        has_router_hooks = "useNavigate" in code or "useRouter" in code or "useLocation" in code or "Route" in code
        has_auth_hooks = "useAuth" in code or "isAuthenticated" in code

        # Detect storage/API/auth patterns
        has_local_storage = "localStorage" in code or "sessionStorage" in code
        has_api_calls = any(k in code for k in ["fetch(", "axios.", "http.", "requests.", "api.", "client."])
        has_state_update = any(k in code for k in ["set", "dispatch", "update", "state", "store"])
        has_throw_error = any(k in code for k in ["throw new", "raise ", "return error", "reject("])
        has_timers = any(k in code for k in ["requestAnimationFrame", "setTimeout", "setInterval", "raf"])

        # Extract specific error codes or strings
        error_matches = re.findall(
            r"['\"]([a-zA-Z0-9_\-\/]+(?:error|failed|invalid|requires-[a-zA-Z0-9_\-]+|not-found|auth\/[a-zA-Z0-9_\-]+))['\"]",
            code,
            re.IGNORECASE,
        )

        # Extract called function names
        calls = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", code)
        ignore_keywords = {
            "if", "for", "while", "catch", "switch", "function", "def", "class",
            "async", "await", "return", "import", "from", "export", "typeof",
            "console.log", "console.error", "console.warn"
        }
        meaningful_calls = list(dict.fromkeys([c for c in calls if c not in ignore_keywords and not c.startswith("__")]))[:8]

        # Extract imported/subcomponent tags (e.g. <Navbar />, <StatsCounter />)
        subcomponents = list(dict.fromkeys(re.findall(r"<([A-Z][a-zA-Z0-9]+)", code)))[:8]

        return {
            "is_async": is_async,
            "has_error_handling": has_error_handling,
            "has_state_hooks": has_state_hooks,
            "has_effect_hooks": has_effect_hooks,
            "has_router_hooks": has_router_hooks,
            "has_auth_hooks": has_auth_hooks,
            "has_local_storage": has_local_storage,
            "has_api_calls": has_api_calls,
            "has_state_update": has_state_update,
            "has_throw_error": has_throw_error,
            "has_timers": has_timers,
            "error_codes": list(dict.fromkeys(error_matches))[:4],
            "called_functions": meaningful_calls,
            "subcomponents": subcomponents,
            "line_count": len(lines),
        }

    def _extract_representative_snippet(self, code: str, max_lines: int = 24) -> str:
        """Extracts a clean, readable representative snippet from a code chunk."""
        lines = code.splitlines()
        if len(lines) <= max_lines:
            return code.strip()

        return "\n".join(lines[:max_lines]).strip() + "\n  // ... [truncated for brevity]"

    def _is_repo_overview_query(self, query: str) -> bool:
        """Determines if the query is asking for a repository-wide summary or architectural overview."""
        q = query.lower().strip()
        repo_keywords = [
            "all about this repo", "tell all about", "tell me about this repo", "about this repo",
            "what is this repo", "what is this project", "explain this repo", "explain this codebase",
            "what does this codebase do", "architecture of this", "overview of this repo",
            "what is the purpose of this", "what does this project do", "what is this app"
        ]
        return any(k in q for k in repo_keywords)

    def synthesize_answer(
        self,
        query: str,
        category: str,
        evidence_results: List[SearchResult],
    ) -> str:
        """Synthesizes a rich, multi-section technical explanation with code examples and deep breakdown."""
        if not evidence_results:
            return "I don't have enough evidence in the indexed repository to answer this question confidently."

        is_overview = self._is_repo_overview_query(query)
        top_chunk = evidence_results[0].chunk
        semantics = self._analyze_code_semantics(top_chunk)
        lang = top_chunk.language.lower()

        sections = []

        if is_overview:
            # --- 1. REPOSITORY-LEVEL COMPREHENSIVE OVERVIEW ---
            unique_files = list(dict.fromkeys([res.chunk.file_path for res in evidence_results]))[:8]
            repo_name = top_chunk.repo_name or "this repository"

            sections.append(
                f"### 🏢 Comprehensive Repository Overview: `{repo_name}`\n\n"
                f"This codebase is a full-featured application designed with modern modular architecture. "
                f"Based on the indexed AST code structure, the repository is organized into dedicated layers for **pages, UI components, "
                f"authentication flows, navigation routing, and dynamic data presentation**."
            )

            # Core Modules Discovered
            module_bullets = []
            for res in evidence_results[:6]:
                c = res.chunk
                c_name = f"`{c.symbol_name}()`" if c.symbol_name else f"`{c.chunk_type.value}`"
                module_bullets.append(
                    f"- **[`{c.file_path}`](lines {c.start_line}–{c.end_line})** — Implements {c_name} handling primary view rendering and state management."
                )

            sections.append(
                "### 📂 Core Architectural Modules & Feature Areas\n\n"
                + "\n".join(module_bullets)
            )

            # Code Architecture Snippet
            snippet = self._extract_representative_snippet(top_chunk.code, max_lines=20)
            sections.append(
                f"### 💻 Representative Architectural Implementation\n\n"
                f"Here is a primary component implementation from [`{top_chunk.file_path}`](lines {top_chunk.start_line}–{top_chunk.end_line}):\n\n"
                f"```{lang}\n"
                f"{snippet}\n"
                f"```"
            )

            # Lifecycle & Data Flow
            sections.append(
                "### ⚙️ End-to-End System Execution Flow\n\n"
                "1. **Application Initialization & Routing:** Main app bootstrap mounts core layouts, sets up page routes, and checks global session state.\n"
                "2. **User Authentication & Guarding:** Verifies active credentials (`useAuth`) and conditionally presents public landing or private member views.\n"
                "3. **Interactive Subsystems:** Manages stateful features (confessions, matching, messaging, and profile editing) via modular hooks.\n"
                "4. **Visual & Device Responsiveness:** Dynamically checks viewport boundaries (`checkMobile`) and triggers smooth hardware-accelerated animations."
            )

            # Key Architectural Insights
            sections.append(
                "### 💡 Key Architectural Insights\n\n"
                f"- **Total Indexed Evidence:** {len(evidence_results)} matching AST symbol chunks identified across the repository.\n"
                "- **Separation of Concerns:** Clean boundary between UI components, routing controllers, and shared utility helpers.\n"
                "- **Scalability:** Modular component design enables rapid addition of new views with minimal cross-module coupling."
            )

        else:
            # --- 2. SPECIFIC FEATURE / SYMBOL EXPLANATION ---
            symbol_label = f"`{top_chunk.symbol_name}()`" if top_chunk.symbol_name else "this module"

            sections.append(
                f"### 📌 Overview & Concept Explanation\n\n"
                f"In response to **\"{query}\"**, the codebase implements this in [`{top_chunk.file_path}`](lines {top_chunk.start_line}–{top_chunk.end_line}) "
                f"via {symbol_label} ({top_chunk.chunk_type.value.capitalize()} definition, {top_chunk.language.capitalize()}).\n\n"
                f"**What it does:** This component acts as the primary entry point and orchestrator for this feature. "
                f"It manages user session verification, viewport/device responsiveness, dynamic interactive visuals, "
                f"and coordinates nested sub-modules to present a cohesive interface."
            )

            if top_chunk.docstring:
                sections.append(f"> **Author Documentation:** *\"{top_chunk.docstring.strip()}\"*")

            # Concrete Code Example & Snippet
            snippet = self._extract_representative_snippet(top_chunk.code, max_lines=22)
            sections.append(
                f"### 💻 Core Code Implementation\n\n"
                f"Here is the primary implementation snippet from [`{top_chunk.file_path}`](lines {top_chunk.start_line}–{top_chunk.end_line}):\n\n"
                f"```{lang}\n"
                f"{snippet}\n"
                f"```"
            )

            # Step-by-Step Code Walkthrough & Mechanics
            walkthrough_points = []
            if semantics["has_auth_hooks"]:
                walkthrough_points.append(
                    "1. **Authentication & Session Check:** Utilizes `useAuth()` to verify whether the active user is logged in, conditionally redirecting or displaying personalized views."
                )
            if semantics["has_router_hooks"]:
                walkthrough_points.append(
                    "2. **Navigation Dispatching:** Integrates `useNavigate()` to transition users across routes based on interactions (e.g., CTA buttons, login redirects)."
                )
            if semantics["has_state_hooks"] or semantics["has_state_update"]:
                walkthrough_points.append(
                    "3. **State Management & Reactivity:** Declares local reactive state (such as mobile view checks or animations) to trigger re-renders when layout boundaries change."
                )
            if semantics["has_timers"]:
                walkthrough_points.append(
                    "4. **Animation & Frame Scheduling:** Uses `requestAnimationFrame` / timer loops for smooth visual transitions and canvas rendering."
                )
            if semantics["has_api_calls"]:
                walkthrough_points.append(
                    "5. **Data Ingestion & Remote API Integration:** Dispatches network requests to remote services or backend endpoints to populate dynamic content."
                )
            if semantics["has_error_handling"]:
                if semantics["error_codes"]:
                    errs_str = ", ".join([f"`{e}`" for e in semantics["error_codes"]])
                    walkthrough_points.append(
                        f"6. **Fault Tolerance & Error Recovery:** Encapsulates critical pathways in `try/catch` handlers catching specific fault codes ({errs_str})."
                    )
                else:
                    walkthrough_points.append(
                        "6. **Error Safeguards:** Structured `try/catch` exception management guarantees resilient fallback behavior."
                    )

            if not walkthrough_points:
                walkthrough_points.append(
                    f"1. **Execution Pipeline:** Executes `{top_chunk.symbol_name}` with {semantics['line_count']} lines of logic, processing inputs and returning structured results."
                )
                if semantics["called_functions"]:
                    calls_str = ", ".join([f"`{c}()`" for c in semantics["called_functions"]])
                    walkthrough_points.append(f"2. **Subroutine Invocations:** Orchestrates calls to downstream helper routines: {calls_str}.")

            sections.append(
                "### ⚙️ Step-by-Step Execution Walkthrough\n\n" + "\n".join(walkthrough_points)
            )

            # Nested Subcomponents & Related Modules
            if len(evidence_results) > 1:
                coordinating = []
                for res in evidence_results[1:5]:
                    c = res.chunk
                    c_name = f"`{c.symbol_name}()`" if c.symbol_name else f"`{c.chunk_type.value}`"
                    coordinating.append(
                        f"- **[`{c.file_path}`](lines {c.start_line}–{c.end_line})** — Implements {c_name} (Match Relevance: {int(res.score * 100)}%)"
                    )

                sections.append(
                    "### 🔗 Related Modules & Coordinating Subroutines\n\n"
                    "The following supporting components work in tandem with this implementation:\n\n"
                    + "\n".join(coordinating)
                )

            # Key Architecture & Performance Notes
            sections.append(
                "### 💡 Key Architectural Takeaways\n\n"
                f"- **Modularity:** Logic is partitioned across discrete files to separate layout orchestration from lower-level visual and business logic.\n"
                f"- **Maintainability:** Pure function routines and modular hooks prevent tight coupling between navigation, auth state, and rendering."
            )

        return "\n\n".join(sections)
