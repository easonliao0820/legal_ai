import requests
import time
import os

class AIService:
    def __init__(self, api_url):
        self.api_url = api_url

    def analyze_content(self, user_id, conversation_id, content):
        payload = {
            "userId": user_id,
            "conversationId": conversation_id,
            "content": content
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"AI 服務通訊失敗: {str(e)}")

    def simulate_legal_analysis(self, content):
        """Mock version for UI testing if Node server is down."""
        time.sleep(1)
        return {
            "score": 85,
            "aiResponse": "這是模擬的法律分析報告內容...",
            "status": "已完成"
        }
