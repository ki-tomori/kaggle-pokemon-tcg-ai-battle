# CLAUDE.md — Development Rules for This Repository

Claude Code はこのファイルを読み、以下のルールに従って開発を行うこと。

## プロジェクト概要

Kaggle コンペのポートフォリオリポジトリ。転職用に分析プロセス・実装力・再現性を示すことが目的。

## ディレクトリ構成ルール

| ディレクトリ | 用途 |
|---|---|
| `src/` | 再利用可能な Python モジュール（本番想定コード） |
| `notebooks/` | EDA・プロトタイピング用 Jupyter Notebook |
| `experiments/` | 実験設定・ログ（YAML / JSON） |
| `reports/` | 分析レポート・図表 |
| `tests/` | pytest によるユニットテスト |
| `submissions/` | Kaggle 提出ファイル（git 管理外） |
| `data/` | データファイル（git 管理外） |

- Notebook でプロトした処理は `src/` に移植してスクリプト化する。
- `src/` のファイルは単体でも `python src/arena.py` のように実行できる構造にする。

## コーディングルール

- Python バージョン: 3.10+
- フォーマッター: `black`、リンター: `flake8`（設定は `requirements.txt` に含める）
- 型ヒントを積極的に使用する（関数の引数・戻り値）
- パスのハードコードは禁止。`src/config.py` に定義した定数を使う
- シードは `src/config.py` の `SEED` で一元管理する
- ログは `print()` でなく `logging` モジュールを使う

## セキュリティルール

- `data/`、`models/`、`.env`、`submissions/*.csv` は `.gitignore` で管理されており、**絶対に git add しない**
- API キー・認証情報はコードにハードコードせず `.env` で管理する
- Kaggle データセットの中身を Notebook のアウトプットに残さない（`nbstripout` 推奨）

## git ルール

- コミットメッセージは英語で書く（例: `feat: add feature engineering for card type`）
- 1 コミット = 1 つの論理的な変更
- 実験結果は `experiments/` にログを残してからコミットする
- `main` ブランチには直接コミットしない（実験は `exp/001-baseline` のようなブランチを切る）

## ファイル作成ルール

- 新しい機能は既存ファイルを編集することを優先し、不要なファイルを増やさない
- コメントは「なぜ（Why）」を書く。「何を（What）」はコード自体が示す
- docstring は関数の目的と引数・戻り値を 1〜3 行で記述する

## 禁止事項

- `data/` 配下のファイルを読み込んで内容を出力すること（データ漏洩リスク）
- `submissions/` 配下のファイル（提出パッケージ一式。`cg/` SDK 含む）を git に追加すること
- `requirements.txt` に使用していないライブラリを追加すること
- `main` ブランチへの force push
