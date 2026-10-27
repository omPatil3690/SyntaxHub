import shutil
from pathlib import Path

import pytest

from packages.schemas.models import ChangeType, Finding, Severity
from services.agent.llm_provider import TemplateOnlyProvider
from services.agent.orchestrator import generate_patches
from services.knowledge_graph.seed_data import ALL_SEED_ENTRIES
from services.migration.planner import build_plan

FIXTURE_REPO = Path(__file__).parent.parent.parent / "analyzer" / "fixtures" / "sample_repo"


@pytest.fixture()
def repo_copy(tmp_path):
    dest = tmp_path / "repo"
    shutil.copytree(FIXTURE_REPO, dest)
    return dest


@pytest.mark.asyncio
async def test_generates_real_diff_for_middleware(repo_copy):
    finding = Finding(
        file_path="middleware.ts", line=1, api_name="middleware.ts convention",
        matched_text="...", change_type=ChangeType.RENAMED, severity=Severity.HIGH,
        replacement="proxy.ts", migration_hint="rename to proxy",
    )
    plan = build_plan([finding], "nextjs", "15", "16")
    patches = await generate_patches(plan, repo_copy, ALL_SEED_ENTRIES, TemplateOnlyProvider())

    assert len(patches) == 1
    assert patches[0].source == "template"
    assert "-export function middleware(" in patches[0].diff
    assert "+export function proxy(" in patches[0].diff


@pytest.mark.asyncio
async def test_unknown_api_without_llm_is_skipped(repo_copy):
    finding = Finding(
        file_path="middleware.ts", line=1, api_name="some future unmapped api",
        matched_text="...", change_type=ChangeType.DEPRECATED, severity=Severity.LOW,
        replacement=None, migration_hint="do something",
    )
    plan = build_plan([finding], "nextjs", "15", "16")
    patches = await generate_patches(plan, repo_copy, ALL_SEED_ENTRIES, TemplateOnlyProvider())

    assert len(patches) == 1
    assert patches[0].diff == ""
    assert "SKIPPED" in patches[0].explanation
