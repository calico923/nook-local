# Nook Local

テック系情報の自動収集・要約ツール「Nook」のローカル実行版です。

## 概要

Nookは、テック系の最新情報を自動的に収集し、要約するWebアプリです。Reddit、Hacker News、GitHub Trending、技術ブログ、学術論文など多様な情報源から情報を収集し、Google Gemini APIを使用して日本語で要約します。オリジナルの[Nook](https://github.com/discus0434/nook)をAWSからローカルのDockerコンテナ環境に移植したものです。

## 特徴

- **多様な情報源からの自動収集・要約**
  - Reddit: 特定のサブレディットからの人気投稿
  - Hacker News: テクノロジーニュース
  - GitHub Trending: 人気のリポジトリ
  - RSS: 技術ブログからの最新記事
  - arXiv: 最新の学術論文

- **インタラクティブなチャット機能**
  - 要約された内容について、さらに詳しく質問可能

- **シンプルなWebインターフェース**
  - 日付別に整理された情報を表示
  - レスポンシブデザインでモバイル対応
  
- **オフライン対応**
  - Gemini APIのクォータ制限に達した場合でも、ダミーレスポンスで動作継続
  - APIキーなしでもテスト・開発可能

## 必要条件

- Docker と Docker Compose
- Google Gemini API キー（オプション、なくても動作可能）
- Reddit API キー（クライアントID、クライアントシークレット）
- インターネット接続（情報収集・要約のため）

## セットアップ方法

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/nook-local.git
cd nook-local
```

### 2. 環境変数の設定

`.env`ファイルを作成し、必要なAPIキーを設定します：

```
GEMINI_API_KEY=your_gemini_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=nook-local/1.0.0
```

**注意**: Gemini APIキーが設定されていない場合や、クォータ制限に達した場合は、自動的にダミーレスポンスが生成されます。開発・テスト目的であれば、APIキーなしでも動作します。

### 3. Dockerイメージのビルドと起動

```bash
# イメージをビルド
docker compose build

# Webインターフェースとコレクターを起動（バックグラウンド実行）
docker compose up -d

# Webインターフェースのみを起動
docker compose up -d viewer

# コレクターのみを実行（フォアグラウンド）
docker compose up collector
```

## 使い方

### 情報収集の実行

情報を収集するには次のコマンドを実行します：

```bash
docker compose up collector
```

これは各情報源（Reddit、Hacker News、GitHub Trendingなど）から最新の情報を収集し、ローカルに保存します。コレクターは実行後に自動的に終了します。

### Webインターフェースへのアクセス

Webインターフェースを起動した後、ブラウザで以下のURLにアクセスします：

```
http://localhost:8080
```

### 日次実行の設定（オプション）

cronを使って毎日自動的に情報収集を行うよう設定できます：

```bash
# crontabを編集
crontab -e

# 毎朝6時に実行する例
0 6 * * * cd /path/to/nook-local && docker compose up collector > /tmp/nook-collector.log 2>&1
```

## プロジェクト構造

```
nook-local/
├── docker-compose.yml     # Dockerコンテナ設定
├── Dockerfile             # Dockerイメージ定義
├── requirements.txt       # Python依存関係
├── data/                  # 収集したデータの保存ディレクトリ
└── nook/                  # アプリケーションコード
    └── local/
        ├── collector.py   # 情報収集の統合スクリプト
        ├── viewer.py      # Webインターフェース
        ├── common/        # 共通ユーティリティ
        │   ├── gemini_client.py  # Gemini APIクライアント
        │   └── ...
        ├── services/      # 各情報源のコレクター
        │   ├── reddit_explorer.py
        │   ├── hacker_news.py
        │   ├── github_trending.py
        │   ├── tech_feed.py
        │   └── paper_summarizer.py
        └── static/        # CSSとJavaScript
```

## カスタマイズ

### 情報源の変更

各サービスのソースコードを編集することで、収集する情報源を変更できます：

- Reddit: `nook/local/services/reddit_explorer.py`の`Config.load_subreddits`メソッド
- GitHub Trending: `nook/local/services/github_trending.py`の`_languages`リスト
- RSS: `nook/local/services/tech_feed.py`の`_feeds`リスト
- arXiv: `nook/local/services/paper_summarizer.py`の`_search_queries`リスト

### UIカスタマイズ

Webインターフェースは`nook/local/static/`ディレクトリ内のCSSとJavaScriptファイルを編集することでカスタマイズ可能です。

### Gemini APIの設定

`nook/local/common/gemini_client.py`を編集することで、Gemini APIの動作をカスタマイズできます：

- モデル名の変更: `model_name`変数を編集
- ダミーレスポンスの調整: `DummyClient`クラス内の`general_responses`と`topic_responses`を編集

## トラブルシューティング

### 一般的な問題

**問題**: コンテナが起動しない  
**解決策**: ログを確認し、必要な環境変数が設定されているか確認してください
```bash
docker compose logs
```

**問題**: APIエラーが発生する  
**解決策**: APIキーの有効性と、レート制限に達していないことを確認してください。Gemini APIのクォータ制限に達した場合は、自動的にダミーレスポンスが生成されます。

**問題**: データが表示されない  
**解決策**: コレクターが正常に実行されたか確認し、`data`ディレクトリ内にファイルが生成されているか確認してください。

### Gemini APIのクォータ制限

Gemini APIのクォータ制限に達した場合（429エラー）、自動的にダミーレスポンスが生成されます。これにより、APIキーがなくても、または制限に達しても、アプリケーションは継続して動作します。

ダミーレスポンスはコンテキストに応じて生成され、以下のカテゴリに対応しています：
- Reddit/Python/プログラミング関連
- GitHub/リポジトリ/トレンド関連
- 論文/研究/arXiv関連
- ニュース/Hacker News/テック関連

## 最近の更新

- Gemini APIのクォータ制限に対応するフォールバックメカニズムを実装
- コンテキストに応じたダミーレスポンス生成機能を追加
- Docker Compose設定の改善
- 日本語UIの強化

## ライセンス

このプロジェクトはオリジナルのNookと同様に、GNU Affero General Public License v3.0の下で提供されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 謝辞

- [オリジナルのNookプロジェクト](https://github.com/discus0434/nook)の作者に感謝します
- このプロジェクトで使用しているオープンソースライブラリの作者たちに感謝します
