import os
import google.generativeai as genai

def create_client(use_search=False):
    """Gemini APIクライアントを作成する"""
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    class GeminiClient:
        def __init__(self, model_name="gemini-pro"):
            self.model = genai.GenerativeModel(model_name)
        
        def generate_content(self, contents, system_instruction=None):
            """コンテンツを生成する"""
            if system_instruction:
                chat = self.model.start_chat(system_instruction=system_instruction)
                response = chat.send_message(contents)
            else:
                response = self.model.generate_content(contents)
            
            return response.text
        
        def chat_with_search(self, message):
            """検索結果を活用してチャットする（ローカル版では検索機能は簡略化）"""
            # 実際の検索は行わず、単純に応答を返す
            return self.generate_content(message)
    
    return GeminiClient()