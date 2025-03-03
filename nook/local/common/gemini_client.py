import os
import google.generativeai as genai

def create_client(use_search=False):
    """Gemini APIクライアントを作成する"""
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-pro-exp-02-05")
    
    if not api_key:
        print("警告: GEMINI_API_KEYが設定されていません。")
        return DummyClient()
    
    genai.configure(api_key=api_key)
    
    class GeminiClient:
        def __init__(self, model_name=model_name):
            # 最新のモデル名を使用
            self.model = genai.GenerativeModel(model_name)
        
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
                return f"エラーが発生しました: {str(e)}"
        
        def chat_with_search(self, message):
            """検索結果を活用してチャットする（ローカル版では検索機能は簡略化）"""
            # 実際の検索は行わず、単純に応答を返す
            return self.generate_content(message)
    
    class DummyClient:
        """APIキーが設定されていない場合のダミークライアント"""
        def generate_content(self, contents, system_instruction=None):
            return "APIキーが設定されていないため、応答を生成できません。"
        
        def chat_with_search(self, message):
            return "APIキーが設定されていないため、応答を生成できません。"
    
    return GeminiClient()