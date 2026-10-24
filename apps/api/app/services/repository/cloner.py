"""
Clones a repo (shallow, for speed) into a working directory. Kept
deliberately simple — subprocess + git, no GitPython dependency needed
for a shallow clone, which is all the scanner (Phase 5/6) needs.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClonedRepo:
    path: Path
    commit_sha: str


def clone_repo(repo_url: str, dest_dir: Path, ref: str | None = None) -> ClonedRepo:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["git", "clone", "--depth", "1"]
    if ref:
        cmd += ["--branch", ref]
    cmd += [repo_url, str(dest_dir)]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed: {proc.stderr.strip()}")

    sha_proc = subprocess.run(
        ["git", "-C", str(dest_dir), "rev-parse", "HEAD"], capture_output=True, text=True,
    )
    commit_sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else "unknown"

    return ClonedRepo(path=dest_dir, commit_sha=commit_sha)
