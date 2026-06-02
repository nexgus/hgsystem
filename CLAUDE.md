# CLAUDE.md

Go + Wails v3 desktop app for an optical shop's customer & prescription system
(Traditional Chinese UI, MongoDB-backed, single GUI binary). Build/deploy:
[README.md](README.md); per-version changes: [CHANGE.md](CHANGE.md). This file
covers only what isn't obvious from the code.

## Layout

- `hgsys/` — the Go module is named `hgsys`, but everything user-facing (binary,
  Mongo DB, Wails identity, log dir) is `hgsystem`. Entry + `//go:embed all:dist`
  in `cmd/hgsystem/main.go`.
- `frontend/` — Vue 3 + TS. `src/App.vue` orchestrates the customer/worksheet
  edit-mode interlock. `bindings/` (generated) and `dist/` (built) aren't committed.
- `deprecated/` — old PySide6 code, reference only; **do not add features here**.

## Invariants (migrate data before changing)

- Mongo DB `hgsystem`; collections `customers` / `worksheets` / `search` /
  `titles`. Field mapping: [docs/mongodb.md](docs/mongodb.md).
- Document `_id` is a stringified `ObjectId`, not native BSON ObjectId.
  Worksheets reference customers via `cid`.
- ROC year 0 doesn't exist — `dates.go` and `rocDate.ts` both shift negative
  results by an extra −1; `YEAR_NONE = 9996` is the "year unknown" sentinel.
  Change one side, change both.

## Wails 3 gotchas

- The bindings generator only finds services declared in
  `application.Options.Services` as `application.NewService(&Foo{})`; ones added
  later via `app.RegisterService(...)` are missed. Services needing
  `*application.App` (`BackupService`, `SystemService`) get it via a `SetApp`
  method called from `main.go`.
- `wails3 generate bindings` must run from `hgsys/` with `./cmd/hgsystem` as the
  pattern (build.sh already does this).
- `//go:embed` can't cross `..`, so build.sh copies `frontend/dist/` into
  `hgsys/cmd/hgsystem/dist/` before `go build`.

## Where to look

- Edit-mode interlock lives entirely in `frontend/src/App.vue`; Go services are
  stateless beyond the Mongo connection.
- MSI quirks and the post-build `msibuild` workarounds: [README.md](README.md) §6.2–6.3.
