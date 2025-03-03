import os
import sys
import importlib
import datetime
import json
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# 元のモジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# データディレクトリの作成
data_dir = os.environ.get("DATA_DIR", "./data")
os.makedirs(data_dir, exist_ok=True)

# 各サービスのローカル版コレクター
from nook.local.services.reddit_explorer import RedditExplorer
from nook.local.services.hacker_news import HackerNewsCollector
from nook.local.services.github_trending import GitHubTrendingCollector
from nook.local.services.tech_feed import TechFeedCollector
from nook.local.services.paper_summarizer import PaperSummarizer

def run_collector():
    """全てのコレクターを実行"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    print(f"Running collectors for {today}")
    
    collectors = [
        ("Reddit Explorer", RedditExplorer()),
        ("Hacker News", HackerNewsCollector()),
        ("GitHub Trending", GitHubTrendingCollector()),
        ("Tech Feed", TechFeedCollector()),
        ("Paper Summarizer", PaperSummarizer())
    ]
    
    for name, collector in collectors:
        try:
            print(f"Running {name}...")
            collector()
            print(f"{name} completed")
        except Exception as e:
            print(f"Error in {name}: {e}")
    
    print("All collectors completed")

if __name__ == "__main__":
    run_collector()