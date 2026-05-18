# Feature Spec: Refactor Log Formatter

## Summary

Consolidate the three separate log-formatting functions in `internal/logging/` into a single `FormatEntry` function, and rename the `LOG_LEVEL_NUMERIC` constant to `LOG_LEVEL_INT` throughout the package.

## Background

The logging package grew organically and now has three near-identical formatter functions (`formatDebug`, `formatInfo`, `formatWarn`) that differ only in their severity label. This duplication makes future changes error-prone.

## Acceptance criteria

1. A single `FormatEntry(level, message string, fields map[string]string) string` function replaces the three existing formatter functions.
2. The constant `LOG_LEVEL_NUMERIC` is renamed to `LOG_LEVEL_INT` in all files under `internal/logging/`.
3. All call sites in the codebase are updated to use the new function signature and constant name.
4. No behavioral change: output format and field ordering remain byte-for-byte identical to the current output.
5. Existing unit tests continue to pass without modification.

## Out of scope

- Changing the log output format
- Adding new severity levels
- Switching to a third-party logging library
