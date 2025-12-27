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
- **デプロイ**: Vercel

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

### Vercelでの制限と問題

**Vercelのサーバーレス環境では、このアプリケーションは動作しません。**

理由：
1. **Selenium/ChromeDriverが動作しない**: Vercelの環境にはChromeDriverやChromeバイナリがインストールされていません
2. **Pythonスクリプトの実行制限**: サーバーレス関数はリクエスト終了後にプロセスが終了するため、長時間実行されるバックグラウンドジョブが動作しません
3. **実行時間制限**: 最大300秒（5分）の制限がありますが、Selenium処理はそれ以上かかる可能性があります

### 推奨される代替案

このアプリケーションを本番環境で使用するには、以下のいずれかの方法を推奨します：

#### 1. 別のホスティングサービスを使用（推奨）

以下のサービスでは、Selenium/ChromeDriverが動作します：

- **Railway** (https://railway.app)
  - Python環境とChromeDriverをサポート
  - 無料プランあり
  - デプロイが簡単

- **Render** (https://render.com)
  - Webサービスとしてデプロイ可能
  - 無料プランあり

- **Fly.io** (https://fly.io)
  - Dockerコンテナとしてデプロイ可能
  - ChromeDriverを含むカスタムイメージを作成可能

#### 2. Puppeteer/Playwrightに変更

Node.jsネイティブのヘッドレスブラウザを使用：

- **Puppeteer**: Chrome/Chromiumを制御
- **Playwright**: 複数ブラウザをサポート

これらはVercelでも動作する可能性がありますが、設定が複雑です。

#### 3. 外部スクレイピングサービスを使用

- **Browserless** (https://www.browserless.io)
- **ScrapingBee** (https://www.scrapingbee.com)
- **Apify** (https://apify.com)

これらのサービスは、Selenium/Puppeteerをクラウドで実行します。

## 使用方法

1. ブラウザでアプリを開く
2. 取得したい年月（および日）を選択
3. 「スケジュール取得を開始」ボタンをクリック
4. 処理が完了するまで待機（進捗バーで確認可能）
5. 完了後、CSVファイルをダウンロード

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
├── requirements.txt      # Python依存関係
└── vercel.json           # Vercel設定
```

## ライセンス

MIT
