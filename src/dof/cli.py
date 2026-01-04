"""
To install run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command dof inside your current environment.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from dof import __version__
from dof.api import OutputFormat, ScanResult, dof_api

__author__ = "Kevin Steptoe"
__copyright__ = "Kevin Steptoe"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


class ProgressCounter:
    """Simple progress counter for CLI feedback."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.count = 0

    def __call__(self, path: str) -> None:
        if not self.enabled:
            return
        self.count += 1
        # Update on same line
        click.echo(f"\rScanning: {self.count} files processed...", nl=False, err=True)

    def finish(self) -> None:
        if self.enabled and self.count > 0:
            click.echo("", err=True)  # New line after progress


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
    help="Output filename (extension auto-adjusted for --format).",
)
@click.option(
    "--sharepoint-base",
    "sharepoint_base_url",
    default=None,
    envvar="DOF_SHAREPOINT_BASE_URL",
    show_default="none",
    help="Base SharePoint/OneDrive URL to use for hyperlinks.",
)
@click.option(
    "--keep-missing",
    is_flag=True,
    default=False,
    help="Keep rows for files that no longer exist (default: remove them).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would change without writing files.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["xlsx", "json", "csv"], case_sensitive=False),
    default="xlsx",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--progress/--no-progress",
    default=True,
    help="Show progress during scan.",
)
def cli(
    loglevel: Optional[int],
    root_dir: Path,
    output_xlsx: Path,
    sharepoint_base_url: Optional[str],
    keep_missing: bool,
    dry_run: bool,
    output_format: str,
    progress: bool,
):
    """Build/update a document "treasure map" Excel workbook."""
    # Convert format string to enum
    fmt = OutputFormat(output_format.lower())

    # Setup progress callback
    progress_counter = ProgressCounter(enabled=progress and sys.stderr.isatty())

    result = dof_api(
        loglevel,
        root_dir=root_dir,
        output_xlsx=output_xlsx,
        sharepoint_base_url=sharepoint_base_url,
        prune_missing=not keep_missing,
        dry_run=dry_run,
        output_format=fmt,
        progress_callback=progress_counter,
    )

    progress_counter.finish()

    if isinstance(result, ScanResult):
        # Dry run - print summary
        click.echo("\n" + result.summary())
        if result.new_files:
            click.echo("\nNew files:")
            for f in result.new_files:
                click.echo(f"  + {f}")
        if result.updated_files:
            click.echo("\nUpdated files:")
            for f in result.updated_files:
                click.echo(f"  ~ {f}")
        if result.deleted_files:
            click.echo("\nDeleted files:")
            for f in result.deleted_files:
                click.echo(f"  - {f}")
        if result.ignored_files:
            click.echo("\nIgnored files:")
            for f in result.ignored_files:
                click.echo(f"  x {f}")
    else:
        click.echo(f"Wrote: {result}")


if __name__ == "__main__":
    cli()
