#!/bin/bash
# スクリプトに実行権限を付与してテストを実行する

# カレントディレクトリに移動
cd "$(dirname "$0")"

# 実行権限の付与
chmod +x run_test.sh run_e2e_test.sh

# ユニットテストを実行
echo "ユニットテストを実行します..."
python3 test_reddit_explorer.py

# 終了コードを確認
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo -e "\n\033[0;32mテストが正常に完了しました。\033[0m"
else
    echo -e "\n\033[0;31mテストが失敗しました。終了コード: $exit_code\033[0m"
fi

exit $exit_code
