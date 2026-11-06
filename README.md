# wravtex

wravtex は、Git の版と DVC で管理する図版を指定して、LaTeX の原稿の組版、版の間の差分 PDF の生成、Word 形式への変換を行う CLI である。LaTeX の標準ツール（latexmk、latexdiff、latexpand）は TeX Live のコンテナで実行される。pandoc は pandoc のコンテナで実行される。利用者は、組版に用いるイメージを論文リポジトリの `wravtex.toml` にダイジェストで記録する。これにより、同じ版と同じ設定から同じ環境で組版できる。TeX Live、フォントキャッシュ、TeX のユーザー設定はホストには配置されず、コンテナと wravtex が管理する Docker ボリュームに格納される。

組版の手順（エンジン、文献処理、実行回数）は原稿ディレクトリの `.latexmkrc` に従う。wravtex を用いなくても、原稿は TeX Live と latexmk で組版できる。

## 前提とするツール

- Docker: TeX Live と pandoc のコンテナを実行するために用いる
- uv: wravtex を論文リポジトリの開発用の依存として導入し、実行するために用いる
- Git: 過去の版を組版する操作と差分を出力する操作に用いる

DVC で図版を管理する場合は、DVC とリモート用のプラグイン（dvc-ssh など）を論文リポジトリの依存に追加すること。wravtex は PATH 上の `dvc` コマンドを呼び出す。

## 導入方法

論文リポジトリで次のコマンドを実行すると、wravtex が開発用の依存に追加される。

```bash
uv add --dev git+https://github.com/sakashita44/wravtex
```

導入後は `uv run wravtex` で実行する。サブコマンドの一覧は次のコマンドで確認のこと。

```bash
uv run wravtex --help
```

## 開発

次のコマンドを実行すると、開発環境が構築され、フックが有効化される。

```bash
bash scripts/setup.sh
```
