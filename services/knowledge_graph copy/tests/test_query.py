from services.knowledge_graph.query import entries_relevant_to_version
from services.knowledge_graph.seed_data import NEXTJS_ENTRIES


def test_version_16_includes_middleware_rename():
    relevant = entries_relevant_to_version(NEXTJS_ENTRIES, "16")
    names = {e.api_name for e in relevant}
    assert "middleware.ts convention" in names


def test_version_14_excludes_middleware_rename():
    relevant = entries_relevant_to_version(NEXTJS_ENTRIES, "14")
    names = {e.api_name for e in relevant}
    assert "middleware.ts convention" not in names
    assert "next/image domains config" in names


def test_all_seed_entries_have_detection_patterns():
    for entry in NEXTJS_ENTRIES:
        assert entry.detection_pattern
        assert entry.migration_hint
