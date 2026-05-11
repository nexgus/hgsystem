# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Chinese-language (Traditional Chinese) PySide2 desktop GUI for an optical shop's customer & prescription management system (豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統). Customers and their worksheets (eyeglass / contact-lens prescriptions) are stored in a local MongoDB database `hgsystem` with collections `customers`, `worksheets`, and `search` (search history). All source lives under `works/`. The app self-updates by `git pull`-ing this repo and re-execing.

## Running

Python is managed via **miniforge3** with a conda environment named `hgsystem`. Activate it before running anything:

```bash
conda activate hgsystem
pip install -r requirements.txt       # deps: dbfread, pymongo, PySide2, pygit2

# from works/
python main.pyw                       # default: MongoDB at localhost:27017
python main.pyw -H <host> -p <port>   # custom MongoDB endpoint
python main.pyw -T                    # test mode (auto-restart instead of "up to date" dialog on Update)
```

A local `mongod` must be running. `mongodump` / `mongorestore` must be on PATH for the backup/restore menu actions (they are invoked via `subprocess`). Logs are written to `works/logs/<YYYYMMDD-HHMMSS>.log` on every launch.

There is no test suite, linter config, or build step. `runhgsystem.bat` is a Windows convenience wrapper assuming the repo lives at `D:\hgsystem`.

## Architecture

The Qt object tree is the architecture — there is no service / repository layer. MongoDB is touched directly from widget callbacks.

- **[works/main.pyw](works/main.pyw)** — `MainWindow`. Owns the `MongoClient`, builds the menu (系統: 更新/有關/離開, 資料: 備份/還原), and embeds a `MainWidget` as central widget. The 更新 action calls `git_pull()` against the parent directory's repo (using `pygit2`), fast-forwards `main` (falls back to `master`), reinstalls `requirements.txt`, writes an `updated` marker file with the old version, then `os.execl`s itself. On next launch the marker is detected and a "已由 X 更新為 Y" dialog is shown. The `search` collection is cleared on every startup.
- **[works/main_widget.py](works/main_widget.py)** — `MainWidget`. The controller: holds a `Customer` panel on top and a `WorkSheet` panel below, wires every button (新增/修改/刪除/查詢/儲存/取消 for both) to a method that mutates MongoDB and toggles `EditMode` on the panels. Customer-side and worksheet-side edit modes are interlocked: editing a customer freezes the history table and inhibits worksheet edits, and vice versa. New documents get a stringified `bson.ObjectId` as `_id`; worksheets carry the customer's `_id` as `cid`.
- **[works/customer.py](works/customer.py)** — `Customer` (composes `Edit` form + `History` table) and `Search` dialog. `History` is a `QTableWidget` showing all worksheets for the selected customer; selecting a row pushes that worksheet into the `WorkSheet` panel via `historyCurrentCellChanged`.
- **[works/worksheet.py](works/worksheet.py)** — `WorkSheet` panel containing the prescription form (`MedicalRecord`: SPH/CYL/AXIS/BASE/BC.V/BC.H/ADD/PD per eye, plus eyesight, lens, frame, prices, memo, dates).
- **[works/widgets.py](works/widgets.py)** — Reusable widgets: `MyLineEdit`, `MyDateWidget` (ROC / 民國 year input), `TaiwanEra` helper.
- **[works/hgsystem.py](works/hgsystem.py)** — Shared module imported as `hg`. Exports `VER_STRING` (bump `VER_MAJOR/MINOR/PATCH/EXTRA` *and* the history docstring on each release — see existing entries), the `FONT` constant (微軟雅黑體 12pt), the `EditMode` enum (`none`/`append`/`modify`/`inhibit`, with stylesheet helpers that color edited fields red), ROC↔Gregorian date converters (`toROCYear`, `toCommonYear`, `toPythonDatetime`, `toROCDateString`), and the module-level `logger` writing to `works/logs/`.
- **[works/backup.py](works/backup.py)** — `BackupRestore` modal dialog. Runs `mongodump -d hgsystem -o <dir>` or `mongorestore -d hgsystem --dir <dir>` in a `QRunnable` worker on a `QThreadPool`, streaming stderr to a `QTextEdit`. Restore requires `customers.bson`/`customers.metadata.json`/`worksheets.bson`/`worksheets.metadata.json` to exist in the chosen folder (or its `hgsystem/` subdir).

## Dates

The domain uses **ROC year** (民國紀年, year - 1911). Year 0 is invalid; year `9996` is the sentinel `YearNone` for "year unknown" (date strings like `MM/DD` with no year). Always go through the helpers in [works/hgsystem.py](works/hgsystem.py:74-109) when converting — `toCommonYear(0)` returns `YearNone`, and `toROCYear` shifts negative results by an extra `-1` to skip the non-existent year 0.

## One-shot migration scripts

`works/0_convert.py`, `works/1_addbc_2eyesight.py`, `works/2_radian2bc.py` are historical, idempotent-once data migrations from a legacy FoxPro `.DBF` database (expected at `works/dbf/gname.DBF` and `works/dbf/gdata.DBF`, gitignored). They are not part of the running app — only re-run them if you're rebuilding the MongoDB from the original DBF dump.
