# かんたん介護 スケジュール取得スクリプト

かんたん介護ソフトからスケジュール情報を自動取得するPythonスクリプトです。

## 機能

- 年月日を指定してスケジュール情報を取得
- Seleniumを使用した自動スクレイピング
- CSVファイルとして出力（Excel対応）

## 技術スタック

- **言語**: Python 3
- **スクレイピング**: Selenium + ChromeDriver

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. ChromeDriverのインストール

Seleniumを使用するため、ChromeDriverが必要です。

```bash
# macOSの場合
brew install chromedriver

# または、手動でダウンロード
# https://chromedriver.chromium.org/downloads
```

### 3. 環境変数の設定（オプション）

環境変数で認証情報を設定することも可能です：

```bash
export KANTAN_USERNAME=your_username
export KANTAN_PASSWORD=your_password
export KANTAN_GROUP_NAME=your_group_name
```

環境変数を設定しない場合は、`auto_login.py`内のデフォルト値が使用されます。

## 使用方法

### 基本的な使用方法

```bash
# 年月を指定して実行（例: 2025年11月）
python auto_login.py --year 2025 --month 11

# 特定の日を指定して実行（例: 2025年11月15日）
python auto_login.py --year 2025 --month 11 --day 15
```

### コマンドライン引数

- `--year` (必須): 対象年（例: 2025）
- `--month` (必須): 対象月（1-12）
- `--day` (オプション): 対象日（1-31）
- `--job-id` (オプション): ジョブID（進捗管理用）

### 実行例

```bash
# 2025年11月の全データを取得
python auto_login.py --year 2025 --month 11

# 2025年11月15日のデータを取得
python auto_login.py --year 2025 --month 11 --day 15

# 環境変数から認証情報を取得する場合
export KANTAN_USERNAME=your_username
export KANTAN_PASSWORD=your_password
export KANTAN_GROUP_NAME=your_group_name
python auto_login.py --year 2025 --month 11
```

### 実行結果

- 実行が成功すると、`schedule_YYYY_MM.csv`（または`schedule_YYYY_MM_DD.csv`）というファイルが生成されます
- ファイルはUTF-8 BOM形式で保存されるため、Excelで開いても文字化けしません
- CSVファイルには以下の列が含まれます：
  - 利用者名
  - 日付
  - 時間帯
  - サービス内容
  - スタッフ名

## ファイル構造

```
.
├── auto_login.py         # Pythonスクレイピングスクリプト
├── requirements.txt      # Python依存関係
└── README.md            # このファイル
```

## 注意事項

- ChromeDriverはChromeブラウザのバージョンと互換性のあるバージョンを使用してください
- スクレイピング処理には時間がかかる場合があります（利用者数に応じて）
- 処理中はChromeブラウザが自動で起動します（ヘッドレスモード）

## ライセンス

MIT
