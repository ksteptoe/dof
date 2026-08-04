DOF Documentation
=================

``dof`` (Document of Files) is a CLI tool that scans directories for document files
and maintains an Excel "treasure map" index with metadata, versioning, and hyperlinks.

Features
--------

- Recursive document scanning with configurable file types
- Excel output with clickable hyperlinks
- JSON and CSV export formats
- Content-based version tracking via SHA-256 hashing
- Move and rename detection, so a restructured tree keeps its history
- Offline broken-link detection with red highlighting and a non-zero exit code
- Gitignore-style exclusion patterns (``.treasureignore``)
- SharePoint/OneDrive URL integration
- Dry-run mode for previewing changes
- Progress indication for large scans

Installation
------------

.. code-block:: bash

   pip install treasure-map

.. note::

   **Installed as** ``treasure-map``, **used as** ``dof``. The distribution published to
   PyPI is named ``treasure-map``; the import package (``import dof``) and the console
   script (``dof``, or ``python -m dof``) are unchanged. ``pip install dof`` will not
   work, as that name is unavailable on PyPI.

To install from a source checkout::

   pip install -e ".[dev]"

Quick Start
-----------

.. code-block:: bash

   # Scan current directory
   dof

   # Preview changes
   dof --dry-run

   # Export as JSON
   dof --format json


Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   treasure_map
   cli

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   api
   api/modules

.. toctree::
   :maxdepth: 1
   :caption: Project Info

   changelog
   contributing
   license
   authors


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
