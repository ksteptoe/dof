API Reference
=============

The ``dof.api`` module provides the core functionality for scanning directories
and managing treasure maps programmatically.

Main Functions
--------------

create_or_update_treasure_map
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: create_or_update_treasure_map(*, root_dir, output_xlsx, sharepoint_base_url=None, today=None, suffixes=None, prune_missing=True, dry_run=False, output_format=OutputFormat.XLSX, progress_callback=None, detect_moves=True, with_result=False)

   Scan a directory and create or update the treasure map.

   :param root_dir: Directory to scan for documents (Path)
   :param output_xlsx: Output file path (Path). Extension adjusted for JSON/CSV formats.
   :param sharepoint_base_url: Optional SharePoint base URL for hyperlinks (str)
   :param today: Override today's date for testing (date)
   :param suffixes: File extensions to include (Iterable[str]). Defaults to common document types.
   :param prune_missing: If True, remove rows for files that no longer exist (bool)
   :param dry_run: If True, compute changes but don't write files (bool)
   :param output_format: Output format - XLSX, JSON, or CSV (OutputFormat)
   :param progress_callback: Optional callback called with each file path (Callable[[str], None])
   :param detect_moves: If True (the default), relink rows whose file has moved or been
      renamed. Set False for the older "deleted plus new" behaviour; the CLI
      equivalent is ``--no-detect-moves``. (bool)
   :param with_result: If True, a non-dry run returns a :py:class:`WriteOutcome`
      carrying both the written path and the :py:class:`ScanResult`, instead of the
      path alone. (bool)
   :returns: ``ScanResult`` if ``dry_run=True``; otherwise the path written, or a
      ``WriteOutcome`` when ``with_result=True``
   :rtype: Path | ScanResult | WriteOutcome

   Both ``detect_moves`` and ``with_result`` are keyword-only with defaults that
   preserve the behaviour existing callers already rely on.

   **Example:**

   .. code-block:: python

      from pathlib import Path
      from dof.api import create_or_update_treasure_map, OutputFormat

      # Basic usage
      result = create_or_update_treasure_map(
          root_dir=Path("/documents"),
          output_xlsx=Path("treasure_map.xlsx"),
      )
      print(f"Wrote: {result}")

      # Dry run
      result = create_or_update_treasure_map(
          root_dir=Path("/documents"),
          output_xlsx=Path("treasure_map.xlsx"),
          dry_run=True,
      )
      print(result.summary())

      # JSON output
      result = create_or_update_treasure_map(
          root_dir=Path("/documents"),
          output_xlsx=Path("output.xlsx"),
          output_format=OutputFormat.JSON,
      )

      # Real write, but report what changed
      outcome = create_or_update_treasure_map(
          root_dir=Path("/documents"),
          output_xlsx=Path("treasure_map.xlsx"),
          with_result=True,
      )
      print(f"Wrote: {outcome.path}")
      for old_loc, new_loc in outcome.scan.moved_files:
          print(f"moved: {old_loc} -> {new_loc}")
      if outcome.scan.broken_links:
          raise SystemExit(2)


dof_api
~~~~~~~

.. py:function:: dof_api(loglevel, *, root_dir, output_xlsx, sharepoint_base_url=None, prune_missing=True, dry_run=False, output_format=OutputFormat.XLSX, progress_callback=None, detect_moves=True, with_result=False)

   CLI-friendly wrapper around :py:func:`create_or_update_treasure_map`. Configures
   logging from ``loglevel``, then forwards every remaining argument unchanged -
   including ``detect_moves`` and ``with_result``.

   :param loglevel: Logging level to configure before scanning (int or None)
   :rtype: Path | ScanResult | WriteOutcome


discover_documents
~~~~~~~~~~~~~~~~~~

.. py:function:: discover_documents(root_dir, suffixes=None, progress_callback=None)

   Recursively scan a directory for document files.

   :param root_dir: Directory to scan (Path)
   :param suffixes: File extensions to include (Iterable[str])
   :param progress_callback: Optional callback for progress reporting (Callable[[str], None])
   :returns: List of discovered documents, sorted by location
   :rtype: List[FoundFile]

   **Example:**

   .. code-block:: python

      from pathlib import Path
      from dof.api import discover_documents

      docs = discover_documents(Path("/documents"))
      for doc in docs:
          print(f"{doc.filename} ({doc.file_type}) - {doc.rel_location}")


Data Classes
------------

FoundFile
~~~~~~~~~

.. py:class:: FoundFile

   Immutable representation of a discovered document file.

   .. py:attribute:: abs_path
      :type: Path

      Absolute path to the file.

   .. py:attribute:: rel_location
      :type: str

      Relative path from scan root (POSIX-style).

   .. py:attribute:: filename
      :type: str

      File name (e.g., ``report.pdf``).

   .. py:attribute:: suffix
      :type: str

      File extension, lowercased (e.g., ``.pdf``).

   .. py:attribute:: file_type
      :type: str

      Human-readable file type (e.g., ``PDF``, ``Word``).

   .. py:attribute:: sha256
      :type: Optional[str]

      SHA-256 hash of file content, or None if unreadable.

   .. py:attribute:: size
      :type: Optional[int]

      Size in bytes, or None if it could not be read. Used by move detection; a
      ``None`` or zero size disqualifies the file from tier 2 matching.


MetaEntry
~~~~~~~~~

.. py:class:: MetaEntry

   Per-file fingerprint stored on the hidden ``_dof_meta`` sheet.

   .. py:attribute:: sha256
      :type: Optional[str]

      SHA-256 of the file's content, or None when it could not be read.

   .. py:attribute:: size
      :type: Optional[int]

      Size in bytes, or None when it could not be read - including for rows carried
      over from a workbook written before sizes were stored.


WriteOutcome
~~~~~~~~~~~~

.. py:class:: WriteOutcome

   Returned by :py:func:`create_or_update_treasure_map` and :py:func:`dof_api` when
   ``with_result=True`` and the run is not a dry run. It exists so a real write can
   still report moves and broken links.

   .. py:attribute:: path
      :type: Path

      Path of the file that was written.

   .. py:attribute:: scan
      :type: ScanResult

      Full record of what changed during the scan.


ScanResult
~~~~~~~~~~

.. py:class:: ScanResult

   Result of a treasure map scan, used for dry-run reporting.

   .. py:attribute:: total_found
      :type: int

      Total number of documents found in scan.

   .. py:attribute:: new_files
      :type: List[str]

      Locations of newly discovered files.

   .. py:attribute:: updated_files
      :type: List[str]

      Locations of files with changed content.

   .. py:attribute:: unchanged_files
      :type: List[str]

      Locations of files with no changes.

   .. py:attribute:: deleted_files
      :type: List[str]

      Locations of files removed (when prune_missing=True).

   .. py:attribute:: ignored_files
      :type: List[str]

      Locations of files matching .treasureignore patterns.

   .. py:attribute:: moved_files
      :type: List[Tuple[str, str]]

      ``(old_location, new_location)`` for each move detected in this scan.

   .. py:attribute:: broken_links
      :type: List[str]

      Locations of rows whose link could not be resolved.

   .. py:attribute:: changes
      :type: List[FileChange]

      Detailed change records for each file.

   .. py:method:: summary()

      Return a human-readable summary of changes. ``Moved:`` and ``Broken:`` lines
      are included only when the corresponding counts are non-zero.

      :rtype: str


FileChange
~~~~~~~~~~

.. py:class:: FileChange

   Tracks a change to a single file.

   .. py:attribute:: location
      :type: str

      Relative path of the file.

   .. py:attribute:: change_type
      :type: ChangeType

      Type of change (NEW, UPDATED, UNCHANGED, DELETED, IGNORED, MOVED, BROKEN).

   .. py:attribute:: old_version
      :type: Optional[str]

      Previous version number (if applicable).

   .. py:attribute:: new_version
      :type: Optional[str]

      New version number (if applicable).

   .. py:attribute:: previous_location
      :type: Optional[str]

      For a ``MOVED`` change, the location the row was relinked from. None otherwise.


Enums
-----

OutputFormat
~~~~~~~~~~~~

.. py:class:: OutputFormat

   Output format enumeration.

   .. py:attribute:: XLSX

      Excel workbook format.

   .. py:attribute:: JSON

      JSON format.

   .. py:attribute:: CSV

      CSV format.


ChangeType
~~~~~~~~~~

.. py:class:: ChangeType

   Type of change for a file.

   .. py:attribute:: NEW

      File is newly discovered.

   .. py:attribute:: UPDATED

      File content has changed.

   .. py:attribute:: UNCHANGED

      File content is the same.

   .. py:attribute:: DELETED

      File has been deleted (and pruned).

   .. py:attribute:: IGNORED

      File matches .treasureignore pattern.

   .. py:attribute:: MOVED

      File has moved or been renamed; the existing row was relinked.

   .. py:attribute:: BROKEN

      The row's link could not be resolved.


Constants
---------

.. py:data:: DEFAULT_DOCUMENT_SUFFIXES
   :type: set[str]

   Default set of file extensions recognized as documents.

.. py:data:: REQUIRED_COLUMNS
   :type: list[str]

   Column names in the treasure map, in output order:
   ``["File Name", "File Type", "Description", "Date Found", "Last Seen", "Link",
   "Version", "Location", "Status", "Previous Location"]``

   JSON and CSV exports use this same order.

.. py:data:: STATUS_OK
   :type: str

   Value written to ``Status`` for a row whose link resolves: ``"OK"``.

.. py:data:: STATUS_MOVED
   :type: str

   Value written to ``Status`` for a row relinked by move detection this scan:
   ``"Moved"``.

.. py:data:: STATUS_BROKEN
   :type: str

   Value written to ``Status`` for a row whose link cannot be resolved: ``"Broken"``.
   Such rows are highlighted red in the workbook and cause the CLI to exit 2.

.. py:data:: MAIN_SHEET_NAME
   :type: str

   Name of the main worksheet: ``"treasure_map"``

.. py:data:: META_SHEET_NAME
   :type: str

   Name of the hidden metadata sheet: ``"_dof_meta"``. It holds ``Location``,
   ``Sha256`` and ``Size`` columns; the ``Size`` column is added automatically to
   workbooks written by earlier versions.
