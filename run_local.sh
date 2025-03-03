#!/bin/bash

# 仮想環境をアクティベート
source .venv/bin/activate

# 環境変数を設定
export DATA_DIR=./data
# .env ファイルから環境変数を読み込む
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "Loaded environment variables from .env file"
else
  echo "Warning: .env file not found"
  # 必須の環境変数が設定されているか確認
  if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY is not set"
    exit 1
  fi
  if [ -z "$GEMINI_MODEL_NAME" ]; then
    echo "Error: GEMINI_MODEL_NAME is not set"
    exit 1
  fi
fi

# 環境変数の値を確認（デバッグ用）
echo "Using DATA_DIR: $DATA_DIR"
echo "Using GEMINI_MODEL_NAME: $GEMINI_MODEL_NAME"

# コマンドライン引数に基づいて実行するモジュールを決定
if [ "$1" == "collector" ]; then
  echo "Running collector module..."
  python -m nook.local.collector
elif [ "$1" == "viewer" ]; then
  echo "Starting viewer at http://localhost:8080..."
  python -m nook.local.viewer
else
  echo "Usage: ./run_local.sh [collector|viewer]"
  echo "  collector: Run the data collection module"
  echo "  viewer: Start the web viewer"
  exit 1
fi 