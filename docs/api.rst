API Reference
=============

The ``dof.api`` module provides the core functionality for scanning directories
and managing treasure maps programmatically.

Main Functions
--------------

create_or_update_treasure_map
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: create_or_update_treasure_map(*, root_dir, output_xlsx, sharepoint_base_url=None, today=None, suffixes=None, prune_missing=False, dry_run=False, output_format=OutputFormat.XLSX, progress_callback=None)

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
   :returns: Path to written file, or ScanResult if dry_run=True
   :rtype: Path | ScanResult

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

   .. py:attribute:: changes
      :type: List[FileChange]

      Detailed change records for each file.

   .. py:method:: summary()

      Return a human-readable summary of changes.

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

      Type of change (NEW, UPDATED, UNCHANGED, DELETED, IGNORED).

   .. py:attribute:: old_version
      :type: Optional[str]

      Previous version number (if applicable).

   .. py:attribute:: new_version
      :type: Optional[str]

      New version number (if applicable).


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


Constants
---------

.. py:data:: DEFAULT_DOCUMENT_SUFFIXES
   :type: set[str]

   Default set of file extensions recognized as documents.

.. py:data:: REQUIRED_COLUMNS
   :type: list[str]

   Column names in the treasure map:
   ``["File Name", "File Type", "Description", "Date Found", "Last Seen", "Link", "Version", "Location"]``

.. py:data:: MAIN_SHEET_NAME
   :type: str

   Name of the main worksheet: ``"treasure_map"``

.. py:data:: META_SHEET_NAME
   :type: str

   Name of the hidden metadata sheet: ``"_dof_meta"``
