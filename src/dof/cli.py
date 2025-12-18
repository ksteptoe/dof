"""
To install run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command dof inside your current environment.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import click

from dof import __version__
from dof.api import dof_api

__author__ = "Kevin Steptoe"
__copyright__ = "Kevin Steptoe"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "--version")
@click.option("-v", "--verbose", "loglevel", flag_value=logging.INFO, default=None, help="Info logging.")
@click.option("-vv", "--very-verbose", "loglevel", flag_value=logging.DEBUG, default=None, help="Debug logging.")
@click.option(
    "-d",
    "--dir",
    "root_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Directory root to scan (recursively).",
)
@click.option(
    "-o",
    "--output",
    "output_xlsx",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("treasure_map.xlsx"),
    show_default=True,
    help="Output Excel filename.",
)
@click.option(
    "--sharepoint-base",
    "sharepoint_base_url",
    default=None,
    envvar="DOF_SHAREPOINT_BASE_URL",
    show_default="(none)",
    help="Base SharePoint/OneDrive URL to use for hyperlinks.",
)
@click.option(
    "--prune-missing",
    is_flag=True,
    default=False,
    help="Remove rows for files that no longer exist under the scanned root.",
)
def cli(
    loglevel: Optional[int],
    root_dir: Path,
    output_xlsx: Path,
    sharepoint_base_url: Optional[str],
    prune_missing: bool,
):
    """Build/update a document "treasure map" Excel workbook."""
    dof_api(
        loglevel,
        root_dir=root_dir,
        output_xlsx=output_xlsx,
        sharepoint_base_url=sharepoint_base_url,
        prune_missing=prune_missing,
    )


if __name__ == "__main__":
    cli()
