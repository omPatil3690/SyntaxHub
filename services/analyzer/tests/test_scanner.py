from pathlib import Path

from services.analyzer.scanner import scan_repository
from services.knowledge_graph.seed_data import ALL_SEED_ENTRIES

FIXTURE_REPO = Path(__file__).parent.parent / "fixtures" / "sample_repo"


def test_finds_middleware_rename():
    findings, files_scanned = scan_repository(FIXTURE_REPO, ALL_SEED_ENTRIES)
    apis = {f.api_name for f in findings}
    assert "middleware.ts convention" in apis
    assert files_scanned == 3


def test_finds_react_legacy_apis():
    findings, _ = scan_repository(FIXTURE_REPO, ALL_SEED_ENTRIES)
    apis = {f.api_name for f in findings}
    assert "ReactDOM.render" in apis
    assert "componentWillMount / componentWillReceiveProps / componentWillUpdate" in apis
    assert "String refs" in apis


def test_modern_file_contributes_no_findings():
    findings, _ = scan_repository(FIXTURE_REPO, ALL_SEED_ENTRIES)
    modern_findings = [f for f in findings if f.file_path.endswith("Modern.jsx")]
    assert modern_findings == []


def test_findings_have_correct_line_numbers():
    findings, _ = scan_repository(FIXTURE_REPO, ALL_SEED_ENTRIES)
    render_finding = next(f for f in findings if f.api_name == "ReactDOM.render")
    assert render_finding.line == 13  # the actual line in the fixture file
