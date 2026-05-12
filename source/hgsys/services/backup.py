"""mongodump / mongorestore wrappers.

Each function spawns the corresponding CLI tool and yields stderr lines so the
caller (typically a worker thread) can stream progress.
"""
import subprocess
from pathlib import Path
from typing import Iterator, Union

DATABASE_NAME = "hgsystem"
REQUIRED_FILES = (
    "customers.bson",
    "customers.metadata.json",
    "worksheets.bson",
    "worksheets.metadata.json",
)


def _stream_stderr(command: str) -> Iterator[str]:
    proc = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
    assert proc.stderr is not None
    for raw in proc.stderr:
        yield raw.decode("utf-8").replace("\n", "").replace("\t", " ")


def dump(savepath: Union[str, Path]) -> Iterator[str]:
    yield from _stream_stderr(f"mongodump -d {DATABASE_NAME} -o {savepath}")


def restore(savepath: Union[str, Path]) -> Iterator[str]:
    yield from _stream_stderr(f"mongorestore -d {DATABASE_NAME} --dir {savepath}")


def resolve_restore_dir(chosen: Union[str, Path]) -> Path:
    """If the user picked the parent of the dumped folder, descend into it."""
    chosen_path = Path(chosen)
    nested = chosen_path / DATABASE_NAME
    return nested if nested.is_dir() else chosen_path


def missing_files(savepath: Union[str, Path]) -> list[str]:
    base = Path(savepath)
    return [name for name in REQUIRED_FILES if not (base / name).exists()]
