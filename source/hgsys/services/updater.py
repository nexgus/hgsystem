"""Self-update via ``git pull`` + ``pip install``.

The legacy app shipped with a 'main → master' fallback because GitHub renamed
the default branch in late 2020. We preserve that behavior.
"""
import os
import subprocess
import sys
from enum import IntEnum
from pathlib import Path
from typing import Optional, Union

import pygit2  # type: ignore

from ..log import get_logger

logger = get_logger()


class PullResult(IntEnum):
    UP_TO_DATE = 0
    FAST_FORWARDED = 1
    UNEXPECTED = 2


_MERGE_RESULT_NAMES = {
    0: "GIT_MERGE_ANALYSIS_NONE",
    1: "GIT_MERGE_ANALYSIS_NORMAL",
    2: "GIT_MERGE_ANALYSIS_UP_TO_DATE",
    4: "GIT_MERGE_ANALYSIS_FASTFORWARD",
    8: "GIT_MERGE_ANALYSIS_UNBORN",
}


def find_repo_root(start_dir: Union[str, Path]) -> Path:
    current = Path(start_dir).resolve()
    while True:
        if (current / ".git").is_dir():
            return current
        if current.parent == current:
            raise FileNotFoundError(f"No git repository found above {start_dir}")
        current = current.parent


def _resolve_remote_ref(repo, remote_name: str, branch: str):
    try:
        return repo.lookup_reference(f"refs/remotes/{remote_name}/{branch}"), branch
    except KeyError:
        if branch == "main":
            return repo.lookup_reference(f"refs/remotes/{remote_name}/master"), "master"
        raise


def pull_and_install(
    repo_root: Union[str, Path],
    remote_name: str = "origin",
    branch: str = "main",
) -> tuple[PullResult, Optional[str]]:
    """Returns (result, detail). ``detail`` describes the merge analysis on UNEXPECTED."""
    repo = pygit2.Repository(str(repo_root))
    logger.info(f"Update application: workdir={repo.workdir}")
    for remote in repo.remotes:
        if remote.name != remote_name:
            continue
        remote.fetch()
        ref, branch = _resolve_remote_ref(repo, remote_name, branch)

        remote_master_id = ref.target
        logger.debug(f"URL - {remote.url}/{ref.shorthand}")

        merge_result, _ = repo.merge_analysis(remote_master_id)
        merge_name = _MERGE_RESULT_NAMES.get(merge_result, f"unknown ({merge_result})")
        logger.debug(f"Merge analysis result: {merge_name} ({merge_result})")

        if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            logger.info("hgsystem is up to date.")
            return PullResult.UP_TO_DATE, None

        if merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
            logger.info("Fast-forward update hgsystem.")
            repo.checkout_tree(repo.get(remote_master_id))
            try:
                master_ref = repo.lookup_reference(f"refs/heads/{branch}")
                master_ref.set_target(remote_master_id)
            except KeyError:
                repo.create_branch(branch, repo.get(remote_master_id))
            repo.head.set_target(remote_master_id)

            requirements = Path(repo.workdir) / "requirements.txt"
            if requirements.exists():
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements)]
                )
            else:
                # Editable install of the package itself if pyproject.toml is present.
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-e", str(repo.workdir)]
                )
            return PullResult.FAST_FORWARDED, None

        return PullResult.UNEXPECTED, f"{merge_name} ({merge_result})"

    return PullResult.UNEXPECTED, f"remote '{remote_name}' not found"


def restart(version_marker_path: Union[str, Path], version_string: str) -> None:
    """Write a marker file so the next launch can show 'updated from X to Y',
    then re-exec the running interpreter with the same argv."""
    Path(version_marker_path).write_text(version_string)
    logger.info("hgsystem is updated. Restart hgsystem.")
    os.execl(sys.executable, sys.executable, "-m", "hgsys", *sys.argv[1:])
