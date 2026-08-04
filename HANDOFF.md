# HANDOFF

State-of-play for `dof`. Read this first; update it after completing a task or release.

## Current state

| | |
|---|---|
| **Updated** | 2026-08-04 |
| **Branch** | `main` (in sync with `origin/main`) |
| **HEAD** | `5e765d3` — Track moved files and flag broken links |
| **Latest tag** | `v0.1.0` (tagged and pushed) |
| **Published to PyPI** | **No** — `v0.1.0` is tagged but not uploaded |
| **Working tree** | Clean |
| **Gates** | lint clean · 83 passed / 2 skipped · coverage 88.71% (gate 85) · docs build OK · `twine check` OK |

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

## Open tasks

**Next up**

- [ ] **Publish `v0.1.0` to PyPI** — `make upload VENV="$HOME/.venvs/dof"`. Tagged but
      not uploaded; awaiting Kevin's go-ahead. `make release` only tags and pushes.
- [ ] **Pin `ruff` in CI.** The lint job does `pip install ruff` unpinned while
      `pyproject.toml` says `ruff>=0.6`, so a new ruff release can turn CI red
      spontaneously while local stays green. CI also runs `ruff check src tests` where
      the Makefile runs `ruff check .`.
- [ ] **`build` job never runs `twine check dist/*`**, so packaging metadata errors only
      surface at upload time.

**Lower priority**

- [ ] **Stale `.readthedocs.yml`** shadowed by `.readthedocs.yaml`. The `.yml` pins
      Python 3.11, below `requires-python = ">=3.12"` — harmless while `.yaml` wins,
      a trap if precedence ever shifts. Recommend deleting it.
- [ ] **Makefile stamp recipes swallow pytest exit 5** (~lines 146, 169), so a break in
      test discovery would show as green. They also contain a `$?`-vs-`$$?` Make
      expansion bug. The `test-live` recipe was fixed; these were left alone.
- [ ] **Symlink support unimplemented** — two skipped tests in
      `tests/unit/test_edge_cases.py` (`resolve()` follows links outside root).
- [ ] `docs/CONTRIBUTING.rst` still carries 11 PyScaffold TODO placeholders, the only
      remaining Sphinx warnings.

## Known sharp edges

- **Tier 2 is a heuristic.** Two same-name, same-size files — one deleted, one added in
  the same scan — can pair wrongly, carrying the wrong Description and Version onto the
  wrong row. `Previous Location` makes it auditable; `--no-detect-moves` disables it.
- **A content swap between two paths that both still exist** yields two `UPDATED`, not
  two `MOVED`, because the same-location pass runs first. Correct, and tested (M5b).
- **Coverage config lives only in `pyproject.toml`.** A root `.coveragerc` used to
  shadow it entirely — coverage.py finds `.coveragerc` first and stops, so the whole
  `[tool.coverage.*]` block was dead. Do not reintroduce one.

## Conventions

- Non-trivial work runs planner → coder → tester ∥ documenter → ci (see `CLAUDE.md`).
- Committing, updating this file, and releasing stay with Kevin / the main session.
- No AI co-author trailers on commits.
