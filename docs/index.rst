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
- Gitignore-style exclusion patterns (``.treasureignore``)
- SharePoint/OneDrive URL integration
- Dry-run mode for previewing changes
- Progress indication for large scans

Quick Start
-----------

.. code-block:: bash

   # Install
   pip install dof

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
