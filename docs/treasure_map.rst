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

   # Keep rows for deleted files (default: remove them)
   dof --keep-missing

   # ... without exiting non-zero for the resulting broken links
   dof --keep-missing --no-fail-on-broken


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
   * - Status
     - ``OK``, ``Moved`` or ``Broken`` for the current scan; broken rows are
       highlighted red in the workbook
   * - Previous Location
     - Where the file was before it last moved; blank for rows that have never moved,
       and retained indefinitely once set


Tracking Moved Files
--------------------

Rows were historically keyed solely on ``Location``, so restructuring a directory tree
made every moved document look like a deletion plus a new file. ``Date Found``, the
user-edited ``Description`` and the whole ``Version`` history were lost, and hyperlinks
in already-circulated copies of the map stopped working.

dof now recognises a moved or renamed document and relinks the existing row to its new
path, preserving ``Date Found``, ``Description`` and ``Version``. Matching runs in three
tiers:

**Tier 1 - identical content (certain):**
  A discovered file whose SHA-256 matches an orphaned row is the same document. The row
  is relinked and its ``Version`` is left unchanged. This covers pure moves and renames.

**Tier 2 - same name, size and file type (probable):**
  Treated as the same document, moved *and* edited: the row is relinked **and** its
  ``Version`` is bumped (``1.0`` → ``1.1``).

**Tier 3 - no match:**
  The file is treated as genuinely new. The orphaned row is pruned, or marked ``Broken``
  under ``--keep-missing``.

In every case the relinked row keeps its ``Date Found``, its ``Description`` and its
version history, records the old path in ``Previous Location``, and takes
``Status = Moved`` for that scan.

Limits, stated honestly:

- **Empty files never pair.** Every zero-byte file shares the same SHA-256 and the same
  size, so neither signal is evidence of a move. Such files always fall through to
  tier 3.
- **Unreadable files never pair.** A file dof could not hash is excluded from tier 1; a
  file whose size it could not read is excluded from tier 2. dof degrades to
  "deleted plus new" rather than guessing.
- **Tier 2 is probabilistic.** Two unrelated files sharing a name, size and type - one
  removed and one added in the same scan - can be paired wrongly, carrying the wrong
  ``Description`` and ``Version`` onto the surviving row. ``Previous Location`` makes
  this visible and auditable.
- **A file moved into an ignored directory is never discovered**, so its row is pruned
  as deleted rather than reported as moved.

``Status`` describes the current scan and reverts to ``OK`` on the next scan that finds
the file where the map says it is. ``Previous Location`` is historical and sticky, so
that someone holding an older copy of the map can still trace where a document went.

Worked example
~~~~~~~~~~~~~~

Starting tree, after a first ``dof`` run and a description typed into Excel:

.. code-block:: text

   docs/proposal.pdf          Version 1.0   Status OK
   docs/notes/meeting.docx    Version 1.0   Status OK

``docs/`` is then renamed to ``archive/2025/``, and ``meeting.docx`` is edited in place
without changing its byte length. Rescanning gives:

.. code-block:: text

   archive/2025/proposal.pdf        Version 1.0  Status Moved  Prev docs/proposal.pdf
   archive/2025/notes/meeting.docx  Version 1.1  Status Moved  Prev docs/notes/meeting.docx

and the CLI reports:

.. code-block:: text

   Moved files:
     > docs/proposal.pdf -> archive/2025/proposal.pdf
     > docs/notes/meeting.docx -> archive/2025/notes/meeting.docx

Both descriptions and both ``Date Found`` dates survive. ``proposal.pdf`` kept version
``1.0`` (tier 1, content unchanged); ``meeting.docx`` moved to ``1.1`` (tier 2, moved
and edited).


Broken and Repaired Links
-------------------------

After each scan, dof checks that every row's link can still be resolved - and **repairs
what it can before reporting anything as broken**.

Repair before report
~~~~~~~~~~~~~~~~~~~~

If a row's file was found by this scan but its stored target no longer resolves, dof
regenerates that target from the current scan root, or from the configured SharePoint
base. Repaired rows are listed under ``Repaired links:`` in the CLI output and **do not
affect the exit code**; repair is a success, not a failure.

Repair is targeted. A link that already resolves is never regenerated, so a hyperlink you
edited by hand is left exactly as you wrote it.

The moved root
~~~~~~~~~~~~~~

The common real-world trigger is the whole tree moving. You rename or reorganise the
top-level folder, or the tree arrives at a different absolute path - on another machine,
or after OneDrive re-roots your local copy. Every relative ``Location`` in the workbook is
still correct, and every file is still present, but every stored absolute link still
points at the old root.

Move tracking (see above) handles files moving *within* the tree; it does not see the
tree itself move. Before v0.1.2 dof marked every such row ``Broken`` and exited 2 -
including the ``treasure_map.xlsx`` it had just written in that same run. A plain re-run
now repairs them all and exits 0:

.. code-block:: bash

   dof -d /path/to/renamed/tree

   # Output:
   # Wrote: /path/to/renamed/tree/treasure_map.xlsx
   #
   # Repaired links:
   #   * reports/q4_summary.pdf
   #   * notes/meeting_2025.docx
   #
   # Exit code: 0

What ``Broken`` means
~~~~~~~~~~~~~~~~~~~~~

``Broken`` means **dof cannot repair this row** - not merely that its link is stale. Such
a row is marked ``Status = Broken``, highlighted red in the workbook, listed under
``Broken links:`` in the CLI output, and causes dof to **exit with code 2**.

This mainly arises with ``--keep-missing``, which deliberately retains rows for files
that no longer exist; those files really are gone, so there is nothing to regenerate a
link to. Pass ``--no-fail-on-broken`` to keep the marking and reporting while exiting 0:

.. code-block:: bash

   dof --keep-missing --no-fail-on-broken

How links are resolved
~~~~~~~~~~~~~~~~~~~~~~

Resolution is entirely offline - **dof never makes a network request** when validating
links:

- A ``file://`` target resolves when the path it references exists on disk.
- A SharePoint target resolves when its path, taken relative to the configured base URL,
  matches a location discovered by this scan.
- An ``http(s)://`` target with no ``--sharepoint-base`` configured was pasted in by
  hand and is always treated as resolvable; dof has no offline way to judge it and must
  not flag your own data as broken.
- Anything else falls back to checking whether the row's ``Location`` exists under the
  scan root.

The consequence of the offline design is that a genuinely dead SharePoint URL for a file
that *is* present locally will still report ``OK``.


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

**Deleted files** (default behavior):
  - Row is removed from the map

**Moved or renamed files:**
  - The existing row is relinked to the new ``Location``
  - ``Date Found``, ``Description`` and version history are preserved
  - ``Previous Location`` records the old path; ``Status`` becomes ``Moved``
  - ``Version`` is bumped only for a tier 2 (moved-and-edited) match

**Files whose stored link has gone stale** (for example after the scan root was renamed):
  - The link target is regenerated from the current root, or the configured SharePoint base
  - The row is listed under ``Repaired links:``; the exit code is unaffected
  - A link that still resolves is left untouched

**Deleted files** (with ``--keep-missing``):
  - Row remains in the map
  - ``Last Seen`` frozen at last scan date when file existed
  - ``Status`` becomes ``Broken`` and the row is highlighted red; dof exits 2 unless
    ``--no-fail-on-broken`` is given


Workbook Compatibility
----------------------

Workbooks written by earlier versions of dof are upgraded in place on the next scan.
The ``Status`` and ``Previous Location`` columns are appended to the right of the
existing ones, and the hidden ``_dof_meta`` sheet - which stores the per-file
fingerprints used for change and move detection - gains a ``Size`` column alongside its
existing ``Location`` and ``Sha256`` columns.

No user action is required and nothing is lost: existing values, including hand-written
``Description`` text, are preserved. Rows carried over from an older workbook have no
recorded size, so their first rescan matches on hash alone (tier 1); sizes are recorded
from that point on.


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
