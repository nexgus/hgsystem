"""Self-update via ``git pull`` + ``pip install``.

The legacy app shipped with a 'main → master' fallback because GitHub renamed
the default branch in late 2020. We preserve that behavior.
"""
import logging
import os
import subprocess
import sys
from enum import IntEnum
from pathlib import Path

import pygit2  # type: ignore

from ..log import get_logger

logger: logging.Logger = get_logger()


class PullResult(IntEnum):
    """``pull_and_install`` 的結果.

    - ``UP_TO_DATE``: 已是最新版本, 無需重啟.
    - ``FAST_FORWARDED``: 已 fast-forward 至 remote, 應呼叫 ``restart``.
    - ``UNEXPECTED``: 無法處理 (非 fast-forward, 或找不到 remote).
    """

    UP_TO_DATE = 0
    FAST_FORWARDED = 1
    UNEXPECTED = 2


_MERGE_RESULT_NAMES: dict[int, str] = {
    0: "GIT_MERGE_ANALYSIS_NONE",
    1: "GIT_MERGE_ANALYSIS_NORMAL",
    2: "GIT_MERGE_ANALYSIS_UP_TO_DATE",
    4: "GIT_MERGE_ANALYSIS_FASTFORWARD",
    8: "GIT_MERGE_ANALYSIS_UNBORN",
}


def find_repo_root(start_dir: str | Path) -> Path:
    """從 ``start_dir`` 向上找出含 ``.git`` 目錄的 repo root.

    Arg(s):
        start_dir: 開始搜尋的目錄.

    Return(s):
        repo root 的絕對路徑.

    Raise(s):
        FileNotFoundError: 一路找到檔案系統根目錄都沒有 ``.git``.
    """
    current = Path(start_dir).resolve()
    while True:
        if (current / ".git").is_dir():
            return current
        if current.parent == current:
            raise FileNotFoundError(f"No git repository found above {start_dir}")
        current = current.parent


def _resolve_remote_ref(repo, remote_name: str, branch: str):
    """查 ``refs/remotes/<remote>/<branch>``; 找不到 ``main`` 時 fallback 到 ``master``.

    Return(s):
        (reference, 實際使用的 branch 名稱).
    """
    try:
        return repo.lookup_reference(f"refs/remotes/{remote_name}/{branch}"), branch
    except KeyError:
        if branch == "main":
            return repo.lookup_reference(f"refs/remotes/{remote_name}/master"), "master"
        raise


def pull_and_install(
    repo_root: str | Path,
    remote_name: str = "origin",
    branch: str = "main",
) -> tuple[PullResult, str | None]:
    """從 ``remote_name/branch`` 抓取並 fast-forward, 必要時重裝依賴.

    僅處理「up-to-date」與「fast-forward」兩種乾淨情境; 其它 merge analysis
    結果一律視為 ``UNEXPECTED``. fast-forward 後若 repo 內有 ``requirements.txt``
    便 ``pip install -r``, 否則 ``pip install -e <workdir>``.

    Arg(s):
        repo_root: 本地 repo 的根目錄.
        remote_name: 要 fetch 的 remote, 預設 ``origin``.
        branch: 目標分支; 找不到 ``main`` 時自動 fallback 到 ``master``.

    Return(s):
        ``(PullResult, detail)``; ``detail`` 僅在 ``UNEXPECTED`` 時非 ``None``,
        說明遇到的 merge analysis 名稱或找不到的 remote.
    """
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


def restart(version_marker_path: str | Path, version_string: str) -> None:
    """寫入 marker 後以 ``os.execl`` 重新啟動本程式.

    Marker 內容為當前版本字串, 下次啟動時讀到便可顯示「已由 X 更新為 Y」.

    Arg(s):
        version_marker_path: marker 檔的完整路徑.
        version_string: 寫入 marker 的版本字串 (通常為更新前的版本).
    """
    Path(version_marker_path).write_text(version_string)
    logger.info("hgsystem is updated. Restart hgsystem.")
    os.execl(sys.executable, sys.executable, "-m", "hgsys", *sys.argv[1:])
