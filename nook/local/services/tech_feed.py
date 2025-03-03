import os
import datetime
import time
from pathlib import Path
import inspect

import feedparser
import requests
from bs4 import BeautifulSoup

from nook.local.common.gemini_client import create_client

class TechFeedCollector:
    """テクノロジー関連のRSSフィードを収集・要約するコレクター"""
    
    def __init__(self):
        self._data_dir = os.environ.get("DATA_DIR", "./data")
        self._client = create_client()
        self._feed_entries_limit = 5
        
        # デフォルトのフィード設定
        self._feeds = [
            {
                "key": "google_ai_blog",
                "name": "Google AI Blog",
                "url": "http://googleaiblog.blogspot.com/atom.xml"
            },
            {
                "key": "openai_blog",
                "name": "OpenAI Blog",
                "url": "https://openai.com/blog/rss.xml"
            },
            {
                "key": "huggingface_blog",
                "name": "Hugging Face Blog",
                "url": "https://huggingface.co/blog/feed.xml"
            },
            {
                "key": "pytorch_blog",
                "name": "PyTorch Blog",
                "url": "https://pytorch.org/feed.xml"
            }
        ]
    
    def __call__(self):
        """RSSフィードから最新の記事を収集・要約して保存"""
        print("Collecting tech feed articles...")
        
        all_article_markdowns = []
        
        for feed_info in self._feeds:
            feed_name = feed_info["name"]
            feed_url = feed_info["url"]
            
            print(f"Fetching feed: {feed_name} from {feed_url}")
            try:
                # フィードを解析
                feed = feedparser.parse(feed_url)
                
                # 最新の記事を取得
                for i, entry in enumerate(feed.entries[:self._feed_entries_limit]):
                    if i >= self._feed_entries_limit:
                        break
                    
                    print(f"Processing article: {entry.title}")
                    
                    # 記事の内容を取得・要約
                    article_markdown = self._process_article(feed_name, entry)
                    if article_markdown:
                        all_article_markdowns.append(article_markdown)
                    
                    # API呼び出しの間隔を空ける
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error processing feed {feed_name}: {e}")
        
        # Markdownで保存
        self._save_articles_as_markdown(all_article_markdowns)
        
        print(f"Collected and summarized {len(all_article_markdowns)} tech feed articles")
    
    def _process_article(self, feed_name, entry):
        """記事を処理して要約を含むMarkdownを生成"""
        try:
            title = entry.title
            url = entry.link
            published = entry.get('published', '')
            
            # 公開日を整形
            try:
                published_date = datetime.datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                published_str = published_date.strftime('%Y-%m-%d')
            except:
                published_str = published
            
            # 記事の内容を取得
            content = self._extract_article_content(entry, url)
            
            # 内容を要約
            summary = self._summarize_article(title, content, url)
            
            # Markdown形式で記事を整形
            markdown = f"## {title}\n\n"
            markdown += f"**Source**: {feed_name}  \n"
            markdown += f"**Published**: {published_str}  \n"
            markdown += f"**URL**: [{url}]({url})  \n\n"
            markdown += f"{summary}\n\n"
            markdown += "---\n\n"
            
            return markdown
            
        except Exception as e:
            print(f"Error processing article {entry.get('title', 'Unknown')}: {e}")
            return None
    
    def _extract_article_content(self, entry, url):
        """記事の本文を抽出"""
        # エントリーに内容がある場合はそれを使用
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
            soup = BeautifulSoup(content, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        
        # 要約がある場合はそれを使用
        if hasattr(entry, 'summary') and entry.summary:
            soup = BeautifulSoup(entry.summary, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        
        # Webページから内容を取得
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ページから本文を抽出 (一般的なパターン)
            article = soup.find('article') or soup.find(class_='post-content') or soup.find(class_='entry-content')
            
            if article:
                # スクリプトと広告を削除
                for tag in article.find_all(['script', 'style', 'iframe', 'noscript']):
                    tag.decompose()
                
                return article.get_text(separator=' ', strip=True)
            
            # 見つからない場合は本文から抽出を試みる
            body = soup.find('body')
            if body:
                # 不要な要素を削除
                for tag in body.find_all(['script', 'style', 'iframe', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                text = body.get_text(separator=' ', strip=True)
                # 長すぎる場合は最初の部分だけ返す
                return text[:5000] + '...' if len(text) > 5000 else text
            
            return "記事の内容を取得できませんでした。"
            
        except Exception as e:
            print(f"Error fetching article content from {url}: {e}")
            return "記事の内容を取得できませんでした。"
    
    def _summarize_article(self, title, content, url):
        """記事を要約"""
        system_prompt = inspect.cleandoc(
            """
            あなたはテクノロジー・プログラミング・AI記事の要約を担当するAIアシスタントです。
            与えられた記事を簡潔に要約し、重要なポイントをまとめてください。
            回答は日本語で行い、見出しなどは使わず、段落で構成してください。
            最大3段落程度にまとめ、技術的な内容はそのまま伝えてください。
            """
        )
        
        content_prompt = inspect.cleandoc(
            f"""
            以下の記事を要約してください。

            タイトル: {title}
            URL: {url}

            内容:
            {content[:5000]}  # 長すぎる場合は切り詰める
            
            要約:
            """
        )
        
        try:
            summary = self._client.generate_content(
                contents=content_prompt,
                system_instruction=system_prompt
            )
            
            return summary
        except Exception as e:
            print(f"Error summarizing article {title}: {e}")
            return "要約を生成できませんでした。"
    
    def _save_articles_as_markdown(self, article_markdowns):
        """記事のMarkdownをファイルに保存"""
        if not article_markdowns:
            print("No articles to save")
            return
        
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        output_dir = os.path.join(self._data_dir, "tech_feed")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{date_str}.md")
        
        content = "# Technology Blog Updates\n\n"
        content += "\n".join(article_markdowns)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Saved tech feed articles to {output_path}")

if __name__ == "__main__":
    # ローカルでテスト実行
    collector = TechFeedCollector()
    collector()