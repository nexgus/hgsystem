"""mongodump / mongorestore wrappers.

Each function spawns the corresponding CLI tool and yields stderr lines so the
caller (typically a worker thread) can stream progress.
"""
import os
import subprocess
from typing import Iterator

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


def dump(savepath: str) -> Iterator[str]:
    yield from _stream_stderr(f"mongodump -d {DATABASE_NAME} -o {savepath}")


def restore(savepath: str) -> Iterator[str]:
    yield from _stream_stderr(f"mongorestore -d {DATABASE_NAME} --dir {savepath}")


def resolve_restore_dir(chosen: str) -> str:
    """If the user picked the parent of the dumped folder, descend into it."""
    nested = os.path.join(chosen, DATABASE_NAME)
    return nested if os.path.isdir(nested) else chosen


def missing_files(savepath: str) -> list[str]:
    return [
        name
        for name in REQUIRED_FILES
        if not os.path.exists(os.path.join(savepath, name))
    ]
