# HANDOFF

State-of-play for `dof`. Read this first; update it after completing a task or release.

## Current state

| | |
|---|---|
| **Updated** | 2026-08-04 |
| **Branch** | `main` (in sync with `origin/main`) |
| **HEAD** | `6efc56f` — Pin ruff, drop stale RTD config, and make `make test` real |
| **Latest tag** | `v0.1.3` |
| **Published to PyPI** | **Yes** — https://pypi.org/project/treasure-map/0.1.3/ |
| **PyPI name** | **`treasure-map`** — install with `pip install treasure-map`, then use as `dof` |
| **Working tree** | Clean |
| **Gates** | lint clean · 98 passed / 2 skipped · coverage 89.11% (gate 85, enforced in CI) · docs build OK · `twine check` OK |
| **CI** | Green on run 30883566481 — lint + 6-way test matrix (3.12/3.13 × ubuntu/macos/windows) |

### Build/test commands on this machine

Plain `make lint` / `make test-all` / `make docs` work. The in-repo `.venv` is healthy.

OneDrive **transiently** breaks it — `pip install` fails with `OSError: [Errno 22]` and
`import docutils` fails the same way — but it clears on its own. A `venv-check` target
now guards every gate and prints an explicit diagnostic when this happens, instead of
letting it look like a repo defect. A working fallback venv exists at `~/.venvs/dof`:

```
make bootstrap VENV="$HOME/.venvs/dof"   # rebuild outside OneDrive if it recurs
export VENV="$HOME/.venvs/dof"           # VENV ?= .venv, so the env var is enough
```

## What last shipped — v0.1.0, move tracking

Fixes a user-reported bug: treasure-map rows were keyed solely by relative path, so
restructuring a directory tree made every moved file look like a deletion plus a new
file. `Date Found`, user-edited `Description` and `Version` history were all lost, and
hyperlinks in circulated copies of the map broke.

- **Three-tier move detection** (`_detect_moves` in `src/dof/api.py`), run after the
  same-location pass and before ignore/prune:
  - Tier 1 — identical SHA-256 relinks the row, `Version` unchanged.
  - Tier 2 — identical file name + byte size + file type relinks *and* bumps `Version`
    (assumed moved and edited).
  - Tier 3 — no match, genuinely new.
  Zero-byte files are excluded from **both** tiers: every empty file shares a hash and a
  size, so neither is evidence of a move. Tier 1 accepts an orphan row with no recorded
  size, so moves are still tracked across the upgrade from a pre-`Size` workbook.
- **Broken links**: unresolvable rows are marked `Broken`, filled red, listed in the CLI
  summary, and `dof` exits **2**. Resolution is entirely offline — no network calls.
- **New columns**: `Status` (OK / Moved / Broken) and `Previous Location` (retained
  indefinitely once set).
- **New flags**: `--no-detect-moves`, `--no-fail-on-broken`.
- **New API**: `WriteOutcome(path, scan)` via `with_result=True`; `MetaEntry`;
  `ScanResult.moved_files` / `.broken_links`; `ChangeType.MOVED` / `.BROKEN`;
  `FileChange.previous_location`; `detect_moves` kwarg.
- `_dof_meta` gained a `Size` column; **existing workbooks upgrade in place** — users
  re-run, they do not delete and rebuild.

Design record is in `PLAN.md` (excluded from the sdist by `MANIFEST.in`).

### Behaviour changes existing users will notice

- **Exit code 2** when the map holds a broken link. `dof --keep-missing` now goes red by
  design; `--no-fail-on-broken` suppresses it.
- Moved/Deleted/Ignored/Broken sections now print on real runs, not just `--dry-run`.

## v0.1.2 — link repair

Follow-up to a real bug report. v0.1.0 tracked files moving *within* a tree; it did not
handle **the tree itself moving**. Renaming a scanned root left every relative `Location`
correct and every file present, but the absolute `file://` target stored in each row
pointed at the old root — so 12 rows were marked `Broken`, including the
`treasure_map.xlsx` dof had just written.

`_repair_link_targets()` now regenerates a stale target before the status pass, so
**`Broken` means "dof cannot repair this"**, not "this happens to be stale". Repair is
*targeted* — a link that already resolves is never regenerated, so hand-edited hyperlinks
survive — and it never causes a non-zero exit. Reported as `Repaired links:` via
`ScanResult.repaired_links` / `ChangeType.REPAIRED`.

Rows kept by `--keep-missing` are never repair candidates: the file is genuinely gone, so
there is nothing to repair. That is correct and deliberate.

## The PyPI name — read before touching packaging

The distribution is **`treasure-map`**; the import package and console script are both
still **`dof`**. `pip install treasure-map`, then run `dof`.

PyPI **refuses** the name `dof`. It is not taken (404 on the JSON API) — it is blocked,
because PyPI rejects new names that collide after normalisation with common affixes
stripped, and **`pydof` already exists**. `v0.1.0` was tagged before this was known and
can never be published; it is left in place as an honest dead end, not force-moved.

Consequences to remember:
- A self-referential extra must name the *distribution*: `dev` depends on
  `treasure-map[docs]`. Naming it `dof[docs]` breaks `pip install -e ".[dev]"` outright.
- The Makefile keeps `PKG := dof` (import) and `DIST := treasure-map` (distribution)
  separate. `release-show`'s `importlib.metadata.version` needs `DIST`.
- Nothing in `src/` looks up distribution metadata — `__version__` comes from
  setuptools_scm's generated `_version.py` — so `dof --version` is immune to the split.

## Open tasks

**Next up**

- [ ] **The `live` marker is registered but no test applies it**, so `make test-live`
      collects nothing. Fine today (no live infrastructure), but do not treat it as a
      safety net — verify a test actually carries the marker before relying on it.

**Lower priority**

- [ ] **Symlink support unimplemented** — two skipped tests in
      `tests/unit/test_edge_cases.py` (`resolve()` follows links outside root).
- [ ] `CONTRIBUTING.rst` still carries 11 PyScaffold TODO placeholders, the only
      remaining Sphinx warnings. Adding `-W` to the docs gate needs these cleared first.
- [ ] **`.readthedocs.yaml` does not declare `formats: [pdf]`**, which the deleted
      `.yml` did. PDF was never actually built (RTD always preferred the `.yaml`), so
      nothing regressed — add it only if PDF output is wanted.

## Known sharp edges

- **Tier 2 is a heuristic.** Two same-name, same-size files — one deleted, one added in
  the same scan — can pair wrongly, carrying the wrong Description and Version onto the
  wrong row. `Previous Location` makes it auditable; `--no-detect-moves` disables it.
- **A content swap between two paths that both still exist** yields two `UPDATED`, not
  two `MOVED`, because the same-location pass runs first. Correct, and tested (M5b).
- **Coverage config lives only in `pyproject.toml`.** A root `.coveragerc` used to
  shadow it entirely — coverage.py finds `.coveragerc` first and stops, so the whole
  `[tool.coverage.*]` block was dead. Do not reintroduce one.
- **`make test` was a false green until v0.1.3.** Its content signature always evaluated
  to the empty string and a `$?`-vs-`$$?` bug let a failing pytest run mark the stamp as
  a pass, so it ran once and reported success forever. Fixed: each stage writes
  self-contained coverage data next to its stamp and promotes it **only on success**, so
  the aggregate is a pure function of the stamps. Do not reintroduce `--cov-append`
  across stages, and keep `coverage combine --keep` — without `--keep` the combine step
  deletes the cache it just read.
- **Ruff is pinned in three coupled places**: the `lint` extra in `pyproject.toml` is the
  source of truth, `dev` pulls it in, and `.pre-commit-config.yaml`'s `rev:` mirrors it.
  Bump all three in the same commit. The `<0.17` ceiling is deliberate — ruff ships new
  default rules in minor releases.

## Conventions

- Non-trivial work runs planner → coder → tester ∥ documenter → ci (see `CLAUDE.md`).
- Committing, updating this file, and releasing stay with Kevin / the main session.
- No AI co-author trailers on commits.
