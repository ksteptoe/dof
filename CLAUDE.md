# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`dof` is a CLI tool that scans directories recursively for document files and maintains an Excel "treasure map" index. The tool tracks document metadata including file type, location, version history (via SHA-256 content hashing), and provides hyperlinks to files (with optional SharePoint/OneDrive URL support).

## Core Architecture

### Entry Points
- **CLI**: `src/dof/cli.py` - Click-based CLI that parses arguments and delegates to the API
- **API**: `src/dof/api.py` - Core business logic for scanning, hashing, and Excel generation
- **Package execution**: Users can run via `dof` command or `python -m dof`

### Key Components

**Document Discovery** (`src/dof/api.py:335-373`)
- `discover_documents()`: Recursively scans directories for document files
- Filters by configurable file extensions (DEFAULT_DOCUMENT_SUFFIXES)
- Supports `.treasureignore` files (gitignore-style patterns) to exclude files/directories
- Returns `FoundFile` dataclass instances with SHA-256 fingerprints

**Treasure Map Management** (`src/dof/api.py:552-699`)
- `create_or_update_treasure_map()`: Main function that creates or updates the Excel workbook
- Uses two sheets:
  - `treasure_map`: User-facing sheet with columns: File Name, File Type, Description, Date Found, Last Seen, Link, Version, Location
  - `_dof_meta`: Hidden sheet storing SHA-256 hashes for change detection
- **Versioning logic**:
  - Date Found: Set on first discovery, never changes (first-seen timestamp)
  - Last Seen: Updated every scan when file is present
  - Version: Starts at 1.0, increments (e.g., 1.0 → 1.1) when content hash changes
  - Description: User-editable field preserved across updates

**File Locking Resilience** (`src/dof/api.py:136-165`)
- `_safe_save_workbook()`: Handles Excel/OneDrive file locks gracefully
- Writes to temp file first, attempts atomic replace
- Falls back to `*.NEW.xlsx` if destination is locked

**Ignore Patterns** (`src/dof/api.py:231-316`)
- `.treasureignore` syntax: gitignore-like patterns
- Supports negation (`!pattern`), directory-only patterns (`dir/`), wildcards (`**`)
- Files matching ignore patterns are excluded from scans and removed from existing maps

**Keep Missing Files** (CLI flag: `--keep-missing`)
- By default, rows for files that no longer exist are removed from the treasure map
- Use `--keep-missing` to preserve historical record of deleted files

## Development Commands

### Environment Setup
```bash
make bootstrap              # Create venv and install dev dependencies
make bootstrap VENV="$HOME/.venvs/dof"  # Use alternate venv location (Windows/OneDrive workaround)
make precommit             # Install pre-commit hooks
```

### Testing
```bash
make test                  # Run unit + integration tests (incremental via stamps)
make test-all              # Run all non-live tests (no cache)
make test NO_CACHE=1       # Force re-run cached tests
pytest tests/unit          # Run only unit tests
pytest tests/integration   # Run only integration tests
pytest -v                  # Verbose output
pytest -k test_name        # Run specific test by name
```

The project uses stamp-based incremental testing: tests only re-run when source files, test files, or config changes. Stamps are stored in `.stamps/`.

### Linting & Formatting
```bash
make lint                  # Check code with Ruff (no changes)
make format                # Auto-fix with Ruff
```

Ruff configuration in `pyproject.toml`: line length 120, target Python 3.12+, checks: E, F, I, B.

### Running the CLI
```bash
make run-cli CLI_ARGS="-d /path/to/scan"
dof                        # After installation
dof -d /some/path -o output.xlsx
dof --keep-missing         # Keep rows for deleted files
DOF_SHAREPOINT_BASE_URL="https://..." dof  # Use SharePoint URLs
```

### Build & Release
```bash
make build                 # Build wheel + sdist
make version               # Show setuptools_scm version
make release KIND=patch    # Run tests, create tag, push (patch/minor/major)
make release-show          # Show version info and last tag
```

Versioning uses `setuptools_scm` with Git tags (format: `v1.2.3`).

### Cleanup
```bash
make clean                 # Remove build artifacts, coverage, caches
make clean-tests           # Remove test stamps only
```

## Test Organization

- `tests/unit/`: Fast tests (pure logic, no I/O)
- `tests/integration/`: Filesystem/external tool tests
- Pytest markers: `@pytest.mark.integration`
- Test fixtures use `tmp_path` for isolated file operations

Key test files:
- `tests/unit/test_treasure_map.py`: Core treasure map functionality
- `tests/unit/test_treasure_map_lifecycle.py`: Create/update/delete lifecycle tests
- `tests/integration/test_cli.py`: End-to-end CLI tests

## Code Patterns

### Working with Excel
- Uses `openpyxl` for Excel manipulation
- Always load existing workbooks to preserve user-edited Description fields
- Use `_safe_save_workbook()` to handle file locks
- Column mapping is dynamic (`_ensure_required_headers()`) to support schema evolution

### File Hashing
- Use `_safe_sha256_file()` instead of `_sha256_file()` to handle OneDrive placeholders/locks
- Hash comparison via `_hash_changed()`: only claims change when provable (ignores None values)

### Path Handling
- Use `Path.resolve()` for absolute paths
- Convert to POSIX-style paths for storage in Excel (`_posix_relpath()`)
- All relative paths in treasure map are POSIX-style for cross-platform consistency

### Logging
- Logger: `_logger = logging.getLogger(__name__)`
- Log levels: INFO for progress, WARNING for file locks/fallbacks
- Configured via `setup_logging()` in `api.py`

## Important Constraints

1. **Windows/OneDrive compatibility**: File locking and cloud placeholder files require defensive error handling
2. **Preserve user edits**: Description column must survive treasure map updates
3. **Deterministic output**: Rows sorted by Location for consistent diffs
4. **Version semantics**: Date Found is immutable (first-seen), Version increments on content change, Last Seen updates every scan
5. **Python version**: Requires Python 3.12+

## SharePoint/OneDrive Integration

Set `DOF_SHAREPOINT_BASE_URL` environment variable or use `--sharepoint-base` flag to generate SharePoint hyperlinks instead of local file:// URIs. The base URL should be the SharePoint document library root (e.g., `https://example.sharepoint.com/sites/Team/Shared%20Documents`).
