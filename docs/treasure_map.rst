Treasure map CLI
================

The ``dof`` CLI scans a directory tree for common document types (PDF, Office, text/markdown, etc.)
and maintains an Excel index file (default ``treasure_map.xlsx``).

Quickstart
----------

.. code-block:: bash

   # current directory
   dof

   # choose root
   dof -d /path/to/root


# remove rows for files that no longer exist
dof -d /path/to/root --prune-missinging


   # choose output filename
   dof -d . -o my_treasure_map.xlsx

Hyperlinks
----------

If you set ``DOF_SHAREPOINT_BASE_URL`` (or pass ``--sharepoint-base``),
new rows will have a hyperlink to:

``<BASE_URL>/<relative/path/to/file>``

The hyperlink display text is the filename.

Update rules
------------

If the output workbook already exists:

* **Identical file content**: no changes
* **Any change to file content**: updates **Date Found** and increments **Version**
  (e.g. ``1.0`` → ``1.1``), with all other columns preserved


Ignoring files with .treasureignore
----------------------------------

If a file named ``.treasureignore`` exists in the scan root directory, DOF will treat it like a
gitignore-style ignore file and will:

- skip matching files during discovery
- remove matching rows from an existing treasure map on the next run (even if the file still exists)

Example ``.treasureignore``::

  # ignore everything in tmp/
  tmp/

  # ignore Excel macro sheets
  *.xlsm

  # ignore a specific file
  secret.pdf

Patterns use gitignore-style "wildmatch" semantics (including ``**`` and negation with ``!``).
