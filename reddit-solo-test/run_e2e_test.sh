#!/bin/bash
# Reddit Explorer E2Eテストを実行するスクリプト

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境が存在する場合はアクティベート
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# デフォルトのパラメータ
LIMIT=2
VERBOSE=""
SUBREDDITS=""

# ヘルプメッセージ
function show_help {
    echo "使用方法: $0 [オプション]"
    echo "オプション:"
    echo "  -h, --help         このヘルプメッセージを表示"
    echo "  -s, --subreddits   テスト対象のサブレディット（空白区切りで複数指定可能）"
    echo "  -l, --limit        取得する投稿数（デフォルト: 2）"
    echo "  -v, --verbose      詳細な出力を表示する"
    echo ""
    echo "例:"
    echo "  $0 -s Python programming -l 3 -v"
}

# コマンドライン引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--subreddits)
            shift
            SUBREDDITS=""
            while [[ $# -gt 0 && ! $1 =~ ^- ]]; do
                SUBREDDITS="$SUBREDDITS $1"
                shift
            done
            SUBREDDITS=$(echo $SUBREDDITS | xargs)  # 前後の空白を削除
            ;;
        -l|--limit)
            shift
            LIMIT=$1
            shift
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        *)
            echo "エラー: 不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

# コマンドの構築
CMD="python3 e2e_test.py --limit $LIMIT $VERBOSE"
if [[ -n "$SUBREDDITS" ]]; then
    CMD="$CMD --subreddits $SUBREDDITS"
fi

# テストの実行
echo "実行コマンド: $CMD"
eval $CMD

# 終了ステータスを保存
STATUS=$?

# 実行結果を表示
if [ $STATUS -eq 0 ]; then
    echo -e "\n\033[0;32mE2Eテストが正常に完了しました。\033[0m"
else
    echo -e "\n\033[0;31mE2Eテストが失敗しました。\033[0m"
fi

exit $STATUS
