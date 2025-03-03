#!/usr/bin/env python3
"""
Reddit Explorerの実際のAPIを使用したE2Eテスト
"""
import os
import sys
import argparse
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 環境変数の読み込み
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# テスト対象のモジュールをインポート
from nook.local.services.reddit_explorer import RedditExplorer, Config


def run_e2e_test(subreddits=None, limit=2, verbose=False):
    """
    Reddit Explorerの実際のAPIを使用したE2Eテスト
    
    Args:
        subreddits: テスト対象のサブレディットリスト（指定しない場合はデフォルト設定を使用）
        limit: 取得する投稿数（デフォルト: 2）
        verbose: 詳細な出力を表示するかどうか
    """
    # 一時的にlimitを変更
    original_limit = Config.reddit_top_posts_limit
    Config.reddit_top_posts_limit = limit
    
    try:
        print("=== Reddit Explorer E2Eテスト ===")
        
        # RedditExplorerのインスタンスを作成
        explorer = RedditExplorer()
        
        # サブレディットが指定されている場合は一時的に上書き
        if subreddits:
            explorer._subreddits = subreddits
            print(f"テスト対象サブレディット: {', '.join(subreddits)}")
        else:
            print(f"テスト対象サブレディット: {', '.join(explorer._subreddits)}")
        
        print(f"取得投稿数: {limit}件/サブレディット")
        
        # 個別のサブレディットから投稿を取得するテスト
        for subreddit in explorer._subreddits:
            print(f"\n--- r/{subreddit}の投稿を取得中... ---")
            try:
                posts = explorer._retrieve_hot_posts(subreddit)
                print(f"{len(posts)}件の投稿を取得しました。")
                
                if verbose:
                    for i, post in enumerate(posts, 1):
                        print(f"\n[{i}] タイトル: {post.title}")
                        print(f"    タイプ: {post.type}")
                        print(f"    Upvotes: {post.upvotes}")
                        
                        # コメント取得のテスト
                        print(f"    コメント取得中...")
                        comments = explorer._retrieve_top_comments_of_post(post.id)
                        post.comments = comments
                        print(f"    {len(comments)}件のコメントを取得しました。")
                        
                        if len(comments) > 0 and verbose:
                            print(f"    最初のコメント: {comments[0]['text'][:50]}...")
                        
                        # サマリー生成のテスト
                        print(f"    サマリー生成中...")
                        summary = explorer._summarize_reddit_post(post)
                        post.summary = summary
                        print(f"    サマリー生成完了: {len(summary)}文字")
                        
                        if verbose:
                            print(f"    サマリーの一部: {summary[:100]}...")
            
            except Exception as e:
                print(f"エラーが発生しました: {type(e).__name__}: {e}")
                continue
        
        # 完全な実行をテスト
        print("\n--- 完全な実行をテスト中... ---")
        try:
            explorer()
            print("完全な実行が成功しました。")
            
            # 出力ファイルを確認
            data_dir = os.environ.get("DATA_DIR", "./data")
            output_dir = os.path.join(data_dir, "reddit_explorer")
            
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                if files:
                    print(f"出力ファイルが生成されました: {', '.join(files)}")
                else:
                    print("出力ディレクトリは作成されましたが、ファイルが生成されていません。")
            else:
                print("出力ディレクトリが作成されていません。")
        
        except Exception as e:
            print(f"完全な実行中にエラーが発生しました: {type(e).__name__}: {e}")
        
        print("\n=== テスト完了 ===")
    
    finally:
        # 設定を元に戻す
        Config.reddit_top_posts_limit = original_limit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reddit Explorer E2Eテスト')
    parser.add_argument('-s', '--subreddits', nargs='+', help='テスト対象のサブレディット（空白区切りで複数指定可能）')
    parser.add_argument('-l', '--limit', type=int, default=2, help='取得する投稿数（デフォルト: 2）')
    parser.add_argument('-v', '--verbose', action='store_true', help='詳細な出力を表示する')
    
    args = parser.parse_args()
    
    run_e2e_test(args.subreddits, args.limit, args.verbose)
