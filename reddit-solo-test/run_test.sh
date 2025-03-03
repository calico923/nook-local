#!/bin/bash
# Reddit Explorerのテストを実行するスクリプト

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境が存在する場合はアクティベート
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# テストの実行
python3 test_reddit_explorer.py

# 終了ステータスを保存
STATUS=$?

# 実行結果を表示
if [ $STATUS -eq 0 ]; then
    echo -e "\n\033[0;32mテストが正常に完了しました。\033[0m"
else
    echo -e "\n\033[0;31mテストが失敗しました。\033[0m"
fi

exit $STATUS
