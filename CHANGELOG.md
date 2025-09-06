\# Changelog

All notable changes to this project will be documented here.



\## \[0.1.0] - 2025-09-06

\### Added

\- CI pipeline (Ruff, Black check, Pytest + coverage) on Windows (3.10–3.12).

\- Minimal unit tests for import-safety and runtime config loader.

\- README badge for CI status.



\### Changed

\- Refactor: made `eliteparser` import-safe; moved side effects into `main()`.

\- Tray: fixed process stop logic and QMessageBox string.



\### Fixed

\- Lint errors (Ruff): exception chaining, boolean returns, indentation/syntax issues.

\- Formatting via Black across repo.



