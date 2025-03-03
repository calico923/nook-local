import os
import datetime
import json
import time
import pytz
from pathlib import Path

import requests

class HackerNewsCollector:
    """Hacker Newsの記事を収集するコレクター"""
    
    def __init__(self):
        self._data_dir = os.environ.get("DATA_DIR", "./data")
        self._api_base_url = "https://hacker-news.firebaseio.com/v0"
        self._article_limit = 20
        
    def __call__(self):
        """Hacker Newsから最新の記事を収集して保存"""
        print("Collecting Hacker News articles...")
        
        # トップ記事のIDを取得
        top_stories = self._get_top_stories()
        
        # 各記事の詳細を取得
        articles = []
        for story_id in top_stories[:self._article_limit]:
            article = self._get_article_details(story_id)
            if article:
                articles.append(article)
                # APIレート制限を避けるための短い遅延
                time.sleep(0.1)
        
        # Markdownで保存
        self._save_articles_as_markdown(articles)
        
        print(f"Collected {len(articles)} Hacker News articles")
    
    def _get_top_stories(self):
        """トップ記事のIDリストを取得"""
        response = requests.get(f"{self._api_base_url}/topstories.json")
        response.raise_for_status()
        return response.json()
    
    def _get_article_details(self, article_id):
        """記事の詳細情報を取得"""
        try:
            response = requests.get(f"{self._api_base_url}/item/{article_id}.json")
            response.raise_for_status()
            article = response.json()
            
            # 'story'タイプの記事のみを処理
            if article.get('type') != 'story':
                return None
            
            # URLがない記事（Ask HNなど）はHacker News自体のURLを使用
            if 'url' not in article:
                article['url'] = f"https://news.ycombinator.com/item?id={article_id}"
            
            return article
        except Exception as e:
            print(f"Error fetching article {article_id}: {e}")
            return None
    
    def _save_articles_as_markdown(self, articles):
        """記事をMarkdownフォーマットで保存"""
        # 日本時間で現在の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        date = datetime.datetime.now(jst).date()
        date_str = date.strftime("%Y-%m-%d")
        
        output_dir = os.path.join(self._data_dir, "hacker_news")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{date_str}.md")
        
        # Markdown形式で記事を整形
        markdown_content = "# Hacker News Top Stories\n\n"
        
        for article in articles:
            title = article.get('title', 'No Title')
            url = article.get('url', '')
            score = article.get('score', 0)
            author = article.get('by', 'anonymous')
            comments = article.get('descendants', 0)
            article_id = article.get('id', '')
            
            markdown_content += f"## {title}\n\n"
            markdown_content += f"**Score**: {score} | "
            markdown_content += f"**Comments**: {comments} | "
            markdown_content += f"**Author**: {author}\n\n"
            
            markdown_content += f"[Read Article]({url}) | "
            markdown_content += f"[Discussion](https://news.ycombinator.com/item?id={article_id})\n\n"
            
            markdown_content += "---\n\n"
        
        # ファイルに保存
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"Saved Hacker News articles to {output_path}")

if __name__ == "__main__":
    # ローカルでテスト実行
    collector = HackerNewsCollector()
    collector()