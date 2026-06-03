# CLAUDE.md

Go + Wails v3 desktop app for an optical shop's customer & prescription system
(Traditional Chinese UI, MongoDB-backed, single GUI binary). Build/deploy:
[README.md](README.md); per-version changes: [CHANGE.md](CHANGE.md). This file
covers only what isn't obvious from the code.

## Layout

- `hgsys/` — the Go module is named `hgsys`, but everything user-facing (binary,
  Mongo DB, Wails identity, log dir) is `hgsystem`. Entry + `//go:embed all:dist`
  in `cmd/hgsystem/main.go`.
- `hgsys/cmd/hgupgrade/` — small standalone self-update helper (downloads the new
  release, swaps the macOS symlink / runs the Windows MSI, relaunches). Embedded
  into hgsystem via `//go:embed` and extracted to a temp dir at update time; see
  [README.md](README.md) §7.
- `frontend/` — Vue 3 + TS. `src/App.vue` orchestrates the customer/worksheet
  edit-mode interlock; `src/About.vue` is the About window (info + third-party
  license tab). `bindings/` (generated) and `dist/` (built) aren't committed, but
  the generated license lists `src/licenses-go.ts` / `src/licenses-frontend.ts`
  are committed (regenerated only by `build.sh --license`; see README §5).
- `scripts/` — dev-only tooling, not shipped. `gen-licenses.sh` + the standalone
  `licgen/` module (own `go.mod`) regenerate the Go third-party license list.
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
  `*application.App` (`BackupService`, `UpdateService`) get it via a `SetApp`
  method called from `main.go`; `UpdateService` also receives the embedded
  `hgupgrade` bytes via `SetUpgrader` there.
- `wails3 generate bindings` must run from `hgsys/` with `./cmd/hgsystem` as the
  pattern (build.sh already does this).
- `//go:embed` can't cross `..`, so build.sh copies `frontend/dist/` into
  `hgsys/cmd/hgsystem/dist/` before `go build`. Likewise the per-platform
  `hgupgrade` binaries under `cmd/hgsystem/hgupgrade/` (selected by build tags)
  must be built before bindings/`go build` or the embed fails — build.sh's
  `build_upgrader` runs first. The `--license` scan (`gen-licenses.sh` runs
  `go list ./cmd/hgsystem`) parses those same embeds, so build.sh sequences it
  after `build_upgrader` too — otherwise a clean checkout aborts before binaries.

## Where to look

- Edit-mode interlock lives entirely in `frontend/src/App.vue`; Go services are
  stateless beyond the Mongo connection.
- Third-party license disclosure (three sources: icon manual in `licenses.ts`,
  Go + frontend npm auto-scanned via `build.sh --license`): [README.md](README.md) §5.
- MSI quirks and the post-build `msibuild` workarounds: [README.md](README.md) §6.2–6.3.
