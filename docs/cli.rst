CLI Reference
=============

The ``dof`` command-line interface provides options for scanning directories,
controlling output format, and managing the treasure map.

Usage
-----

.. code-block:: text

   dof [OPTIONS]

Options
-------

.. option:: -d, --dir DIRECTORY

   Directory root to scan recursively.

   **Default:** Current directory (``.``)

.. option:: -o, --output FILE

   Output filename. The extension is auto-adjusted when using ``--format``.

   **Default:** ``treasure_map.xlsx``

.. option:: --format [xlsx|json|csv]

   Output format.

   - ``xlsx`` - Excel workbook with hyperlinks and formatting (default)
   - ``json`` - JSON file with array of document records
   - ``csv`` - CSV file with headers

   **Default:** ``xlsx``

.. option:: --dry-run

   Show what would change without writing any files.

   Outputs a summary of:

   - New files that would be added
   - Updated files (content changed)
   - Moved files (``old -> new``)
   - Deleted files that will be removed (default behaviour)
   - Ignored files (matching ``.treasureignore`` patterns)
   - Broken links

   The Moved, Deleted, Ignored and Broken sections are also printed on a real
   (non-dry-run) run; previously they appeared only here.

.. option:: --keep-missing

   Keep rows in the treasure map for files that no longer exist
   under the scanned root.

   By default, deleted files are removed from the map. Use this flag
   to preserve their rows with the ``Last Seen`` date frozen at the
   last scan when they existed.

   Retained rows point at files that are gone, so they are marked
   ``Status = Broken`` and dof exits 2. Combine with
   ``--no-fail-on-broken`` if that is expected.

.. option:: --no-detect-moves

   Treat a moved or renamed file as a deletion plus a new document.

   Move tracking is on by default, so a relocated document normally keeps its
   row along with ``Date Found``, ``Description`` and ``Version``. This flag
   switches matching off entirely and restores the pre-feature behaviour.

   Reach for it if the tier-2 heuristic (same file name, byte size and file
   type) ever pairs two unrelated documents: with the flag set, nothing is
   paired, so no row can be relinked to the wrong file. The cost is that
   genuine moves lose their history.

   **Default:** off (moves are tracked)

.. option:: --no-fail-on-broken

   Exit 0 even when broken links are found.

   Broken rows are still marked ``Status = Broken``, still highlighted red in
   the workbook, and still listed under ``Broken links:``; only the non-zero
   exit is suppressed. Intended for cron jobs and CI steps that run
   ``dof --keep-missing``, where broken rows are the point of the flag rather
   than a fault.

   **Default:** off (broken links cause exit 2)

.. option:: --sharepoint-base URL

   Base SharePoint/OneDrive URL to use for hyperlinks instead of
   local ``file://`` URIs.

   Can also be set via the ``DOF_SHAREPOINT_BASE_URL`` environment variable.

   **Example:**

   .. code-block:: bash

      dof --sharepoint-base "https://example.sharepoint.com/sites/Team/Shared%20Documents"

.. option:: --progress / --no-progress

   Show or hide the progress counter during scanning.

   **Default:** ``--progress`` (show progress when running in a terminal)

.. option:: -v, --verbose

   Enable info-level logging. Shows scan progress and file counts.

.. option:: -vv, --very-verbose

   Enable debug-level logging. Shows detailed information about
   each file processed.

.. option:: --version

   Show the version number and exit.

.. option:: -h, --help

   Show help message and exit.


Examples
--------

**Basic scan:**

.. code-block:: bash

   dof

**Scan specific directory with custom output:**

.. code-block:: bash

   dof -d /path/to/documents -o docs_index.xlsx

**Preview changes (dry run):**

.. code-block:: bash

   dof --dry-run

   # Output:
   # Total documents found: 42
   #   New:       5
   #   Updated:   2
   #   Unchanged: 35
   #
   # New files:
   #   + reports/q4_summary.pdf
   #   + notes/meeting_2025.docx
   #   ...

**Export as JSON:**

.. code-block:: bash

   dof --format json -o inventory.xlsx
   # Creates: inventory.json

**Preserve deleted files:**

.. code-block:: bash

   dof --keep-missing

   # Output:
   # Wrote: /docs/treasure_map.xlsx
   #
   # Broken links:
   #   ! notes/old_minutes.docx
   #
   # Exit code: 2

**Preserve deleted files without failing the build:**

.. code-block:: bash

   dof --keep-missing --no-fail-on-broken   # exit code: 0

**After a directory restructure:**

.. code-block:: bash

   dof

   # Output:
   # Wrote: /docs/treasure_map.xlsx
   #
   # Moved files:
   #   > docs/proposal.pdf -> archive/2025/proposal.pdf

**Without move tracking:**

.. code-block:: bash

   dof --no-detect-moves

   # Output:
   # Wrote: /docs/treasure_map.xlsx
   #
   # Deleted files:
   #   - docs/proposal.pdf
   #
   # The relocated file is reported as new instead, and starts again at
   # version 1.0 with an empty Description.

**SharePoint integration:**

.. code-block:: bash

   export DOF_SHAREPOINT_BASE_URL="https://company.sharepoint.com/sites/Docs/Shared%20Documents"
   dof -d ./project_docs

**Verbose output for debugging:**

.. code-block:: bash

   dof -vv


Exit Codes
----------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Code
     - Meaning
   * - 0
     - Success
   * - 1
     - Error (see error message for details)
   * - 2
     - Broken links are present in the map

.. warning::

   Exit code 2 is new. Scripts and CI steps that run ``dof --keep-missing``
   against a tree containing deleted files will now fail unless they pass
   ``--no-fail-on-broken``.


Environment Variables
---------------------

.. envvar:: DOF_SHAREPOINT_BASE_URL

   Base URL for SharePoint/OneDrive hyperlinks. Equivalent to
   ``--sharepoint-base`` option.

   .. code-block:: bash

      export DOF_SHAREPOINT_BASE_URL="https://example.sharepoint.com/sites/Team/Shared%20Documents"
