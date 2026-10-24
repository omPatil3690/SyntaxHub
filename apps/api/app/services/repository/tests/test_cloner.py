import subprocess
from pathlib import Path

import pytest

from services.repository.cloner import clone_repo


@pytest.fixture()
def local_git_repo(tmp_path) -> Path:
    """Creates a real local git repo so the clone path is exercised
    without depending on network access during CI runs. See
    test_clone_real_github_repo below for a network-dependent smoke test.
    """
    repo = tmp_path / "source_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "package.json").write_text('{"dependencies": {"next": "15.0.0"}}')
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def test_clone_local_repo(local_git_repo, tmp_path):
    dest = tmp_path / "cloned"
    result = clone_repo(str(local_git_repo), dest)
    assert (result.path / "package.json").exists()
    assert len(result.commit_sha) == 40


def test_clone_overwrites_existing_dest(local_git_repo, tmp_path):
    dest = tmp_path / "cloned"
    dest.mkdir()
    (dest / "stale_file.txt").write_text("old")
    result = clone_repo(str(local_git_repo), dest)
    assert not (result.path / "stale_file.txt").exists()


@pytest.mark.network
def test_clone_real_github_repo(tmp_path):
    """Network-dependent smoke test — skip in offline CI with `-m "not network"`."""
    dest = tmp_path / "hello-world"
    result = clone_repo("https://github.com/octocat/Hello-World.git", dest)
    assert result.path.exists()
    assert len(result.commit_sha) == 40
