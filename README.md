# wravtex

wravtex は、Git の版と DVC で管理する図版を指定して、LaTeX の標準ツール（latexmk、latexdiff、latexpand、pandoc）を TeX Live のコンテナで実行する CLI である。組版に用いるイメージは論文リポジトリの `wravtex.toml` にダイジェストで記録し、同じ版と同じ設定から同じ環境で組版できるようにする。TeX Live、フォントキャッシュ、TeX のユーザー設定はホストに置かず、コンテナと wravtex が管理する Docker ボリュームに閉じ込める。

組版の手順（エンジン、文献処理、実行回数）は原稿ディレクトリの `.latexmkrc` に従う。wravtex を使わなくても、原稿は TeX Live と latexmk で組版できる。

## 前提とするツール

- Docker: TeX Live と pandoc のコンテナを実行する
- uv: wravtex を論文リポジトリの開発用の依存として導入し、実行する
- Git: 過去の版を組版する操作と差分を出力する操作で用いる

DVC で図版を管理する場合は、DVC とリモート用のプラグイン（dvc-ssh など）を論文リポジトリの依存に加えること。wravtex は PATH 上の `dvc` コマンドを呼び出す。

## 導入方法

論文リポジトリで次のコマンドを実行し、wravtex を開発用の依存に加える。

```bash
uv add --dev git+https://github.com/sakashita44/wravtex
```

導入後は `uv run wravtex` で実行する。サブコマンドの一覧は次のコマンドで確認のこと。

```bash
uv run wravtex --help
```

## 開発

開発環境の構築とフックの有効化は次のコマンドで行う。

```bash
bash scripts/setup.sh
```
