# Data Directory

このディレクトリは `.gitignore` により git 管理対象外です。データファイルをここに配置してください。

## ディレクトリ構成

```
data/
├── raw/        # Kaggle からダウンロードした元データ（変更しない）
│                 EN/JP カードデータCSV、カードIDリストPDF、ptcg_engine（C++エンジン源）、
│                 sample_submission/（対戦エンジンの cg Python SDK）を含む
└── decks/      # 自作のデッキ CSV（src/deck.py が生成）
```

## データのダウンロード方法

1. [Kaggle API](https://github.com/Kaggle/kaggle-api) をセットアップする

```bash
pip install kaggle
# ~/.kaggle/kaggle.json に API キーを配置
```

2. コンペデータをダウンロードする

```bash
kaggle competitions download -c pokemon-tcg-ai-battle -p data/raw/
unzip -o data/raw/pokemon-tcg-ai-battle.zip -d data/raw/
```

## 注意事項

- `data/` 配下のファイルは **絶対に git add しないこと**
- Kaggle の利用規約、および `ptcg_engine` に同梱の
  `LicenseRef-PTCG-ABC-Competition-Use-Only.txt` により、このデータ・エンジン・SDK の
  再配布は禁止されています。コンペ参加目的以外での使用、コンペ終了後の保持も禁止です
