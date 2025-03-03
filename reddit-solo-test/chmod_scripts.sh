#!/bin/bash
# スクリプトに実行権限を付与する

# カレントディレクトリに移動
cd "$(dirname "$0")"

# 実行権限の付与
chmod +x run_test.sh
chmod +x run_e2e_test.sh
chmod +x "${0}"  # このスクリプト自体

echo "実行権限を付与しました。"
