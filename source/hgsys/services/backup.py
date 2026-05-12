"""mongodump / mongorestore wrappers.

Each function spawns the corresponding CLI tool and yields stderr lines so the
caller (typically a worker thread) can stream progress.
"""
import subprocess
from collections.abc import Iterator
from pathlib import Path

DATABASE_NAME: str = "hgsystem"
REQUIRED_FILES: tuple[str, ...] = (
    "customers.bson",
    "customers.metadata.json",
    "worksheets.bson",
    "worksheets.metadata.json",
)


def _stream_stderr(command: str) -> Iterator[str]:
    """執行 shell 指令並逐行 yield 其 stderr (已去除 ``\\n`` / 將 ``\\t`` 轉為空白).

    Arg(s):
        command: 完整 shell 指令字串.

    Return(s):
        逐行迭代的 stderr 內容.
    """
    proc = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
    assert proc.stderr is not None
    for raw in proc.stderr:
        yield raw.decode("utf-8").replace("\n", "").replace("\t", " ")


def dump(savepath: str | Path) -> Iterator[str]:
    """執行 ``mongodump -d hgsystem -o <savepath>`` 並 yield stderr 進度行."""
    yield from _stream_stderr(f"mongodump -d {DATABASE_NAME} -o {savepath}")


def restore(savepath: str | Path) -> Iterator[str]:
    """執行 ``mongorestore -d hgsystem --dir <savepath>`` 並 yield stderr 進度行."""
    yield from _stream_stderr(f"mongorestore -d {DATABASE_NAME} --dir {savepath}")


def resolve_restore_dir(chosen: str | Path) -> Path:
    """容許使用者選到 dump 的父層: 若存在 ``<chosen>/hgsystem`` 子目錄則改下鑽."""
    chosen_path = Path(chosen)
    nested = chosen_path / DATABASE_NAME
    return nested if nested.is_dir() else chosen_path


def missing_files(savepath: str | Path) -> list[str]:
    """回傳 ``savepath`` 下缺漏的還原必要檔 (``REQUIRED_FILES`` 為基準).

    Arg(s):
        savepath: 候選的 dump 目錄.

    Return(s):
        缺漏的檔名列表; 完整時為空列表.
    """
    base = Path(savepath)
    return [name for name in REQUIRED_FILES if not (base / name).exists()]
