=========
Changelog
=========

Version 0.1.3
=============

Infrastructure only. No file under ``src/`` changed, so the **library code is
identical to 0.1.2**: same API, same CLI, same behaviour. Two packaging details do
differ - the wheel ``METADATA`` now lists the new ``lint`` extra, and the sdist ships
slightly different repository tooling - but nothing you can observe from
``import dof`` or from the ``dof`` command has changed.

It is not, however, a no-op for contributors.

Fixed
-----

- **``make test`` used to report success whether or not the tests passed.** The
  incremental-testing machinery works by writing a small "stamp" file after a
  successful run and skipping the run next time if nothing relevant has changed. Two
  faults in those recipes combined badly: the recipe discarded pytest's exit status,
  so a red suite still wrote its stamp; and the signature used to decide whether
  anything had changed always came out empty, so every subsequent run looked
  unchanged. The net effect was that after one invocation, ``make test`` would skip
  the suite and print success indefinitely, no matter what state the tests were in.
  The recipes now propagate pytest's exit code - a failing suite fails the build and
  writes no stamp - and compute a real content signature, so ``make test`` is
  genuinely incremental again. **If you have been relying on** ``make test`` **for
  local verification, treat its recent history as uninformative and re-run it.**
- A partial-stage coverage gate that the above had been masking was corrected, so the
  coverage threshold - which lives in ``pyproject.toml`` under
  ``[tool.coverage.report] fail_under`` - is enforced exactly once, against the
  aggregate of the whole run rather than against a single stage.

Changed
-------

- **Ruff is now declared in one place.** A new ``lint`` extra in ``pyproject.toml``
  pins ``ruff>=0.16.1,<0.17``; ``dev`` pulls it in, the CI lint job installs
  ``.[lint]``, and ``.pre-commit-config.yaml`` moves to ``rev: v0.16.1``. Previously
  three versions drifted independently: ``pyproject`` asked for ``ruff>=0.6``,
  pre-commit pinned v0.6.9, and CI installed whatever was current.
  **Contributor-visible:** running ``pip install -e ".[dev]"`` will move ruff to the
  0.16 series, and some previously clean files may now report new violations. The
  upper bound is deliberate: an open ``>=`` lets a fresh ruff release change the
  default rule set and turn CI red while everyone's local checkout stays green.
- CI lints the whole tree (``ruff check .``) rather than ``src tests`` only, matching
  ``make lint`` and the pre-commit hooks. ``docs/conf.py``, ``tests/conftest.py`` and
  the root tooling files are now linted in CI, where they silently were not.

Added
-----

- The CI build job runs ``twine check dist/*``, so packaging metadata errors surface
  on every push rather than at upload time.

Removed
-------

- The stale ``.readthedocs.yml``, superseded by ``.readthedocs.yaml``. The old file
  pinned Python 3.11, below the project's ``requires-python = ">=3.12"``.

Version 0.1.2
=============

Fixed
-----

- **Renaming or moving the root of a scanned tree no longer breaks every link.**
  Previously, a row whose file was still present at the same relative ``Location`` kept
  its stored hyperlink verbatim, so after the top-level folder was renamed - or the tree
  arrived at a different absolute path on another machine or a re-rooted OneDrive - every
  row still pointed at the old root. Every one of them was reported ``Broken``, including
  the ``treasure_map.xlsx`` dof had just written in that same run. Move tracking covered
  files moving *within* the tree; it did not cover the whole tree moving.
- dof now **repairs stale links before reporting them**. For any row whose file was found
  by the scan but whose stored target no longer resolves, the target is regenerated from
  the current root (or from the configured SharePoint base). Repair is targeted: a link
  that already resolves is never regenerated, so a hand-edited hyperlink is not clobbered.
  Simply re-running dof after a root rename now fixes the workbook.
- **``Broken`` now means "dof cannot repair this", not "this happens to be stale".**
  Repaired rows are listed under a new ``Repaired links:`` section in the CLI output and
  do **not** affect the exit code - repair is a success, not a failure. A run that
  previously exited 2 after a root rename now exits 0.

Added
-----

- ``ScanResult.repaired_links`` (locations whose link target was regenerated) and
  ``ChangeType.REPAIRED``.
- ``ScanResult.summary()`` gains a ``Repaired:`` line, shown only when the count is
  non-zero. The existing lines are unchanged.

Nothing is broken by this release: no flag, option or signature changes, and the only
behaviour change is that fewer rows are reported broken.

Version 0.1.1
=============

Changed
-------

- **The distribution is now published as** ``treasure-map`` **instead of** ``dof``.
  PyPI rejects ``dof`` as a new project name, because it normalises to a name already
  taken by an existing project (``pydof``), so 0.1.0 could never be published. Install
  with ``pip install treasure-map``.
- Documentation updated throughout to give the new installation command.

Unchanged
---------

- The import package is still ``dof`` (``import dof``), and the console script is still
  ``dof`` (or ``python -m dof``). Only the name you install by has changed; no code,
  API or command-line interface is affected.

Version 0.1.0
=============

Added
-----

- **Move and rename detection.** A document that has moved or been renamed now keeps
  its existing row, and with it ``Date Found``, the user-edited ``Description`` and its
  ``Version`` history, instead of being reported as a deletion plus a new file. Matching
  runs in three tiers: identical SHA-256 (relink, version unchanged); identical file
  name, byte size and file type (relink and bump ``Version``, on the assumption the file
  was moved and edited); otherwise the file is treated as genuinely new. Zero-byte files
  and files whose hash or size could not be read are never paired.
- Two user-facing columns: ``Status`` (``OK`` / ``Moved`` / ``Broken``) and
  ``Previous Location`` (the path a row was relinked from, retained indefinitely once
  set, blank for rows that have never moved).
- **Broken-link detection.** Rows whose target cannot be resolved are marked
  ``Broken``, highlighted red in the workbook and listed in the CLI summary. Resolution
  is entirely offline: no network request is ever made.
- ``--no-fail-on-broken`` CLI flag, which keeps the marking and reporting but suppresses
  the non-zero exit.
- ``ScanResult.moved_files`` (a list of ``(old_location, new_location)`` pairs) and
  ``ScanResult.broken_links``; ``ChangeType.MOVED`` and ``ChangeType.BROKEN``;
  ``FileChange.previous_location``.
- ``WriteOutcome(path, scan)``, returned by ``create_or_update_treasure_map()`` and
  ``dof_api()`` when the new ``with_result=True`` keyword argument is passed, so a real
  (non-dry-run) write can report what changed.
- ``MetaEntry(sha256, size)``, the per-file fingerprint now stored on the hidden meta
  sheet.
- ``--no-detect-moves`` CLI flag, which switches move matching off and restores the
  previous "deleted plus new" behaviour. It is the escape hatch for the case where the
  tier-2 heuristic pairs two unrelated documents.
- ``detect_moves`` keyword argument on ``create_or_update_treasure_map()`` and
  ``dof_api()``; set it to ``False`` for the previous "deleted plus new" behaviour.
  ``--no-detect-moves`` is the CLI equivalent.

Changed
-------

- **Exit code 2 is now returned when broken links are present.** This is a behaviour
  change for scripts: any cron job or CI step running ``dof --keep-missing`` against a
  tree containing deleted files will now go red. Add ``--no-fail-on-broken`` to those
  invocations to restore the previous exit status.
- Real (non-dry-run) runs now print ``Moved files:``, ``Deleted files:``,
  ``Ignored files:`` and ``Broken links:`` sections. Previously these appeared only
  under ``--dry-run``.
- The hidden ``_dof_meta`` sheet gains a ``Size`` column. Workbooks written by earlier
  versions are upgraded in place on the next scan; no user action is needed and no data
  is lost.
- ``ScanResult.summary()`` gains ``Moved:`` and ``Broken:`` lines, shown only when the
  corresponding counts are non-zero. The existing lines are unchanged.

No API is broken by this release: every new parameter is keyword-only with a default
that preserves the previous behaviour.

Version 0.1
===========

- Feature A added
- FIX: nasty bug #1729 fixed
- add your changes here!
