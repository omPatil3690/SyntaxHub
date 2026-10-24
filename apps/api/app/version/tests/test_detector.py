import json
from pathlib import Path

import pytest

from services.version.detector import detect_from_package_json, detect_dependencies


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"next": "^15.5.2", "react": "19.1.0"},
    }))
    return tmp_path


def test_detects_next_and_react(fake_repo):
    deps = detect_from_package_json(fake_repo)
    by_framework = {d.framework: d for d in deps}
    assert by_framework["nextjs"].version == "15.5.2"
    assert by_framework["react"].version == "19.1.0"


def test_prefers_lockfile_resolved_version(fake_repo):
    lockfile = {
        "packages": {
            "node_modules/next": {"version": "15.5.4"},
        }
    }
    (fake_repo / "package-lock.json").write_text(json.dumps(lockfile))
    deps = detect_from_package_json(fake_repo)
    by_framework = {d.framework: d for d in deps}
    assert by_framework["nextjs"].version == "15.5.4"  # from lockfile, not package.json range


def test_no_package_json_returns_empty(tmp_path):
    assert detect_dependencies(tmp_path) == []


def test_requirements_txt_detection(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi==0.115.0\n# a comment\ndjango==5.1.2\n")
    deps = detect_dependencies(tmp_path)
    names = {d.framework: d.version for d in deps}
    assert names["fastapi"] == "0.115.0"
    assert names["django"] == "5.1.2"
