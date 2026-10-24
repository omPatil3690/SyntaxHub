"""
Deterministic framework/dependency version detection from manifest
files. Never infer versions with an LLM — package.json/lockfiles are
ground truth and parsing them is trivial, so there's no reason to.
"""

from _future__ import annotations

import json
import re
from pathlib import Path

from packages.schemas.models import DetectedDependancy

# Frameworks we actively track in the knowledge graph (Phase 4).
# Add entries here as coverage expands to more frameworks.
TRACKED_NPM_PACKAGES = {"next": "nextjs", "react": "react"}


def _strip_semver_prefix(version: str) -> str:
    return re.sub(r"^[\^~>=<]+", "", version).strip()


def detect_from_package_json(repo_root: Path)-> list[DetectedDependancy]:
    pkg_path = repo_root/"package.json"
    if not pkg_path.exists():
        return []

    try:
        data = json.loads(pkg_path.read_text())
    except json.JSONDecodeError:
        return []


    deps = {**data.get("dependencies",{}), **data.get("devDependencies", {})}

    detected = []

    for pkg_name, framework in TRACKED_NPM_PACKAGES.items():
        if pkg_name in deps:
            detected.append(DetectedDependancy(
                framework=framework,
                version = _strip_semver_prefix(deps[pkg_name]),
                ecosystem = "npm",
                source_file="package.json"
            ))


    # Prefer the exact resolved version from a lockfile if present —
        # package.json ranges ("^15.0.0") are less precise than what's installed.
        resolved = _resolve_from_lockfile(repo_root, {d.framework: p for p, d in
                                                        zip(TRACKED_NPM_PACKAGES, detected)})
        for dep in detected:
            pkg_name = next(p for p, f in TRACKED_NPM_PACKAGES.items() if f == dep.framework)
            if pkg_name in resolved:
                dep.version = resolved[pkg_name]
    
        return detected


def _resolve_from_lockfile(repo_root: Path, _unused: dict) -> dict[str, str]:
    resolved: dict[str, str] = {}

    package_lock = repo_root / "package-lock.json"
    if package_lock.exists():
        try:
            data = json.loads(package_lock.read_text())
            packages = data.get("packages", {})
            for pkg_name in TRACKED_NPM_PACKAGES:
                node_path = f"node_modules/{pkg_name}"
                if node_path in packages and "version" in packages[node_path]:
                    resolved[pkg_name] = packages[node_path]["version"]
        except json.JSONDecodeError:
            pass

    return resolved



def detect_from_python_manifests(repo_root: Path) -> list[DetectedDependency]:
    """Stub for Phase 3 Python-ecosystem support (requirements.txt / pyproject.toml).
    Not wired into the knowledge graph yet since Phase 1/4 only seed JS
    frameworks — extend TRACKED_NPM_PACKAGES-equivalent mapping here when
    Python framework tracking (e.g. Django, FastAPI) is added.
    """
    detected: list[DetectedDependency] = []
    req = repo_root / "requirements.txt"
    if req.exists():
        for line in req.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^([A-Za-z0-9_.\-]+)\s*==\s*([\w.]+)", line)
            if m:
                detected.append(DetectedDependency(
                    framework=m.group(1).lower(), version=m.group(2),
                    ecosystem="pip", source_file="requirements.txt",
                ))
    return detected


def detect_dependencies(repo_root: Path) -> list[DetectedDependency]:
    return detect_from_package_json(repo_root) + detect_from_python_manifests(repo_root)

