import os
import inspect
import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
import sys

import praw
import toml

from nook.local.common.gemini_client import create_client

_MARKDOWN_FORMAT = """
## {title}

**Upvotes**: {upvotes}

{image_or_video_or_none}

[View on Reddit]({permalink})

{summary}
"""

# 設定
class Config:
    reddit_top_posts_limit = 10
    reddit_top_comments_limit = 3
    
    @classmethod
    def load_subreddits(cls) -> list[str]:
        """デフォルトのサブレディット設定"""
        return ["MachineLearning", "Python", "programming", "artificial"]

@dataclass
class RedditPost:
    type: Literal["image", "gallery", "video", "poll", "crosspost", "text", "link"]
    id: str
    title: str
    url: str | None
    upvotes: int
    text: str
    permalink: str = ""
    comments: list[dict[str, str | int]] = field(default_factory=list)
    summary: str = ""
    thumbnail: str = "self"


class RedditExplorer:
    def __init__(self):
        self._reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT"),
        )
        self._client = create_client()
        self._data_dir = os.environ.get("DATA_DIR", "./data")
        self._subreddits = Config.load_subreddits()

    def __call__(self) -> None:
        markdowns = []
        for subreddit in self._subreddits:
            print(f"Fetching posts from r/{subreddit}...")
            posts = self._retrieve_hot_posts(subreddit)
            for post in posts:
                print(f"Processing post: {post.title[:30]}...")
                post.comments = self._retrieve_top_comments_of_post(post.id)
                post.summary = self._summarize_reddit_post(post)
                markdowns.append(self._stylize_post(post))

        self._store_summaries(markdowns)
        print("Reddit explorer completed")

    def _store_summaries(self, summaries: list[str]) -> None:
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        
        # 環境変数から保存先ディレクトリを取得
        output_dir = os.path.join(self._data_dir, "reddit_explorer")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{date_str}.md")
        content = "\n---\n".join(summaries)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Stored Reddit summaries to {output_path}")

    def _retrieve_hot_posts(
        self, subreddit: str, limit: int = None
    ) -> list[RedditPost]:
        if limit is None:
            limit = Config.reddit_top_posts_limit

        posts = []
        for post in self._reddit.subreddit(subreddit).hot(limit=limit * 2):  # 取得数を多めに
            post_type = self.__judge_post_type(post)

            url = self._get_video_url(post) if post_type == "video" else post.url

            # 不要な投稿はスキップ
            if hasattr(post, 'author') and post.author and post.author.name == "AutoModerator":
                continue
            if "megathread" in post.title.lower():
                continue
            if post.upvote_ratio < 0.7:
                continue
            if ["gallery", "poll", "crosspost"].__contains__(post_type):
                continue
                
            posts.append(
                RedditPost(
                    type=post_type,
                    id=post.id,
                    title=post.title,
                    url=url,
                    upvotes=post.ups,
                    text=post.selftext,
                    thumbnail=post.thumbnail,
                )
            )
            posts[-1].permalink = f"https://www.reddit.com{post.permalink}"
            
            # 指定数まで収集したら終了
            if len(posts) >= limit:
                break
                
        return posts

    def _retrieve_top_comments_of_post(
        self,
        post_id: str,
        limit: int = None,
    ) -> list[dict[str, str | int]]:
        if limit is None:
            limit = Config.reddit_top_comments_limit

        submission = self._reddit.submission(id=post_id)
        submission.comments.replace_more(limit=0)
        return [
            {
                "text": comment.body,
                "upvotes": comment.ups,
            }
            for comment in submission.comments.list()[:limit]
        ]

    def _summarize_reddit_post(self, post: RedditPost) -> str:
        comments_text = "\n".join(
            [
                f"{comment['upvotes']} upvotes: {comment['text']}"
                for comment in post.comments
            ]
        )

        return self._client.generate_content(
            contents=self._contents,
            system_instruction=self._system_instruction_format(
                title=post.title,
                comments=comments_text,
                selftext=post.text,
            ),
        )

    def __judge_post_type(
        self, post: praw.models.Submission
    ) -> Literal["image", "gallery", "video", "poll", "crosspost", "text", "link"]:
        if getattr(post, "post_hint", "") == "image":
            return "image"
        elif getattr(post, "is_gallery", False):
            return "gallery"
        elif getattr(post, "is_video", False):
            return "video"
        elif hasattr(post, "poll_data"):
            return "poll"
        elif hasattr(post, "crosspost_parent"):
            return "crosspost"
        elif post.is_self:
            return "text"
        return "link"

    def _get_video_url(self, post: praw.models.Submission) -> str | None:
        if hasattr(post, "media"):
            return post.media.get("reddit_video", {}).get("fallback_url", None)
        elif hasattr(post, "secure_media"):
            return post.secure_media.get("reddit_video", {}).get("fallback_url", None)
        else:
            return None

    def _stylize_post(self, post: RedditPost) -> str:
        return _MARKDOWN_FORMAT.format(
            title=post.title,
            upvotes=post.upvotes,
            image_or_video_or_none=(
                f"![Image]({post.url})"
                if post.type == "image"
                else f'<video src="{post.url}" controls controls style="width: 100%; height: auto; max-height: 500px;"></video>'
                if post.type == "video" and post.url is not None
                else ""
            ),
            permalink=post.permalink,
            summary=post.summary,
        )

    def _system_instruction_format(
        self, title: str, comments: str, selftext: str
    ) -> str:
        self_text = ""
        if selftext:
            self_text = inspect.cleandoc(
                f"""
                投稿文
                '''
                {selftext}
                '''
                """
            ) + "\n\n"
            
        return inspect.cleandoc(
            f"""
            以下のテキストは、Redditのあるポストのタイトルと{"投稿文、そして" if selftext else ""}当ポストに対する主なコメントです。
よく読んで、ユーザーの質問に答えてください。

タイトル
'''
{title}
'''

{self_text}コメント
'''
{comments}
'''"""
        )

    @property
    def _contents(self) -> str:
        return inspect.cleandoc(
            """
            以下の2つの質問について、順を追って詳細に、分かりやすく答えてください。

            1. このポストの内容を説明してください。
            2. このポストに対するコメントのうち、特に興味深いものを教えてください。

            この質問の回答以外の出力は不要です。
            """
        )


if __name__ == "__main__":
    # ローカルでのテスト用
    explorer = RedditExplorer()
    explorer()