"""
Orchestrates patch generation for a MigrationPlan: for each planned
change, try the deterministic template first (templates.py); only fall
through to the configured LLM provider if no template exists. Every
patch is emitted as a real unified diff, never a silent file overwrite —
that's a hard requirement carried over from the project spec, not just
a nicety.
"""
from __future__ import annotations

import difflib
from pathlib import Path

from packages.schemas.models import MigrationPlan, Patch
from services.agent import templates
from services.agent.llm_provider import LLMProvider
from services.knowledge_graph.query import find_entry
from packages.schemas.models import KnowledgeGraphEntry


def _make_diff(old: str, new: str, path: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}",
    ))


async def generate_patches(
    plan: MigrationPlan,
    repo_root: Path,
    knowledge_graph_entries: list[KnowledgeGraphEntry],
    llm_provider: LLMProvider,
) -> list[Patch]:
    patches: list[Patch] = []

    for change in plan.changes:
        entry = find_entry(knowledge_graph_entries, change.api)
        for file_path in change.files:
            full_path = repo_root / file_path
            if not full_path.exists():
                continue
            old_content = full_path.read_text(encoding="utf-8", errors="ignore")

            if templates.has_template(change.api):
                result = templates.apply_template(change.api, old_content)
                diff = _make_diff(old_content, result.new_content, file_path)
                if result.suggested_new_filename:
                    diff += f"\n# Note: rename this file to {result.suggested_new_filename} after applying the patch.\n"
                patches.append(Patch(
                    file_path=file_path, diff=diff, new_content=result.new_content,
                    explanation=result.explanation,
                    source="template", doc_url=entry.doc_url if entry else None,
                ))
            else:
                try:
                    new_content = await llm_provider.generate_patch(
                        file_content=old_content,
                        migration_hint=entry.migration_hint if entry else "Apply the recommended migration.",
                        api_name=change.api,
                    )
                except NotImplementedError as exc:
                    patches.append(Patch(
                        file_path=file_path, diff="", new_content=None,
                        explanation=f"SKIPPED (manual review needed): {exc}",
                        source="template", doc_url=entry.doc_url if entry else None,
                    ))
                    continue
                diff = _make_diff(old_content, new_content, file_path)
                patches.append(Patch(
                    file_path=file_path, diff=diff, new_content=new_content,
                    explanation=entry.migration_hint if entry else "LLM-generated migration.",
                    source="llm", doc_url=entry.doc_url if entry else None,
                ))

    return patches
