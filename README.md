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

## 設定

論文リポジトリのルートに `wravtex.toml` を配置する。wravtex は作業ディレクトリから上位へ最も近い `wravtex.toml` を探し、そのディレクトリをプロジェクトのルートとする。`--project` でルートを明示することもできる。

```toml
[images]
texlive = "texlive/texlive:latest@sha256:<ダイジェスト>"

[profiles.paper]
dir = "paper"
main = "main.tex"
out = "out/paper"
```

- `images.texlive`: 組版に用いる TeX Live のイメージ。再現性のため、ダイジェストを含む参照で指定すること。ダイジェストは `docker buildx imagetools inspect texlive/texlive:latest` の `Digest` で確認できる
- `profiles.<名前>`: 原稿ごとのプロファイル。`dir` は原稿ディレクトリ、`main` は原稿ディレクトリからのルートファイルのパス、`out` は生成物の出力先で、いずれもプロジェクトのルートからの相対パスで指定する。`out` には、原稿ディレクトリ自体と、原稿ディレクトリを含むディレクトリは指定できない。原稿ディレクトリの中の専用のディレクトリ（例: `dir = "."`、`out = "out"`）は指定できる

コンテナにはプロジェクトのルートだけがマウントされる。原稿から参照するクラスファイル、文献ファイル、図版は、プロジェクトのルートの内側に配置すること。

## 原稿の組版

```bash
uv run wravtex build paper
```

`--project <ディレクトリ>` は、サブコマンドの後に指定する（例: `uv run wravtex build --project ../paper-repo paper`）。

原稿ディレクトリで latexmk が実行され、中間ファイルと PDF は `out` に出力される。`\include` で読み込むファイルの `.aux` を出力できるよう、`.tex` を含むサブディレクトリと同じ構成のディレクトリが `out` に作成される。`-o <パス>` を指定すると、PDF をそのパスにも保存する。組版に失敗した場合、`-o` の保存先の既存のファイルは変更されない。

組版の手順は原稿ディレクトリの `.latexmkrc` に定義する。wravtex は出力先を latexmk の `-outdir` で指定するため、`.latexmkrc` でエンジンや biber のコマンドを定義する場合は、オプションを受け渡す `%O` を含めること。

```perl
$pdf_mode = 4;
$lualatex = 'lualatex -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
```

latexmk は出力先のディレクトリで bibtex を実行し、原稿ディレクトリを文献ファイルの検索パスに加える。そのため、`\bibliography{../bibliography/refs}` のように `../` で始まるパスで指定した文献ファイルは bibtex から見つからない。原稿ディレクトリの外の文献ファイルを BibTeX で参照する場合は、`\bibliography` にはファイル名だけを指定し、`.latexmkrc` で `BIBINPUTS` に絶対パスを追加すること。

```perl
use Cwd 'abs_path';
ensure_path('BIBINPUTS', abs_path('../bibliography'));
```

pdfLaTeX の epstopdf による EPS の自動変換は、変換後の PDF を原稿ディレクトリに作成する。原稿ディレクトリに生成物を残さない場合は、EPS をあらかじめ PDF に変換して配置すること。

LuaLaTeX のフォントキャッシュは、イメージごとの Docker ボリューム（`wravtex-texmf-` で始まる名前）に保存され、次回以降の組版で再利用される。コンテナ内の `HOME`、`TEXMFHOME`、`TEXMFCONFIG` はコンテナ内の一時領域を指し、ホストの TeX の設定は読み込まれない。Linux では、コンテナ内のプロセスを実行ユーザーの UID と GID で実行し、生成物の所有者を実行ユーザーにする。

## 開発

開発環境の構築とフックの有効化は次のコマンドで行う。

```bash
bash scripts/setup.sh
```

TeX Live のコンテナで組版する試験は、環境変数 `WRAVTEX_TEST_IMAGE` にイメージを指定した場合だけ実行される。CI で用いるイメージは `.github/workflows/ci.yml` で確認のこと。

```bash
WRAVTEX_TEST_IMAGE=texlive/texlive@sha256:<ダイジェスト> uv run pytest
```
