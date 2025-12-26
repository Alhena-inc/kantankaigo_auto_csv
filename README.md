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

## Vercelへのデプロイ

### 1. Vercelアカウントの準備

[Vercel](https://vercel.com)にアカウントを作成し、GitHubリポジトリと連携します。

### 2. 環境変数の設定

Vercelのダッシュボードで以下の環境変数を設定：

- `KANTAN_USERNAME`
- `KANTAN_PASSWORD`
- `KANTAN_GROUP_NAME`

### 3. デプロイ

```bash
# Vercel CLIを使用する場合
npm i -g vercel
vercel
```

または、GitHubにプッシュすると自動的にデプロイされます。

## 注意事項

### Vercelでの制限

Vercelのサーバーレス関数には以下の制限があります：

1. **実行時間**: 最大300秒（5分）
2. **メモリ**: 最大1024MB
3. **ChromeDriver**: Vercelの環境ではChromeDriverが利用できない可能性があります

### 推奨される代替案

VercelでSeleniumを実行するのは難しいため、以下の代替案を検討してください：

1. **別のホスティングサービスを使用**
   - Railway
   - Render
   - AWS Lambda (ChromeDriver対応)

2. **Puppeteer/Playwrightを使用**
   - Node.jsネイティブのヘッドレスブラウザ
   - Vercelでより動作しやすい可能性があります

3. **外部APIサービスを使用**
   - ScrapingBee
   - Apify
   - Browserless

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

