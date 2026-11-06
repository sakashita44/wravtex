import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from wravtex.errors import WravtexError

CONFIG_FILE = "wravtex.toml"
_PINNED_IMAGE = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")


class ConfigError(WravtexError):
    exit_code = 2


@dataclass(frozen=True)
class Profile:
    name: str
    dir: Path
    main: str
    out: Path

    @property
    def pdf_name(self) -> str:
        return Path(self.main).with_suffix(".pdf").name


@dataclass(frozen=True)
class Config:
    root: Path
    data: dict[str, object]

    @property
    def path(self) -> Path:
        return self.root / CONFIG_FILE

    def image(self, kind: str) -> str:
        images = _table(self.data.get("images")) or {}
        value = images.get(kind)
        if not isinstance(value, str) or not _PINNED_IMAGE.match(value):
            raise ConfigError(
                f"{self.path} の images.{kind} に、イメージをダイジェストで固定した参照"
                "（例: texlive/texlive:latest@sha256:<64 桁の 16 進数>）を指定してください"
            )
        return value

    def profile(self, name: str) -> Profile:
        profiles = _table(self.data.get("profiles", {}))
        if profiles is None:
            raise ConfigError(f"{self.path} の profiles はテーブルで定義してください")
        if name not in profiles:
            defined = ", ".join(profiles) or "なし"
            raise ConfigError(
                f"{self.path} にプロファイル {name} がありません。定義済み: {defined}"
            )
        entry = _table(profiles[name])
        if entry is None:
            raise ConfigError(
                f"{self.path} の profiles.{name} はテーブルで定義してください"
            )
        fields = {key: self._string(name, entry, key) for key in ("dir", "main", "out")}

        manuscript = self._inside_root(name, "dir", fields["dir"])
        out = self._inside_root(name, "out", fields["out"])
        if not manuscript.is_dir():
            raise ConfigError(
                f"profiles.{name}.dir のディレクトリ {manuscript} がありません"
            )
        if not (manuscript / fields["main"]).is_file():
            raise ConfigError(
                f"profiles.{name}.main のファイル {manuscript / fields['main']} がありません"
            )
        if manuscript.is_relative_to(out):
            raise ConfigError(
                f"profiles.{name}.out には、原稿ディレクトリ {manuscript} を含まないディレクトリを指定してください"
            )
        return Profile(name=name, dir=manuscript, main=fields["main"], out=out)

    def _string(self, name: str, entry: dict[str, object], key: str) -> str:
        value = entry.get(key)
        if not isinstance(value, str) or not value:
            raise ConfigError(
                f"{self.path} の profiles.{name}.{key} を文字列で指定してください"
            )
        return value

    def _inside_root(self, name: str, key: str, value: str) -> Path:
        path = (self.root / value).resolve()
        if not path.is_relative_to(self.root):
            raise ConfigError(
                f"profiles.{name}.{key} には、プロジェクトのルート {self.root} の内側を指定してください"
            )
        return path


def _table(value: object) -> dict[str, object] | None:
    return cast(dict[str, object], value) if isinstance(value, dict) else None


def find_root(start: Path) -> Path:
    start = start.resolve()
    for directory in (start, *start.parents):
        if (directory / CONFIG_FILE).is_file():
            return directory
    raise ConfigError(f"{start} とその上位のディレクトリに {CONFIG_FILE} がありません")


def load(root: Path) -> Config:
    root = root.resolve()
    path = root / CONFIG_FILE
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise ConfigError(f"{path} がありません") from None
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path} を読み込めません: {e}") from None
    return Config(root=root, data=data)
