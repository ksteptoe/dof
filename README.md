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

# Remove rows for deleted files
dof --prune-missing

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
| `--prune-missing` | Remove rows for files that no longer exist |
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
