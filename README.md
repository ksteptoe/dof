# dof

`dof` scans a directory recursively for common document files and maintains an Excel index (a "treasure map").

## Installation

```bash
pip install dof
```

## CLI

```bash
# Scan current directory and write ./treasure_map.xlsx
dof

# Scan a specific directory
dof -d /path/to/root

# Choose output filename
dof -d . -o my_map.xlsx

# Use a SharePoint/OneDrive base URL for hyperlinks
export DOF_SHAREPOINT_BASE_URL="https://example.sharepoint.com/sites/Team/Shared%20Documents"
dof -d .

# Preview changes without writing (dry run)
dof --dry-run

# Output as JSON or CSV instead of Excel
dof --format json
dof --format csv

# Keep rows for deleted files (default: remove them)
dof --keep-missing

# Don't exit non-zero when broken links are found
dof --keep-missing --no-fail-on-broken

# Turn off move tracking (a move becomes a deletion plus a new document)
dof --no-detect-moves

# Disable progress indicator
dof --no-progress

# Verbose logging
dof -v      # info level
dof -vv     # debug level
```

## CLI Options

| Option | Description |
|--------|-------------|
| `-d, --dir PATH` | Directory to scan (default: current directory) |
| `-o, --output PATH` | Output filename (default: `treasure_map.xlsx`) |
| `--format [xlsx\|json\|csv]` | Output format (default: `xlsx`) |
| `--dry-run` | Show what would change without writing files |
| `--keep-missing` | Keep rows for files that no longer exist (default: remove) |
| `--no-detect-moves` | Treat a moved or renamed file as a deletion plus a new document (default: track the move) |
| `--no-fail-on-broken` | Exit 0 even when broken links are found (default: exit 2) |
| `--sharepoint-base URL` | Base SharePoint/OneDrive URL for hyperlinks |
| `--progress / --no-progress` | Show/hide progress during scan (default: show) |
| `-v, --verbose` | Enable info-level logging |
| `-vv, --very-verbose` | Enable debug-level logging |
| `-h, --help` | Show help message |
| `--version` | Show version |

## Output Columns

| Column | Description |
|--------|-------------|
| File Name | Name of the document file |
| File Type | Document type (PDF, Word, Excel, etc.) |
| Description | User-editable notes (preserved across updates) |
| Date Found | First time the file was discovered (immutable) |
| Last Seen | Most recent scan where the file was present |
| Link | Clickable hyperlink to the file |
| Version | Starts at 1.0; increments when content changes |
| Location | Path relative to the scan root (POSIX-style) |
| Status | `OK`, `Moved` or `Broken` for the current scan |
| Previous Location | Where the file was before it last moved (blank if it never has) |

## Tracking Moved Files

Rows used to be keyed solely on `Location`, so reorganising a folder tree made every
moved document look like a deletion plus a brand-new file. Its `Date Found`, your
hand-written `Description` and its whole `Version` history were all lost, and the
hyperlinks in any copy of the map you had already circulated pointed at nothing.

dof now recognises a moved or renamed document and relinks the existing row to its new
path, keeping `Date Found`, `Description` and `Version` intact. Matching happens in
three tiers:

1. **Identical content.** A discovered file whose SHA-256 matches an orphaned row is
   the same document: the row is relinked and its `Version` is left alone. This covers
   plain moves and renames.
2. **Same name, size and file type.** Treated as the same document, moved *and* edited:
   the row is relinked **and** its `Version` is bumped (e.g. `1.0` → `1.1`).
3. **No match.** The file is treated as genuinely new, and the old row is pruned (or
   marked `Broken` under `--keep-missing`).

Empty files never pair. Every zero-byte file shares the same hash and the same size, so
neither signal is evidence of anything; such files always fall through to tier 3. A file
dof could not hash or measure is likewise never paired — it degrades to "deleted plus
new" rather than guessing.

Tier 2 is a probabilistic match. Two unrelated files of the same name, size and type —
say an `invoice.docx` template in two departments, one removed and one added in the same
scan — can be paired wrongly. `Previous Location` makes that visible and auditable.

If that ever happens to you, `--no-detect-moves` is the escape hatch. It turns matching
off altogether and restores the pre-feature behaviour: a moved file is reported as a
deletion plus a new document, losing `Date Found`, `Description` and `Version` but never
pairing two unrelated files. Move tracking is on by default.

### Worked example

Say you start with this tree and run `dof`:

```text
docs/
  proposal.pdf
  notes/meeting.docx
```

| File Name | Version | Location | Status | Previous Location |
|---|---|---|---|---|
| proposal.pdf | 1.0 | docs/proposal.pdf | OK | |
| meeting.docx | 1.0 | docs/notes/meeting.docx | OK | |

You add a description to `proposal.pdf` in Excel, then restructure: `docs/` becomes
`archive/2025/`, and you edit `meeting.docx` while you are there (without changing its
byte length). Rescanning gives:

| File Name | Version | Location | Status | Previous Location |
|---|---|---|---|---|
| proposal.pdf | 1.0 | archive/2025/proposal.pdf | Moved | docs/proposal.pdf |
| meeting.docx | 1.1 | archive/2025/notes/meeting.docx | Moved | docs/notes/meeting.docx |

Both descriptions and both `Date Found` dates survive. `proposal.pdf` kept version `1.0`
(tier 1, content unchanged); `meeting.docx` went to `1.1` (tier 2, moved and edited).
The CLI reports:

```text
Moved files:
  > docs/proposal.pdf -> archive/2025/proposal.pdf
  > docs/notes/meeting.docx -> archive/2025/notes/meeting.docx
```

`Previous Location` is sticky: once written it stays, so someone holding an older copy of
the map can still work out where a document went. `Status`, by contrast, describes the
current scan only — it reverts to `OK` on the next scan that finds the file where the map
says it is.

## Broken Links

A row whose target cannot be resolved is marked `Status = Broken`, highlighted red in the
workbook, and listed under `Broken links:` in the CLI output. **dof then exits with code
2.**

This mostly arises with `--keep-missing`, which deliberately keeps rows for files that
are gone. Pass `--no-fail-on-broken` to keep the marking and the report but exit 0:

```bash
dof --keep-missing --no-fail-on-broken
```

Link checking never touches the network. A `file://` target resolves when the path exists
on disk; a SharePoint target resolves when its path, taken relative to the configured base
URL, matches something found in this scan. A hand-pasted `http(s)://` link with no
`--sharepoint-base` configured is always treated as resolvable, because dof has no offline
way to judge it — so a genuinely dead SharePoint URL for a file that *is* present locally
still reports `OK`.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (see the message) |
| 2 | Broken links present (suppress with `--no-fail-on-broken`) |

## Ignore Patterns

Create a `.treasureignore` file in the scan root to exclude files using gitignore-style patterns:

```gitignore
# Ignore all .tmp files
*.tmp

# Ignore build directory
build/

# Ignore specific file
secret.pdf

# But keep this one
!important.pdf
```

## Supported File Types

Office: `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.rtf`
Text: `.txt`, `.md`, `.rst`, `.csv`, `.json`, `.yaml`, `.xml`, `.toml`
PDF: `.pdf`
Other: `.odt`, `.ods`, `.odp`, `.pages`, `.numbers`, `.key`, `.epub`, `.tex`
