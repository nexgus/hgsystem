package version

// String is the human-readable application version. Used in window titles,
// the "有關" dialog, and the self-update marker.
const String = "0.7.0"

// GitCommitHash and GoVersion are injected at build time via -ldflags by
// build.sh. They default to empty when running `go run` ad-hoc.
var (
	GitCommitHash string
	GoVersion     string
)
