"""
Query layer the analyzer and migration planner call into. Deliberately
thin — the graph is small enough that in-memory filtering after one
fetch-per-framework is fine; revisit only if entry counts grow into the
thousands.
"""
from __future__ import annotations

from packages.schemas.models import KnowledgeGraphEntry


def entries_relevant_to_version(
    entries: list[KnowledgeGraphEntry], current_version: str
) -> list[KnowledgeGraphEntry]:
    """Filter to entries whose deprecated/removed cutoff is <= the version
    the repo is currently on to decide, i.e. changes that already apply.
    Version comparison here is intentionally simple (major-version only);
    extend with proper semver comparison if you need minor-version precision.
    """
    def major(v: str) -> int:
        try:
            return int(v.split(".")[0])
        except (ValueError, IndexError):
            return 0

    current_major = major(current_version)
    relevant = []
    for e in entries:
        cutoff = e.deprecated_in or e.removed_in
        if cutoff is None:
            continue
        if major(cutoff) <= current_major:
            relevant.append(e)
    return relevant


def find_entry(entries: list[KnowledgeGraphEntry], api_name: str) -> KnowledgeGraphEntry | None:
    return next((e for e in entries if e.api_name == api_name), None)
