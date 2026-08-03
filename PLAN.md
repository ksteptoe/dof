# PLAN — move detection, Status column, broken-link reporting

Target: `dof` treasure map (`src/dof/api.py`, `src/dof/cli.py`).
Bug: rows are keyed solely by `Location`, so a moved/renamed file is reported as
`deleted` + `new`, losing Date Found, Description and Version, and breaking links in
distributed copies of the map.

Everything below is scoped to the smallest diff that satisfies the request. **No new
runtime dependencies** — `hashlib`, `pathlib`, `openpyxl.styles.PatternFill` and
`urllib.parse.unquote` are all already available (`PatternFill` is a new import from a
package already in `dependencies`).

---

## Open decisions (need the user's answer before/while coding)

1. **How the CLI learns about broken links on a real (non-dry-run) write.**
   `create_or_update_treasure_map()` currently returns `Path | ScanResult` — a real run
   returns only the `Path`, so the CLI has nothing to print or exit non-zero on.
   *Recommendation:* add keyword-only `with_result: bool = False` to both
   `create_or_update_treasure_map()` and `dof_api()`; when true they return
   `WriteOutcome(path: Path, scan: ScanResult)` (new frozen dataclass). Default `False`
   keeps every existing test and caller working unchanged. The CLI always passes
   `with_result=True`. Alternative rejected: changing the return type unconditionally
   (breaks existing tests and any programmatic caller).
2. **`--no-fail-on-broken` escape hatch.** *Recommendation: yes, add it.* A map scanned
   with `--keep-missing` is *expected* to contain broken rows (that is the point of the
   flag), so a hard non-zero exit would make `dof --keep-missing` permanently red in any
   cron/CI wrapper. The flag is cheap and the default stays strict (exit 2 on broken).
   Confirm you want the flag and want the default to remain strict.
3. **Exit code value.** *Recommendation: `2`* (`sys.exit(2)` via `click.exceptions.Exit`),
   leaving `1` for genuine errors and `0` for clean. Confirm.
4. **`Previous Location` persistence.** *Recommendation: retain it indefinitely* once
   written; only overwritten when a *newer* move is detected for that row. Justification:
   the column's job is to let a human holding an old copy of the map find where a document
   went; clearing it on the next unchanged scan destroys that information within one run
   and makes the column useless in practice. Stated as a fixed decision in the plan below
   — say so if you want single-scan semantics instead.
5. **Tier 2 minimum size.** Same-name + same-size + same-type is a weak signal for
   zero-byte files (every empty `.txt` matches every other). *Recommendation:* skip Tier 2
   when `size == 0`; such files fall through to Tier 3 (new row). Confirm.

---

## Fixed decisions (already made by the user — not re-opened)

- Three-tier matching: Tier 1 exact hash → move; Tier 2 name+size+type → move-with-edit
  (relink **and** bump Version); Tier 3 → new row.
- `Status` column with `OK` / `Moved` / `Broken`; broken rows red-filled, listed in the CLI
  summary, non-zero exit.
- `Previous Location` column.
- Size recorded on `FoundFile` and in the hidden `_dof_meta` sheet.
- No network calls when validating links.

---

## Increments

Each increment ends green (`make lint && make test`) and is committable alone.

### Increment 1 — capture file size (coder, tester)
Goal: `FoundFile` carries `size`, and the meta sheet round-trips `Location → (Sha256, Size)`
with backwards-compatible load of existing 2-column workbooks.
Files: `src/dof/api.py`, `tests/unit/test_treasure_map.py`.
Done when: an existing workbook with only `Location`/`Sha256` loads, gains a `Size` header
on save, and no behaviour changes; `make test` green.

### Increment 2 — new columns, no logic (coder, tester, documenter)
Goal: `Status` and `Previous Location` appended to `REQUIRED_COLUMNS`; every new/existing
row gets `Status = "OK"` and `Previous Location = ""`. Exporters and `_row_to_dict` follow
automatically; verify JSON/CSV field order and existing assertions.
Files: `src/dof/api.py`, tests touching column lists.
Done when: an old workbook upgrades in place with the two new columns appended right of
existing ones, user column edits preserved.

### Increment 3 — move detection (coder, tester)
Goal: the three-tier matcher, run after the same-location pass and before prune/ignore.
Files: `src/dof/api.py`, `tests/unit/test_moves.py` (new).
Done when: all acceptance criteria M1–M12 below pass.

### Increment 4 — broken-link detection, Status painting, ScanResult (coder, tester)
Goal: `_link_is_resolvable()`, `Status = "Broken"` + red fill/font, `ScanResult.moved_files`
/ `broken_links`, `ChangeType.MOVED` / `ChangeType.BROKEN`, extended `summary()`.
Files: `src/dof/api.py`, `tests/unit/test_broken_links.py` (new).
Done when: acceptance criteria B1–B7 pass.

### Increment 5 — CLI plumbing (coder, tester)
Goal: `WriteOutcome`, `with_result`, `--no-fail-on-broken`, moved/broken sections in the
CLI output, non-zero exit.
Files: `src/dof/cli.py`, `src/dof/api.py`, `tests/integration/test_cli.py`.
Done when: acceptance criteria C1–C5 pass.

### Increment 6 — docs (documenter) and CI check (ci)
Files: `README.md`, `docs/treasure_map.rst`, `docs/cli.rst`, `CHANGELOG.rst`, docstrings.

---

## coder

All changes in `src/dof/api.py` unless stated.

### Data structures

```python
REQUIRED_COLUMNS = [
    "File Name", "File Type", "Description", "Date Found", "Last Seen",
    "Link", "Version", "Location",
    "Status",              # NEW — OK | Moved | Broken
    "Previous Location",   # NEW — prior POSIX relpath, blank if never moved
]

STATUS_OK = "OK"
STATUS_MOVED = "Moved"
STATUS_BROKEN = "Broken"

BROKEN_FILL = PatternFill(start_color="FFFFC7CE", end_color="FFFFC7CE", fill_type="solid")
BROKEN_FONT = Font(color="FF9C0006")   # Excel's standard "Bad" style colours
```

```python
class ChangeType(Enum):
    NEW = "new"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    DELETED = "deleted"
    IGNORED = "ignored"
    MOVED = "moved"        # NEW
    BROKEN = "broken"      # NEW


@dataclass
class FileChange:
    location: str
    change_type: ChangeType
    old_version: Optional[str] = None
    new_version: Optional[str] = None
    previous_location: Optional[str] = None   # NEW, set for MOVED


@dataclass(frozen=True)
class FoundFile:
    abs_path: Path
    rel_location: str
    filename: str
    suffix: str
    file_type: str
    sha256: Optional[str]
    size: Optional[int] = None      # NEW, keyword-safe default keeps existing construction valid


@dataclass(frozen=True)
class MetaEntry:
    """Per-file fingerprint stored on the hidden meta sheet."""
    sha256: Optional[str] = None
    size: Optional[int] = None


@dataclass(frozen=True)
class WriteOutcome:
    """Returned by ``create_or_update_treasure_map(..., with_result=True)``."""
    path: Path
    scan: ScanResult
```

`ScanResult` gains:

```python
moved_files: List[Tuple[str, str]] = field(default_factory=list)  # (old_location, new_location)
broken_links: List[str] = field(default_factory=list)             # locations whose link cannot resolve
```

`summary()` appends, after Unchanged and before Deleted:
`  Moved:     {n}` when non-empty; and after Ignored:
`  Broken:    {n}` when non-empty.
Existing lines and their wording are unchanged (tests assert on them).

### Size capture

- `_safe_file_size(path: Path) -> Optional[int]` — mirrors `_safe_sha256_file`; returns
  `path.stat().st_size`, catching `(PermissionError, OSError)` → `None`. OneDrive
  placeholders and locks must not raise.
- `discover_documents()` populates `size=_safe_file_size(p)`.

### Meta sheet migration

- `_meta_headers(meta_ws)` — when the sheet already has headers but no `"Size"` column,
  append `"Size"` at `max_column + 1` and return it in the mapping. When creating fresh,
  write `Location`, `Sha256`, `Size`.
- `_read_meta(meta_ws) -> Dict[str, MetaEntry]` — **return type changes**. Reads `Sha256`
  as before; reads `Size` only if the column exists, coercing via
  `int(v)` inside `try/except (TypeError, ValueError)` → `None`. No test currently touches
  `_read_meta`/`_write_meta` (verified), so this is internal-only.
- `_write_meta(meta_ws, meta: Dict[str, MetaEntry])` — writes all three columns, still
  sorted by lowercased location.
- Every `meta[loc] = f.sha256` in the main loop becomes
  `meta[loc] = MetaEntry(f.sha256, f.size)`, and `prev_sha = meta.get(loc)` becomes
  `prev = meta.get(loc)` / `prev_sha = prev.sha256 if prev else None`.

### Move detection

New public-ish helper, called from `create_or_update_treasure_map` **after** the existing
`for f in found:` loop and **before** the `.treasureignore` removal and prune blocks:

```python
def _detect_moves(
    *,
    found: List[FoundFile],
    matched_locations: Set[str],
    updated_rows: Dict[str, Dict[str, object]],
    meta: Dict[str, MetaEntry],
    existing_rows: Dict[str, Dict[str, object]],
    found_locations: Set[str],
) -> List[Tuple[str, str]]:
    """Relink rows whose file has moved. Returns [(old_location, new_location)]."""
```

Restructuring the main loop: today the loop creates a new row immediately in the `else`
branch. Change it to **defer**: collect `unmatched_found: List[FoundFile]` instead of
creating the row, run `_detect_moves`, then create rows for whatever is still unmatched.
`matched_locations` is the set of `loc` handled by the same-location branch.

#### Algorithm (precise)

```
INPUTS
  unmatched_found : found files with no row at their own location
  orphan_rows     : {loc: row for loc in updated_rows
                    if loc not in found_locations}          # row exists, path gone
  meta            : loc -> MetaEntry

# ---------- TIER 1: exact SHA-256 ----------
# Build indexes, skipping unusable keys.
by_hash_orphan : sha -> [loc, ...]      for loc in orphan_rows if meta[loc].sha256 is not None
by_hash_found  : sha -> [f, ...]        for f in unmatched_found if f.sha256 is not None

for sha in sorted(by_hash_orphan.keys() & by_hash_found.keys()):
    olocs = sorted(by_hash_orphan[sha], key=str.lower)
    fs    = sorted(by_hash_found[sha], key=lambda f: f.rel_location.lower())
    # Pair greedily, preferring identical basenames, then sorted order.
    pairs = []
    remaining_f = list(fs)
    for oloc in olocs:                                   # deterministic outer order
        obase = PurePosixPath(oloc).name.lower()
        cand = first f in remaining_f where f.filename.lower() == obase   # tie-break 1
        if cand is None:
            cand = remaining_f[0] if remaining_f else None                # tie-break 2
        if cand is None:
            break                                        # more orphans than found: rest stay deleted/broken
        remaining_f.remove(cand)
        pairs.append((oloc, cand))
    for (oloc, f) in pairs:
        relink(oloc, f, bump_version=False)

# ---------- TIER 2: name + size + type ----------
# Only among what Tier 1 left over. Key is (lower filename, size, file type).
by_key_orphan : key -> [loc, ...]   built from the ROW's File Name / File Type and meta[loc].size
by_key_found  : key -> [f, ...]     built from f.filename / f.size / f.file_type
skip any key whose size is None or 0            # see Open decision 5
for key in sorted(by_key_orphan.keys() & by_key_found.keys()):
    pair 1:1 in sorted order (orphans by lowercased loc, found by lowercased rel_location)
    for each pair: relink(oloc, f, bump_version=True)

# ---------- TIER 3 ----------
# every still-unmatched FoundFile becomes a new row (existing code path)
```

`relink(old_loc, f, bump_version)`:

```
row = updated_rows.pop(old_loc)
meta.pop(old_loc, None)
row["Location"]           = f.rel_location
row["File Name"]          = f.filename
row["File Type"]          = f.file_type
row["Previous Location"]  = old_loc
row["Status"]             = STATUS_MOVED
row["Last Seen"]          = today
# Date Found and Description are NOT touched — invariant preserved.
if bump_version:
    row["Version"] = _bump_version(row.get("Version"))
row["Link"] = {"target": _build_sharepoint_url(sharepoint_base_url, f.rel_location, f.abs_path),
               "text": f.filename}
updated_rows[f.rel_location] = row
meta[f.rel_location] = MetaEntry(f.sha256, f.size)
scan_result.moved_files.append((old_loc, f.rel_location))
scan_result.changes.append(FileChange(f.rel_location, ChangeType.MOVED,
                                      old_version, row["Version"],
                                      previous_location=old_loc))
```

Hard invariants the implementation must guarantee:

- **Never merge two rows.** `updated_rows[f.rel_location] = row` must only run when
  `f.rel_location` is not already a key (it cannot be, because `unmatched_found` excludes
  files whose own location matched a row — assert this defensively).
- **Never consume a `FoundFile` twice** — the greedy pairing removes from `remaining_f`.
- **Never match on `None`.** A file that failed to hash has `sha256 is None` and is
  excluded from Tier 1 entirely; a file whose size is unreadable is excluded from Tier 2.
  Degrade to "deleted + new", never guess.
- Determinism: all iteration over sets/dicts goes through `sorted(...)`, lowercased keys.

Rows relinked by a move are, by construction, no longer missing, so the `prune_missing`
block leaves them alone (it tests `loc not in found_locs` on the *new* location).

### Retaining `Previous Location`

On a later scan where the file is found at its own location (the same-location branch),
**do not clear** `Previous Location`, and set `Status` back to `STATUS_OK` only if the row
is resolvable. That is: `Status` reflects the *current* scan; `Previous Location` is
historical and sticky. (Open decision 4.)

### Broken links

```python
def _link_is_resolvable(
    row: Dict[str, object],
    *,
    root_dir: Path,
    found_locations: Set[str],
    sharepoint_base_url: Optional[str],
) -> bool:
    """Return True when this row's Link target can be resolved without network access.

    A ``file://`` target resolves when the referenced path exists on disk. A
    SharePoint target resolves when its path, relative to the configured base URL,
    matches a location discovered in this scan.
    """
```

Rules:
- Target taken from `row["Link"]["target"]` when the row was written this run, else from
  the preserved `__link_target` on the existing row, else the row's Location resolved
  against `root_dir`.
- `file://` → `Path(url2pathname(urlparse(t).path)).exists()`; simpler and sufficient:
  `(root_dir / row["Location"]).exists()` when the target was generated by dof. Use the
  URL form only when a target is present and starts with `file:`.
- `http(s)://` with `sharepoint_base_url` set → strip the base prefix, `unquote` the
  remainder, and require it in `found_locations`. **No network call.**
- `http(s)://` with no configured base (a link a user pasted in by hand) → treat as
  resolvable; dof cannot judge it and must not flag user data as broken.
- Anything else / empty target → resolvable if `(root_dir / Location).exists()`.

Applied in a final pass over `updated_rows` after prune/ignore, just before writing:

```
for loc in sorted(updated_rows):
    row = updated_rows[loc]
    if _link_is_resolvable(row, ...):
        if row.get("Status") != STATUS_MOVED:
            row["Status"] = STATUS_OK
    else:
        row["Status"] = STATUS_BROKEN
        scan_result.broken_links.append(loc)
        scan_result.changes.append(FileChange(loc, ChangeType.BROKEN))
```

Note this pass runs for **all** output formats and for `dry_run`, so JSON/CSV exports and
dry-run reporting carry `Status` too.

When writing xlsx, after populating each row: if `row["Status"] == STATUS_BROKEN`, apply
`BROKEN_FILL` and `BROKEN_FONT` to every cell of that row across `REQUIRED_COLUMNS`
(setting the font on the Link cell after `_set_link_cell`, since `cell.style = "Hyperlink"`
would otherwise override it). Non-broken rows must have the fill explicitly reset to the
default `PatternFill()` — rows are rewritten in place and a previously-broken row's
formatting would otherwise persist at that row index.

### Signature changes

```python
def create_or_update_treasure_map(
    *,
    root_dir: Path,
    output_xlsx: Path,
    sharepoint_base_url: Optional[str] = None,
    today: Optional[date] = None,
    suffixes: Optional[Iterable[str]] = None,
    prune_missing: bool = True,
    dry_run: bool = False,
    output_format: OutputFormat = OutputFormat.XLSX,
    progress_callback: Optional[Callable[[str], None]] = None,
    detect_moves: bool = True,        # NEW — escape hatch, and lets tests isolate old behaviour
    with_result: bool = False,        # NEW — see Open decision 1
) -> Path | ScanResult | WriteOutcome:
```

`dof_api()` gains the same two parameters and forwards them. NumPy-style docstring
sections updated for both.

### `src/dof/cli.py`

- New option:
  ```python
  @click.option("--no-fail-on-broken", is_flag=True, default=False,
                help="Exit 0 even when broken links are found (default: exit 2).")
  ```
- Pass `with_result=True` to `dof_api`; unwrap `WriteOutcome` into `written` + `scan`.
- Dry-run and real-run output both print, after the existing sections:
  ```
  Moved files:
    > old/path.pdf -> new/path.pdf
  Broken links:
    ! some/missing.pdf
  ```
  Moved before Deleted; Broken last, so it is the final thing on screen.
- After printing: `if scan.broken_links and not no_fail_on_broken: raise SystemExit(2)`
  (use `sys.exit(2)`; Click surfaces it as the process exit code and
  `CliRunner.invoke(...).exit_code == 2`).

---

## tester

New files: `tests/unit/test_moves.py`, `tests/unit/test_broken_links.py`; extend
`tests/integration/test_cli.py`. Use `tmp_path` for every path. Do not assert a coverage
number — the gate is `[tool.coverage.report] fail_under` in `pyproject.toml` (now set to
85; see **ci** below).

### Move detection (M)

- **M1** Pure move: create `a/doc.pdf`, scan, edit Description to `"mine"`, move to
  `b/doc.pdf`, rescan → one row at `b/doc.pdf`, `Date Found` == first scan date,
  `Description == "mine"`, `Version == "1.0"`, `Status == "Moved"`,
  `Previous Location == "a/doc.pdf"`; `deleted_files` empty; `new_files` empty.
- **M2** Rename in place: `a/old.pdf` → `a/new.pdf`, same content → move, `File Name`
  updated to `new.pdf`, Version unchanged.
- **M3** Move + edit (Tier 2): `a/doc.txt` → `b/doc.txt` with content changed but **same
  byte length** → move detected, `Version == "1.1"`, `Status == "Moved"`.
- **M4** Move + edit with different size → **not** a move: one `deleted`, one `new`.
  (Documents the limit of Tier 2 honestly.)
- **M5** Swap: `a.pdf` and `b.pdf` with distinct contents swap paths → two moves, two rows,
  no row lost, Descriptions follow content.
- **M6** Duplicate content: two rows with identical content, both move → two rows survive;
  assert exactly 2 rows and that no location appears twice.
- **M7** Ambiguous hash, name tie-break: orphan `x/report.pdf` and orphan `x/copy.pdf` have
  identical content; found `y/report.pdf` and `y/copy.pdf` → `report` pairs with `report`.
- **M8** Copy/split: one row, file copied to two new locations, original deleted → exactly
  one move (deterministic: lowest sorted found path) and one new row.
- **M9** Moved into an ignored directory: `.treasureignore` contains `archive/` and the
  file moves into `archive/` → the file is never discovered, so the row is pruned
  (default) as deleted, not moved. Assert no `Moved`.
- **M10** Unhashable file: monkeypatch `_safe_sha256_file` to return `None` for the moved
  file → no Tier 1 match; falls to Tier 2 if name+size match, else new. Assert it does not
  crash and does not mis-pair.
- **M11** Empty files: two zero-byte `.txt` files with different names in different dirs;
  one is deleted and an unrelated empty `.txt` appears → assert they are *not* paired.
  Zero-byte files are excluded from **both** tiers: every empty file shares the SHA-256 of
  the empty string and the same size, so neither signal is evidence of a move. Such files
  always fall through to Tier 3 (new row) and the deleted one is reported as deleted.
- **M12** `detect_moves=False` reproduces the old deleted+new behaviour exactly.

### Backwards compatibility (BC)

- **BC1** A workbook written by the *current* released code (build one by writing a
  workbook with only the eight original columns and a two-column meta sheet) upgrades in
  place: new columns appended right-most, all original values and the user Description
  preserved, `Size` header added to `_dof_meta`.
- **BC2** JSON and CSV exports contain the two new columns, in `REQUIRED_COLUMNS` order.
- **BC3** Existing tests in `test_treasure_map.py`, `test_treasure_map_lifecycle.py`,
  `test_edge_cases.py`, `test_treasureignore.py` still pass untouched, except where they
  assert an exact column count/header list — update those explicitly, not by relaxing them.

### Broken links (B)

- **B1** Default `prune_missing=True`: delete a file, rescan → row removed,
  `broken_links` empty, exit 0.
- **B2** `--keep-missing`: delete a file, rescan → row retained, `Status == "Broken"`,
  `broken_links == ["<loc>"]`.
- **B3** Broken row's cells carry a solid red fill in the saved xlsx (assert
  `ws.cell(...).fill.start_color.rgb`).
- **B4** A previously-broken row whose file reappears goes back to `Status == "OK"` and its
  fill is reset to the default (this is the regression that a naive implementation misses).
- **B5** SharePoint mode: with `sharepoint_base_url` set and `--keep-missing`, a missing
  file's link is Broken; a present file's link is OK. Assert **no network access** —
  monkeypatch/ban `urllib.request.urlopen` for the test module.
- **B6** A hand-pasted `https://` link in a row with no `sharepoint_base_url` configured is
  never flagged Broken.
- **B7** `ScanResult.summary()` includes `Moved:` and `Broken:` lines only when non-zero,
  and the pre-existing three lines are byte-identical to before.

### CLI (C)

- **C1** `--dry-run` on a moved file prints a `Moved files:` section with `old -> new`.
- **C2** `--keep-missing` with a deleted file → `exit_code == 2` and `Broken links:` in
  stdout.
- **C3** `--keep-missing --no-fail-on-broken` → `exit_code == 0`, broken still listed.
- **C4** Clean scan → `exit_code == 0`, no Moved/Broken sections printed.
- **C5** `--format json` and `--format csv` still exit 0 and include the new columns.

All of the above are unit tests except C1–C5 and BC1, which go in `tests/integration/`
with `@pytest.mark.integration`.

---

## documenter

- **`README.md`** — new short section "Tracking moved files": explain the three tiers in
  user language (identical content → tracked silently; same name+size+type → tracked and
  version bumped; otherwise treated as a new document), and a "Status column" section
  covering `OK` / `Moved` / `Broken`, the red highlighting, `Previous Location` being
  sticky, and the exit-code behaviour plus `--no-fail-on-broken`.
- **`docs/treasure_map.rst`** — document the two new columns in the column table, the
  `_dof_meta` schema change (`Size`), and the in-place upgrade guarantee for workbooks
  written by earlier versions.
- **`docs/cli.rst`** — `--no-fail-on-broken`; document exit codes (0 clean, 2 broken links
  present).
- **`CHANGELOG.rst`** — under `## Unreleased`: Added (move detection, `Status`,
  `Previous Location`, `--no-fail-on-broken`, `moved_files`/`broken_links` on `ScanResult`,
  `ChangeType.MOVED`/`BROKEN`); Changed (**exit code is now 2 when broken links are
  present** — call this out as behaviour-changing for scripts; `_dof_meta` gains a `Size`
  column). Not a breaking API change: all new parameters are keyword-only with defaults.
- **Docstrings** — NumPy-style on `_detect_moves`, `_link_is_resolvable`, `MetaEntry`,
  `WriteOutcome`, and the updated `create_or_update_treasure_map` / `dof_api` parameter
  and returns sections. Update the module docstring's "Key behaviour" list at the top of
  `api.py` to mention moves and broken links.
- **`CLAUDE.md`** — extend the "Treasure Map Management" section with the move-detection
  tiers and the Status column, so future sessions do not re-derive it.

---

## ci

- **No new dependencies.** Confirmed: `PatternFill` ships with `openpyxl` (already a
  runtime dep), everything else is stdlib. `pyproject.toml` `dependencies` must not change
  — flag it if a coder proposes otherwise.
- Gates to run: `make lint`, `make test-all`, `make docs`, `make build`.
- **`[tool.coverage.report] fail_under` is set to 85** (raised from 40 with the user's
  approval once actual coverage reached 88.7%). Never hardcode the threshold anywhere but
  `pyproject.toml` — not in the Makefile, a workflow, or a `.coveragerc`.
- Verify the GitHub Actions workflow (`.github/workflows/`) still passes; the new non-zero
  exit code means **any CI step or smoke test that runs `dof` against a tree with missing
  files will now fail** — audit the workflow and the Makefile's `run-cli` target for such a
  call and add `--no-fail-on-broken` there if one exists.
- Ruff: line length 120; the pseudocode above translates to real code that must satisfy
  `E, F, I, B` — in particular B006 (no mutable defaults) and B905 (`zip(..., strict=)`) if
  `zip` is used in the pairing.
- No `.stamps/` or `tmp/` changes; no new files under version control beyond the two new
  test modules and this `PLAN.md`.

---

## Risks

- **Behaviour change on exit code** — scripts wrapping `dof --keep-missing` will start
  failing. Mitigated by `--no-fail-on-broken` and a loud CHANGELOG entry; still needs the
  user's sign-off (Open decision 2/3).
- **False-positive moves.** Tier 2 (name+size+type) can pair unrelated files — e.g. two
  templates named `invoice.docx` of identical size in different departments, one deleted
  and one added in the same scan. Consequence is a wrong Description/Version carried onto
  the wrong row. This is the accepted cost of the user's chosen design; `Previous Location`
  at least makes it visible and auditable. Tier 1 has the same exposure only for
  byte-identical files, where the consequence is benign.
- **Zero-byte and near-empty files** hash identically, making Tier 1 itself unreliable for
  them (M11). Resolved: size-0 files are excluded from Tier 1 as well as Tier 2, so they
  are never paired by either tier.
- **Row rewriting and formatting** — the sheet is rewritten from row 2 every run, so stale
  red fills persist at reused row indices unless explicitly cleared (B4). Easy to miss.
- **OneDrive/Windows** — `_safe_file_size` must swallow `OSError`/`PermissionError` exactly
  as `_safe_sha256_file` does; a cloud placeholder reports a size without hydrating, which
  is fine, but a locked file must not crash the scan. Saving still goes through
  `_safe_save_workbook` unchanged.
- **PII** — no new files containing user data are added; test fixtures use `tmp_path` only.
  `PLAN.md` itself contains no customer data. The repo's `tmp/` and `coverage.xml` should
  stay out of any commit made for this work.
- **Manual validation only** — SharePoint link resolution is validated structurally
  (path-in-scan) with no network call, so a genuinely dead SharePoint URL for a file that
  *is* present locally will still report OK. That limit must be stated in the docs.
