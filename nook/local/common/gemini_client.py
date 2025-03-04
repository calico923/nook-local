import os
import google.generativeai as genai
import random
import re

def create_client(use_search=False):
    """Gemini APIクライアントを作成する"""
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-pro-exp-02-05")
    
    class DummyClient:
        """APIキーが設定されていない場合のダミークライアント"""
        def __init__(self):
            # 一般的なダミーレスポンス
            self.general_responses = [
                "この記事は技術的な革新について述べています。主要なポイントは、新しいアルゴリズムの効率性と、それが業界にもたらす可能性のある変化です。",
                "この投稿は機械学習の最新トレンドに焦点を当てています。特に注目すべきは、モデルの精度向上と計算コストの削減です。",
                "この論文は自然言語処理の進歩について論じています。主な貢献は、新しい言語モデルのアーキテクチャと、それによるパフォーマンスの向上です。",
                "このプロジェクトはオープンソースコミュニティに大きな影響を与える可能性があります。特に、開発者の生産性向上とコード品質の改善に貢献します。",
                "この記事はAIの倫理的側面について考察しています。主要な議論は、透明性、公平性、およびプライバシーに関するものです。"
            ]
            
            # トピック別のダミーレスポンス
            self.topic_responses = {
                "reddit|python|programming": [
                    "このReddit投稿はPythonプログラミングに関するもので、効率的なコード実装とベストプラクティスについて議論しています。",
                    "この投稿はPythonライブラリの使用方法について説明しており、特に機械学習フレームワークの活用に焦点を当てています。",
                    "このスレッドはプログラミングの課題と解決策について議論しており、特にパフォーマンス最適化に関する洞察を提供しています。"
                ],
                "github|repository|trending": [
                    "このGitHubリポジトリは、データ処理のための効率的なツールを提供しています。主な特徴は、高速な処理能力とユーザーフレンドリーなAPIです。",
                    "このトレンディングプロジェクトは、ウェブ開発のための新しいフレームワークを提供しています。特に注目すべきは、その柔軟性と拡張性です。",
                    "このリポジトリは、機械学習モデルのデプロイを簡素化するツールを提供しています。主な利点は、その使いやすさとスケーラビリティです。"
                ],
                "paper|research|arxiv": [
                    "この研究論文は、深層学習の新しいアプローチを提案しています。実験結果は、従来の方法と比較して有意な改善を示しています。",
                    "この論文は、自然言語処理の課題に対する革新的な解決策を提示しています。提案されたモデルは、複数のベンチマークで最先端の結果を達成しています。",
                    "この研究は、コンピュータビジョンの分野における重要な進展を報告しています。新しいアーキテクチャは、精度と効率性の両方を向上させています。"
                ],
                "news|hacker|tech": [
                    "この技術ニュースは、業界の最新動向について報告しています。特に注目すべきは、新しいテクノロジーの採用とその市場への影響です。",
                    "このHacker Newsの記事は、開発者コミュニティ内の重要な議論を取り上げています。主なトピックは、オープンソースの持続可能性と企業の関与です。",
                    "このテック記事は、新興技術の可能性と課題について分析しています。特に、プライバシーとセキュリティの側面に焦点を当てています。"
                ]
            }
        
        def generate_content(self, contents, system_instruction=None):
            print("DummyClient: APIを使わずにダミーレスポンスを返します")
            
            # コンテンツに基づいて適切なレスポンスを選択
            content_str = str(contents).lower()
            
            for keywords, responses in self.topic_responses.items():
                keywords_list = keywords.split('|')
                if any(keyword in content_str for keyword in keywords_list):
                    return random.choice(responses)
            
            # 特定のトピックが見つからない場合は一般的なレスポンスを返す
            return random.choice(self.general_responses)
        
        def chat_with_search(self, message):
            print("DummyClient: APIを使わずにダミーレスポンスを返します")
            return self.generate_content(message)
    
    if not api_key:
        print("警告: GEMINI_API_KEYが設定されていません。ダミークライアントを使用します。")
        return DummyClient()
    
    genai.configure(api_key=api_key)
    
    class GeminiClient:
        def __init__(self, model_name=model_name):
            # 最新のモデル名を使用
            self.model = genai.GenerativeModel(model_name)
            self.dummy_client = DummyClient()
        
        def generate_content(self, contents, system_instruction=None):
            """コンテンツを生成する"""
            try:
                if system_instruction:
                    # 最新のAPIでは、system_instructionをプロンプトの一部として組み込む
                    prompt = f"{system_instruction}\n\n{contents}"
                    response = self.model.generate_content(prompt)
                else:
                    response = self.model.generate_content(contents)
                
                return response.text
            except Exception as e:
                print(f"Gemini API呼び出しエラー: {e}")
                # APIクォータ制限に達した場合（429エラー）
                if "429" in str(e) or "quota" in str(e).lower() or "exhausted" in str(e).lower():
                    print("APIクォータ制限に達しました。ダミーレスポンスを返します。")
                    return self.dummy_client.generate_content(contents, system_instruction)
                return f"エラーが発生しました: {str(e)}"
        
        def chat_with_search(self, message):
            """検索結果を活用してチャットする（ローカル版では検索機能は簡略化）"""
            # 実際の検索は行わず、単純に応答を返す
            return self.generate_content(message)
    
    return GeminiClient()