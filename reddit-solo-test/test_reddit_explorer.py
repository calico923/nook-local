#!/usr/bin/env python3
"""
Reddit Explorerのテストスクリプト
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import date
from importlib import reload

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 環境変数の読み込み
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# テストのためにimport時点を固定しておく
from nook.local.services.reddit_explorer import RedditExplorer, RedditPost, Config


class TestRedditExplorer(unittest.TestCase):
    """RedditExplorerクラスのテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成してDATAディレクトリとして使用
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ['DATA_DIR'] = self.temp_dir.name
        
        # RedditExplorerのインスタンスを作成
        self.explorer = RedditExplorer()
        
        # テスト用の投稿データ
        self.sample_post = RedditPost(
            type="text",
            id="abc123",
            title="Test Post Title",
            url=None,
            upvotes=100,
            text="This is a test post content.",
            permalink="https://www.reddit.com/r/test/comments/abc123/test_post_title/",
            comments=[
                {"text": "First comment", "upvotes": 50},
                {"text": "Second comment", "upvotes": 30},
                {"text": "Third comment", "upvotes": 10}
            ]
        )

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.temp_dir.cleanup()

    def test_initialization(self):
        """初期化が正しく行われるかテスト"""
        with patch('nook.local.common.gemini_client.create_client') as mock_create_client, \
             patch('praw.Reddit') as mock_reddit:
            # モックの設定
            mock_create_client.return_value = MagicMock()
            mock_reddit.return_value = MagicMock()
            
            # テスト対象のモジュールを再ロード
            import nook.local.services.reddit_explorer
            reload(nook.local.services.reddit_explorer)
            from nook.local.services.reddit_explorer import RedditExplorer

            # インスタンス化
            explorer = RedditExplorer()
            
            # Reddit APIクライアントが正しく初期化されたか確認
            mock_reddit.assert_called_once_with(
                client_id=os.environ.get("REDDIT_CLIENT_ID"),
                client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
                user_agent=os.environ.get("REDDIT_USER_AGENT"),
            )
            
            # Geminiクライアントが正しく初期化されたか確認
            mock_create_client.assert_called_once()
            
            # サブレディットリストが正しく読み込まれたか確認
            self.assertEqual(explorer._subreddits, nook.local.services.reddit_explorer.Config.load_subreddits())

    def test_stylize_post(self):
        """投稿の整形が正しく行われるかテスト"""
        # テスト用の投稿データを用意
        self.sample_post.summary = "This is a test summary."
        
        # メソッドを呼び出し
        result = self.explorer._stylize_post(self.sample_post)
        
        # 期待される結果
        expected = """
# Test Post Title

**Upvotes**: 100



[View on Reddit](https://www.reddit.com/r/test/comments/abc123/test_post_title/)

This is a test summary.
"""
        
        # 結果を検証
        self.assertEqual(result, expected)
        
    def test_store_summaries(self):
        """サマリーの保存が正しく行われるかテスト"""
        # テスト用のサマリーリスト
        summaries = ["Summary 1", "Summary 2", "Summary 3"]
        
        # メソッドを呼び出し
        self.explorer._store_summaries(summaries)
        
        # 出力先のパスを取得
        date_str = date.today().strftime("%Y-%m-%d")
        output_path = os.path.join(self.temp_dir.name, "reddit_explorer", f"{date_str}.md")
        
        # ファイルが作成されたか確認
        self.assertTrue(os.path.exists(output_path))
        
        # ファイルの内容を確認
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        expected_content = "Summary 1\n---\nSummary 2\n---\nSummary 3"
        self.assertEqual(content, expected_content)

    def test_system_instruction_format(self):
        """システム指示文の生成が正しく行われるかテスト"""
        # テスト用のデータ
        title = "Test Title"
        comments = "Test Comments"
        selftext = "Test Selftext"
        
        # メソッドを呼び出し
        result = self.explorer._system_instruction_format(title, comments, selftext)
        
        # cleanedoc関数を使用して期待される結果と実際の結果を正規化
        import inspect
        
        # 結果の正規化（余分な空白や改行を削除）
        normalized_result = inspect.cleandoc(result)
        
        # 期待される結果
        expected = inspect.cleandoc("""
        以下のテキストは、Redditのあるポストのタイトルと投稿文、そして当ポストに対する主なコメントです。
        よく読んで、ユーザーの質問に答えてください。

        タイトル
        '''
        Test Title
        '''

        投稿文
        '''
        Test Selftext
        '''

        コメント
        '''
        Test Comments
        '''
        """)
        
        # 結果を検証
        self.assertEqual(normalized_result, expected)
        
        # 投稿内容がない場合のテスト
        result_no_selftext = self.explorer._system_instruction_format(title, comments, "")
        normalized_result_no_selftext = inspect.cleandoc(result_no_selftext)
        
        # 期待される結果
        expected_no_selftext = inspect.cleandoc("""
        以下のテキストは、Redditのあるポストのタイトルと当ポストに対する主なコメントです。
        よく読んで、ユーザーの質問に答えてください。

        タイトル
        '''
        Test Title
        '''

        コメント
        '''
        Test Comments
        '''
        """)
        
        # 結果を検証
        self.assertEqual(normalized_result_no_selftext, expected_no_selftext)

    def test_call(self):
        """__call__メソッドの動作をテスト"""
        with patch('nook.local.services.reddit_explorer.RedditExplorer._retrieve_hot_posts') as mock_posts, \
             patch('nook.local.services.reddit_explorer.RedditExplorer._retrieve_top_comments_of_post') as mock_comments, \
             patch('nook.local.services.reddit_explorer.RedditExplorer._summarize_reddit_post') as mock_summarize, \
             patch('nook.local.services.reddit_explorer.RedditExplorer._store_summaries') as mock_store:
            
            # モックの設定
            mock_posts.return_value = [self.sample_post]
            mock_comments.return_value = [{"text": "Comment", "upvotes": 10}]
            mock_summarize.return_value = "Summary text"
            
            # サブレディットリストを一時的に上書き（テスト向けに1つだけにする）
            original_subreddits = self.explorer._subreddits
            self.explorer._subreddits = ["test"]
            
            try:
                # メソッドを呼び出し
                self.explorer()
                
                # 各メソッドが正しく呼び出されたか確認
                mock_posts.assert_called_once_with("test")
                mock_comments.assert_called_once_with(self.sample_post.id)
                mock_summarize.assert_called_once_with(self.sample_post)
                mock_store.assert_called_once()
            finally:
                # 元の設定に戻す
                self.explorer._subreddits = original_subreddits


if __name__ == '__main__':
    unittest.main()
