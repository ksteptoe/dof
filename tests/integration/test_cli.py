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


def test_cli_prune_missing_flag(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.pdf").write_bytes(b"%PDF-1.4\nA\n")
    (root / "b.docx").write_bytes(b"BBB")

    out = tmp_path / "out.xlsx"
    runner = CliRunner()
    res1 = runner.invoke(cli, ["-d", str(root), "-o", str(out)])
    assert res1.exit_code == 0

    # remove one file then prune
    (root / "b.docx").unlink()
    res2 = runner.invoke(cli, ["-d", str(root), "-o", str(out), "--prune-missing"])
    assert res2.exit_code == 0
