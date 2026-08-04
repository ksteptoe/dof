=========
Changelog
=========

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
