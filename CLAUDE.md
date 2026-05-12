# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Chinese-language (Traditional Chinese) PySide6 desktop GUI for an optical shop's customer & prescription management system (豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統). Customers and their worksheets (eyeglass / contact-lens prescriptions) are stored in a local MongoDB database `hgsystem` with collections `customers`, `worksheets`, and `search` (search history). The app self-updates by `git pull`-ing this repo and re-execing.

## Repository layout

- **`source/hgsys/`** — **active development.** The rewrite (currently `0.6.0`, PySide6-based). Layered MVVM-ish:
  - `domain/` — pure data types (`models`, `edit_mode`, `dates` — ROC↔Gregorian conversion).
  - `repository/` — MongoDB access for `customers`, `worksheets`, `search_history`.
  - `services/` — `backup` (mongodump/restore wrapper), `updater` (self-update via pygit2).
  - `viewmodels/` — `main`, `customer`, `worksheet`, `search`.
  - `views/` — Qt widgets/dialogs (`main_window`, `main_widget`, `customer`, `worksheet`, `search`, `backup`, `widgets`, `style`).
  - `log.py` — `setup_logging(debug)` + `get_logger()`; emits ANSI-colored console output and a per-launch file `YYMMDD_NNNN.log` (NNNN = same-day serial starting at 0001).
  - `__main__.py` — CLI entry point. Flags: `-H/--host`, `-p/--port`, `-T/--test`, `-d/--debug`.
  - `assets/` — PNG icons bundled via `pyproject.toml`'s `package-data`.
- **`deprecated/`** — the prior PySide2 implementation (formerly `works/`). Kept for reference and for the still-needed parts (data migration scripts, mongodump/mongorestore wrapper). Do **not** add features here — port logic into `source/hgsys/` instead. The legacy architecture notes below describe this codebase so the rewrite can preserve the domain behavior.

The MongoDB database name (`hgsystem`) and document shapes (`_id` as stringified `bson.ObjectId`, worksheets carrying customer `_id` as `cid`) must stay compatible — there is live production data and `deprecated/`'s `mongodump`/`mongorestore` backups must keep restoring cleanly into the rewrite.

## Running

**Python is managed via miniforge3 with a conda environment named `hgsystem`.** All commands below assume `conda activate hgsystem` has been run first; the env supplies the Python interpreter (3.12) and all dependencies listed in `pyproject.toml` (`pymongo`, `PySide6`, `pygit2`). There is no `requirements.txt` — install the package itself in editable mode.

```bash
conda activate hgsystem
pip install -e .                      # installs hgsystem from pyproject.toml

# Rewrite (active):
python -m hgsys                       # default: MongoDB at localhost:27017
python -m hgsys -H <host> -p <port>   # custom MongoDB endpoint
python -m hgsys -T                    # test mode (auto-restart instead of "up to date" dialog on Update)
python -m hgsys -d                    # DEBUG-level console output
# (also installed as a console script: `hgsystem` — see [project.scripts] in pyproject.toml)

# Legacy app (for comparison / reference only):
cd deprecated/
python main.pyw -H <host> -p <port> -T
```

A local `mongod` must be running. `mongodump` / `mongorestore` must be on PATH for the backup/restore menu actions (they are invoked via `subprocess`).

**Logs**: the rewrite writes to the OS-conventional location, not the working directory:
- macOS: `~/Library/Logs/hgsystem/YYMMDD_NNNN.log`
- Windows: `%LOCALAPPDATA%\hgsystem\logs\YYMMDD_NNNN.log`
- Linux fallback: `$XDG_STATE_HOME/hgsystem/logs/` (or `~/.local/state/hgsystem/logs/`)

The legacy app still writes to `deprecated/logs/<YYYYMMDD-HHMMSS>.log` on every launch.

There is no test suite, linter config, or build step. `deprecated/runhgsystem.bat` is a Windows convenience wrapper assuming the repo lives at `D:\hgsystem`.

## Legacy architecture (in `deprecated/`, for reference)

The Qt object tree was the architecture — there was no service / repository layer. MongoDB was touched directly from widget callbacks. The rewrite in `source/hgsys/` is an opportunity to fix that, but the domain behavior below must be preserved.

- **[deprecated/main.pyw](deprecated/main.pyw)** — `MainWindow`. Owns the `MongoClient`, builds the menu (系統: 更新/有關/離開, 資料: 備份/還原), and embeds a `MainWidget` as central widget. The 更新 action calls `git_pull()` against the parent directory's repo (using `pygit2`), fast-forwards `main` (falls back to `master`), reinstalls `requirements.txt`, writes an `updated` marker file with the old version, then `os.execl`s itself. On next launch the marker is detected and a "已由 X 更新為 Y" dialog is shown. The `search` collection is cleared on every startup.
- **[deprecated/main_widget.py](deprecated/main_widget.py)** — `MainWidget`. The controller: holds a `Customer` panel on top and a `WorkSheet` panel below, wires every button (新增/修改/刪除/查詢/儲存/取消 for both) to a method that mutates MongoDB and toggles `EditMode` on the panels. Customer-side and worksheet-side edit modes are interlocked: editing a customer freezes the history table and inhibits worksheet edits, and vice versa. New documents get a stringified `bson.ObjectId` as `_id`; worksheets carry the customer's `_id` as `cid`.
- **[deprecated/customer.py](deprecated/customer.py)** — `Customer` (composes `Edit` form + `History` table) and `Search` dialog. `History` is a `QTableWidget` showing all worksheets for the selected customer; selecting a row pushes that worksheet into the `WorkSheet` panel via `historyCurrentCellChanged`.
- **[deprecated/worksheet.py](deprecated/worksheet.py)** — `WorkSheet` panel containing the prescription form (`MedicalRecord`: SPH/CYL/AXIS/BASE/BC.V/BC.H/ADD/PD per eye, plus eyesight, lens, frame, prices, memo, dates).
- **[deprecated/widgets.py](deprecated/widgets.py)** — Reusable widgets: `MyLineEdit`, `MyDateWidget` (ROC / 民國 year input), `TaiwanEra` helper.
- **[deprecated/hgsystem.py](deprecated/hgsystem.py)** — Shared module imported as `hg`. Exports `VER_STRING` (bump `VER_MAJOR/MINOR/PATCH/EXTRA` *and* the history docstring on each release — see existing entries), the `FONT` constant (微軟雅黑體 12pt), the `EditMode` enum (`none`/`append`/`modify`/`inhibit`, with stylesheet helpers that color edited fields red), ROC↔Gregorian date converters (`toROCYear`, `toCommonYear`, `toPythonDatetime`, `toROCDateString`), and the module-level `logger` writing to `deprecated/logs/`.
- **[deprecated/backup.py](deprecated/backup.py)** — `BackupRestore` modal dialog. Runs `mongodump -d hgsystem -o <dir>` or `mongorestore -d hgsystem --dir <dir>` in a `QRunnable` worker on a `QThreadPool`, streaming stderr to a `QTextEdit`. Restore requires `customers.bson`/`customers.metadata.json`/`worksheets.bson`/`worksheets.metadata.json` to exist in the chosen folder (or its `hgsystem/` subdir).

## Dates

The domain uses **ROC year** (民國紀年, year - 1911). Year 0 is invalid; year `9996` is the sentinel `YearNone` for "year unknown" (date strings like `MM/DD` with no year). The legacy helpers are in [deprecated/hgsystem.py](deprecated/hgsystem.py:74-109) — `toCommonYear(0)` returns `YearNone`, and `toROCYear` shifts negative results by an extra `-1` to skip the non-existent year 0. The rewrite ([source/hgsys/domain/dates.py](source/hgsys/domain/dates.py)) keeps the same sentinel and negative-year shift, otherwise existing stored dates would misround.

## One-shot migration scripts

`deprecated/0_convert.py`, `deprecated/1_addbc_2eyesight.py`, `deprecated/2_radian2bc.py` are historical, idempotent-once data migrations from a legacy FoxPro `.DBF` database (expected at `deprecated/dbf/gname.DBF` and `deprecated/dbf/gdata.DBF`, gitignored). They are not part of the running app — only re-run them if you're rebuilding the MongoDB from the original DBF dump.
