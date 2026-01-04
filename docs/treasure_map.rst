Treasure Map
============

The ``dof`` CLI scans a directory tree for common document types (PDF, Office, text/markdown, etc.)
and maintains an Excel index file (default ``treasure_map.xlsx``).

Quickstart
----------

.. code-block:: bash

   # Scan current directory
   dof

   # Scan a specific directory
   dof -d /path/to/root

   # Choose output filename
   dof -d . -o my_treasure_map.xlsx

   # Preview changes without writing (dry run)
   dof --dry-run

   # Output as JSON or CSV
   dof --format json
   dof --format csv

   # Remove rows for deleted files
   dof --prune-missing


Output Columns
--------------

The treasure map contains the following columns:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Description
   * - File Name
     - Name of the document file
   * - File Type
     - Document type (PDF, Word, Excel, etc.)
   * - Description
     - User-editable notes (preserved across updates)
   * - Date Found
     - First time the file was discovered (immutable)
   * - Last Seen
     - Most recent scan where the file was present
   * - Link
     - Clickable hyperlink to the file
   * - Version
     - Starts at 1.0; increments when content changes
   * - Location
     - Path relative to the scan root (POSIX-style)


Hyperlinks
----------

By default, hyperlinks use local ``file://`` URIs.

To generate SharePoint/OneDrive URLs instead, set the ``DOF_SHAREPOINT_BASE_URL``
environment variable or use the ``--sharepoint-base`` option:

.. code-block:: bash

   export DOF_SHAREPOINT_BASE_URL="https://example.sharepoint.com/sites/Team/Shared%20Documents"
   dof

   # Or pass directly
   dof --sharepoint-base "https://example.sharepoint.com/sites/Team/Shared%20Documents"

The hyperlink target becomes: ``<BASE_URL>/<relative/path/to/file>``


Update Behavior
---------------

When the output workbook already exists, dof applies these rules:

**Unchanged files** (same content hash):
  - ``Last Seen`` is updated to today's date
  - All other columns preserved (including user-edited ``Description``)

**Changed files** (content hash differs):
  - ``Version`` is incremented (e.g., ``1.0`` → ``1.1``)
  - ``Last Seen`` is updated to today's date
  - ``Date Found`` remains unchanged (first-seen date is immutable)
  - ``Description`` is preserved

**New files**:
  - New row added with ``Version`` = ``1.0``
  - ``Date Found`` and ``Last Seen`` set to today's date

**Deleted files** (without ``--prune-missing``):
  - Row remains in the map
  - ``Last Seen`` frozen at last scan date when file existed

**Deleted files** (with ``--prune-missing``):
  - Row is removed from the map


Ignoring Files
--------------

Create a ``.treasureignore`` file in the scan root to exclude files using
gitignore-style patterns:

.. code-block:: text

   # Ignore everything in tmp/
   tmp/

   # Ignore Excel macro sheets
   *.xlsm

   # Ignore a specific file
   secret.pdf

   # Negation: keep this one even though *.xlsm is ignored
   !important.xlsm

**Pattern types:**

- ``pattern`` - Matches anywhere in the tree
- ``/pattern`` - Matches only at the root level
- ``dir/`` - Ignores entire directory tree
- ``*.ext`` - Wildcard matching
- ``**/pattern/**`` - Matches across directory boundaries
- ``!pattern`` - Negation (last match wins)

Files matching ignore patterns are:

1. Excluded from new scans
2. Removed from existing treasure maps (even if the file still exists)


Supported File Types
--------------------

dof recognizes these document extensions:

**Office documents:**
  ``.doc``, ``.docx``, ``.dot``, ``.dotx``, ``.rtf``,
  ``.xls``, ``.xlsx``, ``.xlsm``, ``.xlsb``, ``.xlt``, ``.xltx``, ``.xltm``,
  ``.ppt``, ``.pptx``, ``.pptm``, ``.pot``, ``.potx``

**Text files:**
  ``.txt``, ``.text``, ``.md``, ``.rst``, ``.csv``, ``.tsv``

**Data/config:**
  ``.yaml``, ``.yml``, ``.json``, ``.xml``, ``.toml``, ``.ini``

**PDF:**
  ``.pdf``

**OpenDocument:**
  ``.odt``, ``.ods``, ``.odp``

**Apple iWork:**
  ``.pages``, ``.numbers``, ``.key``

**eBooks:**
  ``.epub``, ``.mobi``

**Other:**
  ``.tex``
