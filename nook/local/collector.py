import os
import sys
import importlib
import datetime
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# 元のモジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# データディレクトリの作成
data_dir = os.environ.get("DATA_DIR", "./data")
os.makedirs(data_dir, exist_ok=True)

# ログディレクトリの作成
logs_dir = "./logs"
os.makedirs(logs_dir, exist_ok=True)

# ロガーの設定
def setup_logger():
    today = datetime.date.today().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"collector_{today}.log")
    
    # ロガーの設定
    logger = logging.getLogger("collector")
    logger.setLevel(logging.INFO)
    
    # ファイルハンドラーの設定
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # フォーマッターの設定
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # ハンドラーをロガーに追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 各サービスのローカル版コレクター
from nook.local.services.reddit_explorer import RedditExplorer
from nook.local.services.hacker_news import HackerNewsCollector
from nook.local.services.github_trending import GitHubTrendingCollector
from nook.local.services.tech_feed import TechFeedCollector
from nook.local.services.paper_summarizer import PaperSummarizer

def run_collector():
    """全てのコレクターを実行"""
    # ロガーのセットアップ
    logger = setup_logger()
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    logger.info(f"Running collectors for {today}")
    
    collectors = [
        ("Reddit Explorer", RedditExplorer()),
        ("Hacker News", HackerNewsCollector()),
        ("GitHub Trending", GitHubTrendingCollector()),
        ("Tech Feed", TechFeedCollector()),
        ("Paper Summarizer", PaperSummarizer())
    ]
    
    for name, collector in collectors:
        try:
            logger.info(f"Running {name}...")
            collector()
            logger.info(f"{name} completed")
        except Exception as e:
            logger.error(f"Error in {name}: {e}", exc_info=True)
    
    logger.info("All collectors completed")

if __name__ == "__main__":
    run_collector()