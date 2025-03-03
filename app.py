#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# 必要な環境変数が設定されているか確認
required_vars = [
    "GEMINI_API_KEY",
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USER_AGENT",
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these variables in your .env file or environment.")
    sys.exit(1)

if __name__ == "__main__":
    print("nook-local application")
    print("Use docker-compose to run the components:")
    print("  - docker-compose up viewer      # Start the web interface")
    print("  - docker-compose up collector   # Run data collection")
    print("")
    print("For more information, see README.md")