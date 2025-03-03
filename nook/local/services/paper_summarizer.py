import os
import datetime
import time
import inspect
import pytz
from pathlib import Path

import arxiv
import requests
from bs4 import BeautifulSoup

from nook.local.common.gemini_client import create_client

class PaperSummarizer:
    """最新の学術論文を収集・要約するサービス"""
    
    def __init__(self):
        self._data_dir = os.environ.get("DATA_DIR", "./data")
        self._client = create_client()
        self._max_papers = 5
        
        # 検索クエリ設定
        self._search_queries = [
            {
                "query": "cat:cs.AI AND cat:cs.LG",
                "name": "AI and Machine Learning",
                "max_results": self._max_papers
            },
            {
                "query": "cat:cs.CL",
                "name": "Computational Linguistics and NLP",
                "max_results": self._max_papers
            }
        ]
    
    def __call__(self):
        """arXivから最新の論文を収集・要約"""
        print("Collecting and summarizing research papers...")
        
        all_paper_markdowns = []
        
        for search_config in self._search_queries:
            query = search_config["query"]
            name = search_config["name"]
            max_results = search_config["max_results"]
            
            print(f"Searching arXiv for: {name} ({query})")
            
            papers = self._search_arxiv(query, max_results)
            
            for paper in papers:
                print(f"Processing paper: {paper.title}")
                
                paper_markdown = self._process_paper(paper, name)
                if paper_markdown:
                    all_paper_markdowns.append(paper_markdown)
                
                # API呼び出しの間隔を空ける
                time.sleep(1)
        
        # 保存
        self._save_papers_as_markdown(all_paper_markdowns)
        
        print(f"Collected and summarized {len(all_paper_markdowns)} papers")
    
    def _search_arxiv(self, query, max_results):
        """arXivで論文を検索"""
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        return list(client.results(search))
    
    def _process_paper(self, paper, category):
        """論文を処理して要約を含むMarkdownを生成"""
        try:
            title = paper.title
            authors = ", ".join([author.name for author in paper.authors])
            published = paper.published.strftime("%Y-%m-%d")
            summary = paper.summary
            arxiv_url = paper.entry_id
            pdf_url = paper.pdf_url
            
            # 追加情報を取得（可能であれば）
            additional_content = self._get_paper_additional_content(paper)
            
            # 要約を生成
            ai_summary = self._summarize_paper(title, authors, summary, additional_content)
            
            # Markdown形式で論文を整形
            markdown = f"## {title}\n\n"
            markdown += f"**Authors**: {authors}  \n"
            markdown += f"**Published**: {published}  \n"
            markdown += f"**Category**: {category}  \n"
            markdown += f"**arXiv**: [{arxiv_url}]({arxiv_url})  \n"
            markdown += f"**PDF**: [{pdf_url}]({pdf_url})  \n\n"
            markdown += f"### 要約\n\n{ai_summary}\n\n"
            markdown += "---\n\n"
            
            return markdown
            
        except Exception as e:
            print(f"Error processing paper {paper.title}: {e}")
            return None
    
    def _get_paper_additional_content(self, paper):
        """論文の追加情報を取得（HTMLページなど）"""
        try:
            # arXivのHTMLページから追加情報を取得
            response = requests.get(paper.entry_id, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            if response.status_code != 200:
                return ""
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 論文の要約部分を取得
            abstract_div = soup.select_one('.abstract')
            if abstract_div:
                return abstract_div.get_text(separator=' ', strip=True)
            
            return ""
            
        except Exception as e:
            print(f"Error fetching additional content for {paper.title}: {e}")
            return ""
    
    def _summarize_paper(self, title, authors, abstract, additional_content):
        """論文を要約"""
        system_prompt = inspect.cleandoc(
            """
            あなたは学術論文の要約を行うAIアシスタントです。
            以下の論文のアブストラクトと追加情報を読んで、以下の情報をまとめてください：

            1. 研究の背景と目的
            2. 提案されている手法や方法論
            3. 主な成果や結果
            4. 実用的な意義や今後の可能性

            要約は日本語で、技術的に正確で、分かりやすくまとめてください。
            """
        )
        
        content_prompt = inspect.cleandoc(
            f"""
            論文タイトル: {title}
            著者: {authors}
            
            アブストラクト:
            {abstract}
            
            追加情報:
            {additional_content}
            
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
            print(f"Error summarizing paper {title}: {e}")
            return "要約を生成できませんでした。"
    
    def _save_papers_as_markdown(self, paper_markdowns):
        """論文のMarkdownをファイルに保存"""
        if not paper_markdowns:
            print("No papers to save")
            return
        
        # 日本時間で現在の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        date = datetime.datetime.now(jst).date()
        date_str = date.strftime("%Y-%m-%d")
        
        output_dir = os.path.join(self._data_dir, "paper_summarizer")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{date_str}.md")
        
        content = "# Latest Research Papers\n\n"
        content += "\n".join(paper_markdowns)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Saved paper summaries to {output_path}")

if __name__ == "__main__":
    # ローカルでテスト実行
    summarizer = PaperSummarizer()
    summarizer()