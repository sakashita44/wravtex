import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from wravtex import config
from wravtex.build import build
from wravtex.errors import WravtexError

Handler = Callable[[argparse.Namespace], int]


def _load_config(args: argparse.Namespace) -> config.Config:
    project: Path | None = args.project
    root = project if project is not None else config.find_root(Path.cwd())
    return config.load(root)


def _build(args: argparse.Namespace) -> int:
    cfg = _load_config(args)
    profile = cfg.profile(args.profile)
    pdf = build(cfg, profile, args.output)
    print(f"出力: {pdf}")
    return 0


def _not_implemented(args: argparse.Namespace) -> int:
    raise WravtexError(f"{args.command} は未実装です")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wravtex",
        description="LaTeX の標準ツールを TeX Live のコンテナで実行する",
    )
    project = argparse.ArgumentParser(add_help=False)
    project.add_argument(
        "--project",
        type=Path,
        help=f"{config.CONFIG_FILE} があるディレクトリ（省略時は作業ディレクトリから上位へ探す）",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    def add(name: str, help: str, handler: Handler) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help, description=help, parents=[project])
        p.set_defaults(handler=handler)
        return p

    add("init", "プロジェクトの雛形を出力する", _not_implemented)

    build_cmd = add("build", "作業ツリーの原稿を組版して PDF を出力する", _build)
    build_cmd.add_argument("profile", help=f"{config.CONFIG_FILE} のプロファイル名")
    build_cmd.add_argument("-o", "--output", type=Path, help="PDF の保存先")

    add("diff", "2 つの版の差分 PDF を出力する", _not_implemented)
    add("clean", "生成物を削除する", _not_implemented)
    add("docx", "原稿を Word 形式に変換する", _not_implemented)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler: Handler = args.handler
    try:
        return handler(args)
    except WravtexError as e:
        print(f"wravtex: error: {e}", file=sys.stderr)
        return e.exit_code
