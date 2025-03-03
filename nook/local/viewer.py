import os
import sys
import datetime
import json
import re
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

import uvicorn
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bs4 import BeautifulSoup

# gemini_clientを適切なパスからインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nook.local.common.gemini_client import create_client

app = FastAPI()

# データディレクトリの設定
data_dir = os.environ.get("DATA_DIR", "./data")
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# テンプレートディレクトリの設定
templates = Jinja2Templates(directory=templates_dir)

# staticディレクトリが存在しない場合は作成
static_dir = os.path.join(templates_dir, "static")
os.makedirs(static_dir, exist_ok=True)

# 静的ファイルの提供
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 対象のアプリ名リスト
app_names = [
    "github_trending",
    "hacker_news",
    "paper_summarizer",
    "reddit_explorer",
    "tech_feed",
]

# 天気アイコンの対応表（元のコードから）
WEATHER_ICONS = {
    "100": "☀️",  # 晴れ
    "101": "🌤️",  # 晴れ時々くもり
    "200": "☁️",  # くもり
    "201": "⛅",  # くもり時々晴れ
    "202": "🌧️",  # くもり一時雨
    "300": "🌧️",  # 雨
    "301": "🌦️",  # 雨時々晴れ
    "400": "🌨️",  # 雪
}

def get_weather_data():
    """
    気象庁のAPIから東京の天気データを取得する
    """
    try:
        response = requests.get(
            "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json", timeout=5
        )
        response.raise_for_status()
        data = response.json()

        # 東京地方のデータを取得
        tokyo = next(
            (
                area
                for area in data[0]["timeSeries"][2]["areas"]
                if area["area"]["name"] == "東京"
            ),
            None,
        )
        tokyo_weather = next(
            (
                area
                for area in data[0]["timeSeries"][0]["areas"]
                if area["area"]["code"] == "130010"
            ),
            None,
        )

        if tokyo and tokyo_weather:
            # 現在の気温（temps[0]が最低気温、temps[1]が最高気温）
            temps = tokyo["temps"]
            weather_code = tokyo_weather["weatherCodes"][0]
            weather_icon = WEATHER_ICONS.get(weather_code, "")

            return {
                "temp": temps[0],
                "weather_code": weather_code,
                "weather_icon": weather_icon,
            }
    except Exception as e:
        print(f"Error fetching weather data: {e}")

    # エラー時やデータが取得できない場合はデフォルト値を返す
    return {
        "temp": "--",
        "weather_code": "100",  # デフォルトは晴れ
        "weather_icon": WEATHER_ICONS.get("100", "☀️"),
    }

def extract_links(text: str) -> list[str]:
    """Markdownテキストからリンクを抽出する"""
    # Markdown形式のリンク [text](url) を抽出
    markdown_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
    # もし[text]の部分が[Image]または[Video]の場合は、その部分を除外
    markdown_links = [
        (text, url)
        for text, url in markdown_links
        if not text.startswith("[Image]") and not text.startswith("[Video]")
    ]
    # 通常のURLも抽出
    urls = re.findall(r"(?<![\(\[])(https?://[^\s\)]+)", text)

    return [url for _, url in markdown_links] + urls

def fetch_url_content(url: str) -> str | None:
    """URLの内容を取得してテキストに変換する"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # スクリプト、スタイル、ナビゲーション要素を削除
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()

        # メインコンテンツを抽出（article, main, または本文要素）
        main_content = soup.find("article") or soup.find("main") or soup.find("body")
        if main_content:
            # テキストを抽出し、余分な空白を削除
            text = " ".join(main_content.get_text(separator=" ").split())
            # 長すぎる場合は最初の1000文字に制限
            return text[:1000] + "..." if len(text) > 1000 else text

        return None
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def fetch_markdown(app_name: str, date_str: str) -> str:
    """
    指定されたアプリ名と日付のローカルファイルシステム上のMarkdownファイルを取得
    """
    file_path = os.path.join(data_dir, f"{app_name}/{date_str}.md")
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return f"No data available for {app_name} on {date_str}"
    except Exception as e:
        return f"Error reading {file_path}: {e}"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, date: str = None):
    if date is None:
        date = datetime.date.today().strftime("%Y-%m-%d")
    
    # 利用可能な日付のリストを取得
    available_dates = []
    for app_name in app_names:
        app_dir = os.path.join(data_dir, app_name)
        if os.path.exists(app_dir):
            for file_name in os.listdir(app_dir):
                if file_name.endswith(".md"):
                    date_str = file_name.replace(".md", "")
                    if date_str not in available_dates:
                        available_dates.append(date_str)
    
    available_dates.sort(reverse=True)
    
    # コンテンツを取得
    contents = {name: fetch_markdown(name, date) for name in app_names}
    
    # 天気データを取得
    weather_data = get_weather_data()

    # 天気データを新しいフォーマットに変換
    weather = {
        "temperature": weather_data["temp"],
        "icon": "sunny"  # デフォルト値
    }
    
    # 天気コードに基づいてアイコンを設定
    weather_code = weather_data.get("weather_code", "100")
    if weather_code.startswith("1"):  # 晴れ系
        weather["icon"] = "sunny"
    elif weather_code.startswith("2"):  # くもり系
        weather["icon"] = "cloudy"
    elif weather_code.startswith("3"):  # 雨系
        weather["icon"] = "rainy"
    elif weather_code.startswith("4"):  # 雪系
        weather["icon"] = "snowy"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "contents": contents,
            "selected_date": date,
            "app_names": app_names,
            "weather": weather,
            "available_dates": available_dates,
        },
    )

@app.get("/fetch_markdown", response_class=JSONResponse)
async def get_markdown(app_name: str, date: str):
    """
    指定されたアプリ名と日付のMarkdownコンテンツを取得するAPIエンドポイント
    """
    content = fetch_markdown(app_name, date)
    return {"content": content}

@app.get("/api/weather", response_class=JSONResponse)
async def get_weather():
    """天気データを取得するAPIエンドポイント"""
    return get_weather_data()

_MESSAGE = """
以下の記事に関連して、検索エンジンを用いて事実を確認しながら、ユーザーからの質問に対してできるだけ詳細に答えてください。
なお、回答はMarkdown形式で記述してください。

[記事]

{markdown}

{additional_context}

[チャット履歴]

'''
{chat_history}
'''

[ユーザーからの新しい質問]

'''
{message}
'''

それでは、回答をお願いします。
"""

@app.post("/chat/{topic_id}")
async def chat(topic_id: str, request: Request):
    data = await request.json()
    message = data.get("message")
    markdown = data.get("markdown")
    chat_history = data.get("chat_history", "なし")  # チャット履歴を受け取る

    # markdownとメッセージからリンクを抽出
    links = extract_links(markdown) + extract_links(message)

    # リンクの内容を取得
    additional_context = []
    for url in links:
        if content := fetch_url_content(url):
            additional_context.append(f"- Content from {url}:\n\n'''{content}'''\n\n")

    # 追加コンテキストがある場合、markdownに追加
    if additional_context:
        additional_context = (
            "\n\n[記事またはユーザーからの質問に含まれるリンクの内容](うまく取得できていない可能性があります)\n\n"
            + "\n\n".join(additional_context)
        )
    else:
        additional_context = ""

    formatted_message = _MESSAGE.format(
        markdown=markdown,
        additional_context=additional_context,
        chat_history=chat_history,
        message=message,
    )

    gemini_client = create_client(use_search=True)
    response_text = gemini_client.chat_with_search(formatted_message)

    return {"response": response_text}

if __name__ == "__main__":
    # データディレクトリのサブディレクトリを作成
    for app_name in app_names:
        os.makedirs(os.path.join(data_dir, app_name), exist_ok=True)
    
    print(f"Starting Nook viewer at http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)