from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from dof.cli import cli


def test_cli_creates_output(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "note.txt").write_text("hi", encoding="utf-8")

    out = tmp_path / "out.xlsx"
    runner = CliRunner()
    res = runner.invoke(cli, ["-d", str(root), "-o", str(out)])
    assert res.exit_code == 0
    assert out.exists()


def test_cli_keep_missing_flag(tmp_path: Path) -> None:
    """Test that --keep-missing preserves deleted file rows."""
    from openpyxl import load_workbook

    root = tmp_path / "root"
    root.mkdir()
    (root / "a.pdf").write_bytes(b"%PDF-1.4\nA\n")
    (root / "b.docx").write_bytes(b"BBB")

    out = tmp_path / "out.xlsx"
    runner = CliRunner()
    res1 = runner.invoke(cli, ["-d", str(root), "-o", str(out)])
    assert res1.exit_code == 0

    # Remove one file - default behavior should prune it
    (root / "b.docx").unlink()
    res2 = runner.invoke(cli, ["-d", str(root), "-o", str(out)])
    assert res2.exit_code == 0

    wb = load_workbook(out)
    ws = wb["treasure_map"]
    locs = {ws.cell(r, 8).value for r in range(2, ws.max_row + 1)}
    assert "b.docx" not in locs  # Should be pruned by default

    # Re-add the file and run again
    (root / "b.docx").write_bytes(b"BBB")
    res3 = runner.invoke(cli, ["-d", str(root), "-o", str(out)])
    assert res3.exit_code == 0

    # Remove again but use --keep-missing
    (root / "b.docx").unlink()
    res4 = runner.invoke(cli, ["-d", str(root), "-o", str(out), "--keep-missing"])
    assert res4.exit_code == 0

    wb = load_workbook(out)
    ws = wb["treasure_map"]
    locs = {ws.cell(r, 8).value for r in range(2, ws.max_row + 1)}
    assert "b.docx" in locs  # Should be kept with --keep-missing
