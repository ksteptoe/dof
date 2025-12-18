# dof

`dof` scans a directory recursively for common document files and maintains an Excel index (a “treasure map”).

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
```

## Output columns

- File Name
- File Type
- Description (blank by default)
- Date Found
- Link (hyperlink with display text = filename)
- Version (starts at 1.0; increments when file content changes)
- Location (path relative to the scan root)
