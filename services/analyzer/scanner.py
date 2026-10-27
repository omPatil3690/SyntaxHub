"""
Scans source files for API usages that match the knowledge graph.

Two detection strategies, combined:
1. Regex, matched per-line against raw source. Handles the majority of
   entries (imports, call expressions, config keys) cheaply and reliably.
2. Tree-sitter structural check for the middleware->proxy rename
   specifically: it confirms the file is *actually* a top-level exported
   function named `middleware`, not just a string that happens to match
   "export function middleware(" in a comment or string literal — the
   kind of false positive regex alone is prone to.

This mirrors the project's own stated principle: prefer deterministic
parsing over asking an LLM to "find" deprecated APIs, and use the AST
wherever precision actually matters.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from packages.schemas.models import Finding, KnowledgeGraphEntry

SCAN_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}
IGNORE_DIRS = {"node_modules", ".git", ".next", "dist", "build", ".turbo"}


@dataclass
class _TreeSitterUnavailable:
    reason: str


def _get_ts_parser():
    """Lazily load tree-sitter so the rest of the analyzer still works
    (regex-only) in environments where the grammar package isn't installed.
    """
    try:
        from tree_sitter_languages import get_parser
        return get_parser("typescript")
    except Exception as exc:  # pragma: no cover - exercised only when tree-sitter missing
        return _TreeSitterUnavailable(reason=str(exc))


def iter_source_files(repo_root: Path, max_files: int) -> list[Path]:
    files = []
    for path in repo_root.rglob("*"):
        if len(files) >= max_files:
            break
        if path.is_dir() or path.suffix not in SCAN_EXTENSIONS:
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def _regex_findings(content: str, rel_path: str, entries: list[KnowledgeGraphEntry]) -> list[Finding]:
    findings = []
    lines = content.splitlines()
    for entry in entries:
        try:
            pattern = re.compile(entry.detection_pattern)
        except re.error:
            continue
        for i, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(Finding(
                    file_path=rel_path, line=i, api_name=entry.api_name,
                    matched_text=line.strip()[:200], change_type=entry.change_type,
                    severity=entry.severity, replacement=entry.replacement,
                    migration_hint=entry.migration_hint, doc_url=entry.doc_url,
                ))
    return findings


def _middleware_ast_check(content: str, rel_path: str, ts_parser, entry: KnowledgeGraphEntry) -> Finding | None:
    """Structural confirmation for the middleware->proxy rename: only
    fires when `middleware` is a top-level exported function, and only
    for files actually named middleware.ts/js (the Next.js convention).
    """
    if not Path(rel_path).name.startswith("middleware."):
        return None
    if isinstance(ts_parser, _TreeSitterUnavailable):
        return None  # regex path above already covers this case as a fallback

    tree = ts_parser.parse(content.encode("utf-8"))

    def walk(node):
        if node.type == "export_statement":
            for child in node.children:
                if child.type == "function_declaration":
                    name_node = child.child_by_field_name("name")
                    if name_node and content.encode("utf-8")[name_node.start_byte:name_node.end_byte] == b"middleware":
                        line = content[:node.start_byte].count("\n") + 1
                        return line
        for child in node.children:
            result = walk(child)
            if result:
                return result
        return None

    line = walk(tree.root_node)
    if line is None:
        return None
    return Finding(
        file_path=rel_path, line=line, api_name=entry.api_name,
        matched_text="export function middleware(...)", change_type=entry.change_type,
        severity=entry.severity, replacement=entry.replacement,
        migration_hint=entry.migration_hint, doc_url=entry.doc_url,
    )


def scan_repository(
    repo_root: Path, entries: list[KnowledgeGraphEntry], max_files: int = 3000
) -> tuple[list[Finding], int]:
    ts_parser = _get_ts_parser()
    middleware_entry = next((e for e in entries if e.api_name == "middleware.ts convention"), None)
    other_entries = [e for e in entries if e is not middleware_entry]

    files = iter_source_files(repo_root, max_files)
    all_findings: list[Finding] = []

    for path in files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel_path = str(path.relative_to(repo_root))

        all_findings.extend(_regex_findings(content, rel_path, other_entries))

        if middleware_entry is not None:
            ast_finding = _middleware_ast_check(content, rel_path, ts_parser, middleware_entry)
            if ast_finding:
                all_findings.append(ast_finding)
            elif Path(rel_path).name.startswith("middleware."):
                # AST check declined (parser unavailable or no match) — fall back to regex
                # so coverage never silently drops when tree-sitter isn't installed.
                all_findings.extend(_regex_findings(content, rel_path, [middleware_entry]))

    return all_findings, len(files)
