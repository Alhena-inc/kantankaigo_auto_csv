# かんたん介護 スケジュール取得 Webアプリ

かんたん介護ソフトからスケジュール情報を自動取得するWebアプリケーションです。

## 機能

- 年月日を選択してスケジュール情報を取得
- バックグラウンドでSelenium処理を実行
- リアルタイムで進捗状況を表示
- CSVファイルとしてダウンロード可能

## 技術スタック

- **フロントエンド**: Next.js 14 (React)
- **バックエンド**: Next.js API Routes
- **スクレイピング**: Python + Selenium
- **デプロイ**: Render (Docker)

## セットアップ

### 1. 依存関係のインストール

```bash
# Node.jsの依存関係
npm install

# Pythonの依存関係
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.local`ファイルを作成し、以下の環境変数を設定してください：

```
KANTAN_USERNAME=your_username
KANTAN_PASSWORD=your_password
KANTAN_GROUP_NAME=your_group_name
```

### 3. ChromeDriverのインストール

Seleniumを使用するため、ChromeDriverが必要です。

```bash
# macOSの場合
brew install chromedriver

# または、手動でダウンロード
# https://chromedriver.chromium.org/downloads
```

### 4. 開発サーバーの起動

```bash
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開きます。

## Renderへのデプロイ（推奨）

### 1. Renderアカウントの準備

1. [Render](https://render.com)にアクセスしてアカウントを作成（GitHubアカウントでサインイン可能）
2. GitHubアカウントと連携

### 2. 新しいWebサービスを作成

1. Renderダッシュボードで「New +」→「Web Service」を選択
2. GitHubリポジトリ `kantankaigo_auto_csv` を選択
3. 以下の設定を行う：
   - **Name**: `kantankaigo-auto-csv`（任意の名前）
   - **Environment**: `Docker`
   - **Region**: `Oregon (US West)` または `Singapore (Asia Pacific)`
   - **Branch**: `main`
   - **Root Directory**: （空白のまま）
   - **Dockerfile Path**: `./Dockerfile`
   - **Instance Type**: `Starter`（無料プランは15分後にスリープするため、本番環境では有料プラン推奨）

### 3. 環境変数の設定

Renderダッシュボードの「Environment」セクションで、以下の環境変数を追加：

- `KANTAN_USERNAME` = あなたのユーザー名
- `KANTAN_PASSWORD` = あなたのパスワード
- `KANTAN_GROUP_NAME` = あなたのグループ名
- `NODE_ENV` = `production`

### 4. デプロイ

1. 「Create Web Service」をクリック
2. 初回ビルドが開始されます（5-10分程度かかります）
3. デプロイが完了すると、URLが表示されます（例: `https://kantankaigo-auto-csv.onrender.com`）

### 5. 動作確認

デプロイされたURLにアクセスして、アプリケーションが正常に動作することを確認してください。

### 注意事項

- **無料プラン**: 15分間リクエストがないとスリープします。初回アクセス時に起動するまで時間がかかります
- **有料プラン**: 常時起動で、より高速に動作します（Starterプラン: $7/月）
- **ビルド時間**: 初回ビルドは5-10分程度かかります（Dockerイメージのビルドのため）

## ⚠️ 重要な注意事項

このアプリケーションは、Selenium/ChromeDriverが必要なため、サーバーレス環境（Vercelなど）では動作しません。Dockerコンテナを実行できるホスティングサービス（Render、Railway、Fly.ioなど）でのデプロイが必要です。

## 使用方法

### Webアプリケーションでの使用

1. ブラウザでアプリを開く
2. 取得したい年月（および日）を選択
3. 「スケジュール取得を開始」ボタンをクリック
4. 処理が完了するまで待機（進捗バーで確認可能）
5. 完了後、CSVファイルをダウンロード

### ターミナルでの実行

Pythonスクリプトを直接実行することも可能です。

#### 基本的な使用方法

```bash
# 年月を指定して実行（例: 2025年11月）
python auto_login.py --year 2025 --month 11

# 特定の日を指定して実行（例: 2025年11月15日）
python auto_login.py --year 2025 --month 11 --day 15
```

#### コマンドライン引数

- `--year` (必須): 対象年（例: 2025）
- `--month` (必須): 対象月（1-12）
- `--day` (オプション): 対象日（1-31）
- `--job-id` (オプション): ジョブID（進捗管理用）

#### 実行例

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

#### 実行結果

- 実行が成功すると、`schedule_YYYY_MM.csv`（または`schedule_YYYY_MM_DD.csv`）というファイルが生成されます
- ファイルはUTF-8 BOM形式で保存されるため、Excelで開いても文字化けしません

## ファイル構造

```
.
├── app/                    # Next.js App Router
│   ├── api/               # API Routes
│   │   ├── jobs/         # ジョブ管理API
│   │   └── download/      # ファイルダウンロードAPI
│   ├── page.tsx          # メインページ
│   └── layout.tsx        # レイアウト
├── lib/                   # ユーティリティ
│   ├── jobManager.ts     # ジョブ管理
│   └── scraperRunner.ts  # スクレイパー実行
├── auto_login.py         # Pythonスクレイピングスクリプト
├── Dockerfile            # Docker設定（Render用）
├── render.yaml           # Render設定ファイル
├── requirements.txt      # Python依存関係
├── package.json          # Node.js依存関係
└── tsconfig.json         # TypeScript設定
```

## ライセンス

MIT
