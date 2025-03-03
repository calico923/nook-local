import os
import datetime
import json
import time
import pytz
from pathlib import Path

import requests
from bs4 import BeautifulSoup

class GitHubTrendingCollector:
    """GitHub Trendingのリポジトリを収集するコレクター"""
    
    def __init__(self):
        self._data_dir = os.environ.get("DATA_DIR", "./data")
        self._languages = ["python", "javascript", "typescript", "go", "rust", "cpp", "java"]
        self._trending_url = "https://github.com/trending/{language}?since=daily"
    
    def __call__(self):
        """GitHub Trendingからトレンドリポジトリを収集して保存"""
        print("Collecting GitHub Trending repositories...")
        
        all_repos = []
        
        for language in self._languages:
            print(f"Fetching trending repos for {language}...")
            repos = self._get_trending_repos(language)
            all_repos.extend(repos)
            # GitHubのレート制限を避けるための遅延
            time.sleep(1)
        
        # Markdownで保存
        self._save_repos_as_markdown(all_repos)
        
        print(f"Collected {len(all_repos)} GitHub Trending repositories")
    
    def _get_trending_repos(self, language):
        """指定された言語のGitHub Trendingリポジトリを取得"""
        url = self._trending_url.format(language=language)
        
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            repo_list = []
            
            # リポジトリ情報を抽出
            repo_items = soup.select('article.Box-row')
            
            for item in repo_items[:10]:  # 上位10リポジトリを取得
                repo = {}
                
                # リポジトリ名とURL
                repo_link = item.select_one('h2 a')
                if repo_link:
                    repo_path = repo_link.get('href', '').strip('/')
                    repo['name'] = repo_path
                    repo['url'] = f"https://github.com/{repo_path}"
                
                # 説明
                description = item.select_one('p')
                repo['description'] = description.text.strip() if description else ""
                
                # スター数
                stars_element = item.select_one('a.Link--muted:nth-of-type(1)')
                repo['stars'] = stars_element.text.strip().replace(',', '') if stars_element else "0"
                
                # 言語
                language_element = item.select_one('span[itemprop="programmingLanguage"]')
                repo['language'] = language_element.text.strip() if language_element else language
                
                # フォーク数
                forks_element = item.select_one('a.Link--muted:nth-of-type(2)')
                repo['forks'] = forks_element.text.strip().replace(',', '') if forks_element else "0"
                
                repo_list.append(repo)
            
            return repo_list
        
        except Exception as e:
            print(f"Error fetching trending repositories for {language}: {e}")
            return []
    
    def _save_repos_as_markdown(self, repos):
        """リポジトリをMarkdownフォーマットで保存"""
        # 日本時間で現在の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        date = datetime.datetime.now(jst).date()
        date_str = date.strftime("%Y-%m-%d")
        
        output_dir = os.path.join(self._data_dir, "github_trending")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{date_str}.md")
        
        # 言語ごとにグループ化
        repos_by_language = {}
        for repo in repos:
            language = repo['language']
            if language not in repos_by_language:
                repos_by_language[language] = []
            repos_by_language[language].append(repo)
        
        # Markdown形式でリポジトリを整形
        markdown_content = "# GitHub Trending Repositories\n\n"
        
        for language, language_repos in repos_by_language.items():
            markdown_content += f"## {language.capitalize()}\n\n"
            
            for repo in language_repos:
                name = repo.get('name', 'No Name')
                url = repo.get('url', '')
                description = repo.get('description', 'No description')
                stars = repo.get('stars', '0')
                forks = repo.get('forks', '0')
                
                markdown_content += f"### [{name}]({url})\n\n"
                markdown_content += f"{description}\n\n"
                markdown_content += f"⭐ Stars: {stars} | 🍴 Forks: {forks}\n\n"
                markdown_content += "---\n\n"
        
        # ファイルに保存
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"Saved GitHub Trending repositories to {output_path}")

if __name__ == "__main__":
    # ローカルでテスト実行
    collector = GitHubTrendingCollector()
    collector()