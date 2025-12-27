# Next.js + Python + ChromeDriver 環境のDockerfile
FROM node:20-slim

# Python3とChrome/ChromeDriverの依存関係をインストール
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Chromeをインストール
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriverをインストール（Chromeのバージョンに合わせて）
RUN apt-get update && apt-get install -y unzip curl \
    && CHROME_MAJOR_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) \
    && echo "Chrome major version: ${CHROME_MAJOR_VERSION}" \
    && CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR_VERSION}" | head -1 | tr -d '\n\r') \
    && if [ -z "$CHROMEDRIVER_VERSION" ] || echo "$CHROMEDRIVER_VERSION" | grep -q "<!DOCTYPE"; then \
         echo "Using alternative method to get ChromeDriver version..."; \
         CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | grep -o '"version":"[0-9.]*"' | head -1 | cut -d'"' -f4); \
       fi \
    && echo "Installing ChromeDriver version: ${CHROMEDRIVER_VERSION}" \
    && wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver* /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# package.jsonとrequirements.txtをコピー
COPY package*.json ./
COPY requirements.txt ./

# Node.jsの依存関係をインストール（devDependenciesも含める）
RUN npm ci

# Pythonの依存関係をインストール
RUN pip3 install --no-cache-dir -r requirements.txt

# アプリケーションのファイルをコピー
COPY . .

# Next.jsアプリをビルド
RUN npm run build

# ポート3000を公開
EXPOSE 3000

# アプリケーションを起動
CMD ["npm", "start"]
