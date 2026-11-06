import os
import shutil
import tempfile
from pathlib import Path

from wravtex import container
from wravtex.config import Config, Profile
from wravtex.errors import WravtexError


class BuildError(WravtexError):
    pass


def build(config: Config, profile: Profile, output: Path | None) -> Path:
    image = config.image("texlive")
    mirror_source_directories(profile)
    outdir = container.container_path(config.root, profile.out)
    status = container.run(
        config.root, image, profile.dir, ["latexmk", f"-outdir={outdir}", profile.main]
    )
    log = profile.out / Path(profile.main).with_suffix(".log").name
    if status:
        raise BuildError(f"latexmk が終了コード {status} で失敗しました。ログ: {log}")
    pdf = profile.out / profile.pdf_name
    if output is None:
        return pdf
    replace_atomically(pdf, output)
    return output


def mirror_source_directories(profile: Profile) -> None:
    # \include{sub/file} は出力先の sub/file.aux に書き込むが、TeX は出力先の
    # サブディレクトリを作成しないため、原稿ディレクトリと同じ構成を先に作る
    profile.out.mkdir(parents=True, exist_ok=True)
    for current, subdirs, files in os.walk(profile.dir):
        directory = Path(current)
        subdirs[:] = [
            name
            for name in subdirs
            if not name.startswith(".") and directory / name != profile.out
        ]
        if any(name.endswith(".tex") for name in files):
            relative = directory.relative_to(profile.dir)
            (profile.out / relative).mkdir(parents=True, exist_ok=True)


def replace_atomically(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # os.replace が置き換えを原子的に行えるのは同じファイルシステムの中に限られるため、
    # 一時ファイルは保存先と同じディレクトリに作る
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=f".{dest.name}.", suffix=".tmp")
    os.close(fd)
    try:
        shutil.copyfile(src, tmp)
        os.replace(tmp, dest)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
