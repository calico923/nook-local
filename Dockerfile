FROM python:3.11-slim

WORKDIR /app

# 必要なツールをインストール
RUN apt-get update && apt-get install -y git make

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pytz

# アプリケーションコードをコピー
COPY . .

# Webサーバーを公開するポート
EXPOSE 8080

# デフォルトのコマンド
CMD ["python", "app.py"]