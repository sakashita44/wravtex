import argparse
import sys
from collections.abc import Sequence

COMMANDS = {
    "init": "プロジェクトの雛形を出力する",
    "build": "原稿を組版して PDF を出力する",
    "diff": "2 つの版の差分 PDF を出力する",
    "clean": "生成物を削除する",
    "docx": "原稿を Word 形式に変換する",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wravtex",
        description="LaTeX の標準ツールを TeX Live のコンテナで実行する",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    for name, help in COMMANDS.items():
        sub.add_parser(name, help=help, description=help)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"wravtex: error: {args.command} は未実装です", file=sys.stderr)
    return 2
