# CLAUDE.md

Guidance for Claude Code working in this repository. Build / deployment procedure lives in [README.md](README.md); per-version changes in [CHANGE.md](CHANGE.md); this file is for things that aren't obvious from reading the code.

## Project

Go + Wails v3 desktop app for an optical shop's customer & prescription system (豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統). Single GUI binary, MongoDB-backed, Traditional Chinese UI.

## Layout

- `hgsys/` — Go module. Module name is `hgsys` (intentionally different from the user-facing app name `hgsystem`, which is the binary, the cmd subdir, the Mongo DB, the Wails app identity, and the log directory name). `cmd/hgsystem/main.go` holds the entry + `//go:embed all:dist`. `pkg/{domain,repository,services,app,applog,version}/`.
- `frontend/` — Vue 3 + TS + Vite. `src/App.vue` orchestrates state and the customer/worksheet edit-mode interlock. `bindings/` is generated, `dist/` is built — neither committed.
- `msi/hgsystem.wxs.in` — WiX template for the Windows MSI.
- `build.sh` — cross-compile darwin/arm64 + windows/amd64 + MSI. `clear.sh` — wipe artifacts.
- `deprecated/` — old PySide6 code. Reference only; **do not add features here**.

## Invariants

These must not be changed without migrating data first:

- Mongo DB name `hgsystem`, collections `customers` / `worksheets` / `search` / `titles`.
- Document `_id` is a stringified `ObjectId`, not native BSON ObjectId. Worksheets reference customers via `cid`.
- ROC year 0 does not exist — both [hgsys/pkg/domain/dates.go](hgsys/pkg/domain/dates.go) and [frontend/src/lib/rocDate.ts](frontend/src/lib/rocDate.ts) shift negative results by an extra −1; `YEAR_NONE = 9996` is the "year unknown" sentinel. Change one side, change both.

## Wails 3 gotchas

- The bindings generator does static analysis and only finds services declared inside `application.Options.Services` as `application.NewService(&Foo{})`. Services registered later via `app.RegisterService(...)` will not be picked up. Services that need the `*application.App` (currently `BackupService`, `SystemService`) get it via a `SetApp` method called from `main.go` after `application.New` returns.
- `wails3 generate bindings` must run from `hgsys/` (needs `go.mod` in cwd) with `./cmd/hgsystem` as the pattern. `build.sh` already does this.
- `//go:embed` cannot cross `..`, so `frontend/dist/` is copied to `hgsys/cmd/hgsystem/dist/` by `build.sh` before `go build`. Don't try to embed the original.

## Where to look

- Edit-mode interlock (customer panel ↔ worksheet panel) lives entirely in `frontend/src/App.vue`. Go services are stateless beyond the Mongo connection.
- Self-update flow (`SystemService.Update` + `更新` menu) uses the go-git library to fetch + fast-forward from the remote, then runs `go install ./cmd/hgsystem` + `syscall.Exec`. Target machines therefore need a Go toolchain to self-update (the `git` CLI is not required — fetch happens in-process via go-git).
- MSI quirks (wixl ignoring `SummaryCodepage`, missing `=-*PATH` on uninstall) and the post-build `msibuild` patches that work around them: see [README.md](README.md) §6.2–6.3.
