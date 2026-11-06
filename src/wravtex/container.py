import hashlib
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from wravtex.errors import WravtexError

CONTAINER_ROOT = PurePosixPath("/workdir")
CACHE_MOUNT = PurePosixPath("/cache")
CACHE_LABEL = "io.github.sakashita44.wravtex.image"
_HOME = PurePosixPath("/tmp/wravtex")

# TeX のユーザー領域はコンテナ内の一時領域へ向け、ホストやイメージのユーザー設定を読まないようにする。
# フォントキャッシュは組版ごとに再生成しないようボリュームへ置く。
# luaotfload は TEXMFCACHE、luatexja は TEXMFVAR に書き込むため、両方を向ける
ENVIRONMENT = {
    "HOME": str(_HOME),
    "TEXMFHOME": str(_HOME / "texmf"),
    "TEXMFCONFIG": str(_HOME / "texmf-config"),
    "TEXMFVAR": str(CACHE_MOUNT / "texmf-var"),
    "TEXMFCACHE": str(CACHE_MOUNT / "texmf-var"),
}


class ContainerError(WravtexError):
    pass


def container_path(root: Path, path: Path) -> str:
    return str(CONTAINER_ROOT / path.relative_to(root).as_posix())


def cache_volume_name(image: str) -> str:
    return f"wravtex-texmf-{hashlib.sha256(image.encode()).hexdigest()[:12]}"


def _docker(*args: str, quiet: bool = False) -> int:
    output = subprocess.DEVNULL if quiet else None
    try:
        return subprocess.run(
            ["docker", *args], stdout=output, stderr=output
        ).returncode
    except FileNotFoundError:
        raise ContainerError(
            "docker コマンドが見つかりません。Docker を導入してください"
        ) from None


def ensure_cache_volume(image: str) -> str:
    name = cache_volume_name(image)
    if _docker("volume", "inspect", name, quiet=True) == 0:
        return name
    created = _docker(
        "volume", "create", "--label", f"{CACHE_LABEL}={image}", name, quiet=True
    )
    if created != 0:
        raise ContainerError(f"Docker ボリューム {name} を作成できません")
    # マウント先がイメージにないため、ボリュームは root 所有の 755 で初期化される。
    # Linux でホストの UID として実行するコンテナからも書き込めるよう、権限を開く
    chmod = _docker(
        "run",
        "--rm",
        "--user",
        "0:0",
        "--volume",
        f"{name}:{CACHE_MOUNT}",
        image,
        "chmod",
        "1777",
        str(CACHE_MOUNT),
    )
    if chmod != 0:
        _docker("volume", "rm", name, quiet=True)
        raise ContainerError(f"Docker ボリューム {name} を初期化できません")
    return name


def _user_options() -> list[str]:
    # Linux ではコンテナ内の UID がそのまま生成物の所有者になる。
    # Docker Desktop はファイル共有の層でホストのユーザーに対応付けるため指定しない
    if sys.platform == "linux":
        return ["--user", f"{os.getuid()}:{os.getgid()}"]
    return []


def run(root: Path, image: str, workdir: Path, command: Sequence[str]) -> int:
    volume = ensure_cache_volume(image)
    env = [
        option
        for key, value in ENVIRONMENT.items()
        for option in ("--env", f"{key}={value}")
    ]
    return _docker(
        "run",
        "--rm",
        "--volume",
        f"{root}:{CONTAINER_ROOT}",
        "--volume",
        f"{volume}:{CACHE_MOUNT}",
        "--workdir",
        container_path(root, workdir),
        *env,
        *_user_options(),
        image,
        *command,
    )
