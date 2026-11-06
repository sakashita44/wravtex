from pathlib import Path

import pytest

from wravtex import config

DIGEST = "sha256:" + "0" * 64


def make_project(root: Path, toml: str) -> Path:
    (root / "paper").mkdir(parents=True)
    (root / "paper" / "main.tex").write_text("", encoding="utf-8")
    (root / config.CONFIG_FILE).write_text(toml, encoding="utf-8")
    return root


def test_root_is_nearest_ancestor_with_config(tmp_path: Path) -> None:
    root = make_project(tmp_path, "")

    assert config.find_root(root / "paper") == root.resolve()


def test_root_not_found(tmp_path: Path) -> None:
    with pytest.raises(config.ConfigError):
        config.find_root(tmp_path)


def test_profile_paths_are_resolved_from_root(tmp_path: Path) -> None:
    root = make_project(
        tmp_path,
        '[profiles.p]\ndir = "paper"\nmain = "main.tex"\nout = "out/p"\n',
    )

    profile = config.load(root).profile("p")

    assert profile.dir == root.resolve() / "paper"
    assert profile.out == root.resolve() / "out" / "p"
    assert profile.pdf_name == "main.pdf"


@pytest.mark.parametrize(
    "entry",
    [
        'dir = "paper"\nmain = "main.tex"\nout = "paper"',
        'dir = "paper"\nmain = "main.tex"\nout = "."',
        'dir = "paper"\nmain = "main.tex"\nout = "../out"',
        'dir = "paper"\nmain = "missing.tex"\nout = "out"',
        'dir = "paper"\nout = "out"',
    ],
    ids=[
        "out-is-manuscript",
        "out-contains-manuscript",
        "out-outside-root",
        "main-missing",
        "main-undefined",
    ],
)
def test_invalid_profile(tmp_path: Path, entry: str) -> None:
    root = make_project(tmp_path, f"[profiles.p]\n{entry}\n")

    with pytest.raises(config.ConfigError):
        config.load(root).profile("p")


def test_out_may_be_inside_manuscript_at_root(tmp_path: Path) -> None:
    root = make_project(tmp_path, "")
    (root / "main.tex").write_text("", encoding="utf-8")
    (root / config.CONFIG_FILE).write_text(
        '[profiles.p]\ndir = "."\nmain = "main.tex"\nout = "out"\n', encoding="utf-8"
    )

    assert config.load(root).profile("p").out == root.resolve() / "out"


def test_unknown_profile_lists_defined_profiles(tmp_path: Path) -> None:
    root = make_project(
        tmp_path, '[profiles.p]\ndir = "paper"\nmain = "main.tex"\nout = "out"\n'
    )

    with pytest.raises(config.ConfigError, match="定義済み: p"):
        config.load(root).profile("q")


@pytest.mark.parametrize(
    ("image", "valid"),
    [
        (f"texlive/texlive:latest@{DIGEST}", True),
        (f"texlive/texlive@{DIGEST}", True),
        ("texlive/texlive:latest", False),
    ],
)
def test_image_must_be_pinned_by_digest(
    tmp_path: Path, image: str, *, valid: bool
) -> None:
    root = make_project(tmp_path, f'[images]\ntexlive = "{image}"\n')
    cfg = config.load(root)

    if valid:
        assert cfg.image("texlive") == image
    else:
        with pytest.raises(config.ConfigError):
            cfg.image("texlive")
