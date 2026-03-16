from pymongo import MongoClient
import time
import os

# ---------------- MongoDB Configuration ----------------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/")
DB_NAME = "ai_law"

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.client = MongoClient(MONGO_URI)
            cls._instance.db = cls._instance.client[DB_NAME]
        return cls._instance

    @property
    def users(self):
        return self.db["users"]

    @property
    def chats(self):
        return self.db["chats"]

def init_db():
    db_instance = Database()
    users_collection = db_instance.users
    chats_collection = db_instance.chats
    
    try:
        if users_collection.count_documents({}) == 0:
            print("\n=== [System] 檢測到資料庫為空，正在進行自動初始化... ===")
            # 建立預設帳號
            users_collection.insert_one({
                "username": "admin",
                "password": "password123", 
                "email": "admin@legal-ai.tw",
                "createdAt": time.time()
            })
            # 建立預設對話紀錄
            chats_collection.insert_one({
                "userId": "system",
                "conversationId": "init-check",
                "message": "系統初始化",
                "aiResponse": "歡迎使用 AI 法律諮詢助理，資料庫已成功建立。",
                "createdAt": time.time()
            })
            print("=== [System] 預設帳號 admin / password123 建立完成 ===\n")
    except Exception as e:
        print(f"\n⚠️ [Warning] 資料庫初始化檢查失敗: {e}")
        print("請確保 MongoDB 服務已啟動。\n")

# Export a singleton instance
db = Database()
