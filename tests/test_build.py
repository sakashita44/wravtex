import os
import shutil
import sys
from pathlib import Path

import pytest

from wravtex.cli import main

IMAGE = os.environ.get("WRAVTEX_TEST_IMAGE")
FIXTURE = Path(__file__).parent / "fixtures" / "project"
ENGINES = ["lualatex biber", "pdflatex bibtex", "uplatex pbibtex"]

pytestmark = pytest.mark.skipif(
    not IMAGE, reason="WRAVTEX_TEST_IMAGE に TeX Live のイメージが指定されていない"
)


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("wravtex") / "project with space"
    shutil.copytree(FIXTURE, root)
    profiles = "".join(
        f'[profiles."{name}"]\ndir = "{name}"\nmain = "main.tex"\nout = "out/{name}"\n\n'
        for name in [*ENGINES, "broken"]
    )
    (root / "wravtex.toml").write_text(
        f'[images]\ntexlive = "{IMAGE}"\n\n{profiles}', encoding="utf-8"
    )
    return root


def snapshot(directory: Path) -> list[Path]:
    return sorted(path.relative_to(directory) for path in directory.rglob("*"))


@pytest.mark.parametrize("engine", ENGINES)
def test_build_from_manuscript_directory(
    project: Path, engine: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    manuscript = project / engine
    before = snapshot(manuscript)
    monkeypatch.chdir(manuscript)

    assert main(["build", engine]) == 0

    out = project / "out" / engine
    pdf = out / "main.pdf"
    assert pdf.read_bytes().startswith(b"%PDF")
    assert "Knuth" in (out / "main.bbl").read_text(encoding="utf-8")
    assert snapshot(manuscript) == before
    # Docker Desktop はファイル共有の層で所有者を対応付けるため、Linux でだけ検証する
    if sys.platform == "linux":
        assert pdf.stat().st_uid == os.getuid()
        assert pdf.stat().st_gid == os.getgid()


def test_output_replaces_existing_file(project: Path, tmp_path: Path) -> None:
    dest = tmp_path / "result.pdf"
    dest.write_bytes(b"previous")

    assert main(["build", "--project", str(project), ENGINES[1], "-o", str(dest)]) == 0

    assert dest.read_bytes().startswith(b"%PDF")


def test_failed_build_keeps_existing_output(project: Path, tmp_path: Path) -> None:
    dest = tmp_path / "result.pdf"
    dest.write_bytes(b"previous")

    assert main(["build", "--project", str(project), "broken", "-o", str(dest)]) != 0

    assert dest.read_bytes() == b"previous"
    assert list(tmp_path.iterdir()) == [dest]
