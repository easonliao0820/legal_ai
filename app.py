from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import requests
import hashlib
import uuid
from pymongo import MongoClient
import time

app = Flask(__name__)
app.secret_key = "legal_ai_secure_key" # In production, use environment variables

# ---------------- MongoDB ----------------
MONGO_URI = "mongodb://127.0.0.1:27017/"
client = MongoClient(MONGO_URI)
db = client["ai_law"]
users_collection = db["users"]
chats_collection = db["chats"]

# ---------------- Node.js AI API ----------------
NODE_API_URL = "http://localhost:5003/api/analyze"

# --- Mock AI Logic ---
# Since we are not connecting to the real API yet, we simulate the comparison
def simulate_legal_analysis(content):
    # This simulates comparing user documents with "Ministry of Justice" patterns
    time.sleep(2) # Simulate processing time
    
    analysis = {
        "score": 85,
        "recommendations": [
            {
                "title": "訴訟策略建議 (Litigation Strategy)",
                "content": "根據法務部相似判例，本案件建議強調『事實發生之不可抗力性』。文件內對於時間點的描述需更精確以強化證據效力。"
            },
            {
                "title": "文件內容優化 (Document Improvement)",
                "content": "建議在第三段加入具體的損害賠償計算基礎。目前內容較為籠統，比對歷史判決後，具體化數額能增加法官採信度。"
            },
            {
                "title": "法規比對提醒 (Legal Pattern Match)",
                "content": "偵測到與民法第 184 條相關之敘述，建議補充行為人與損害間之因果關係說明。"
            }
        ],
        "status": "已完成 AI 比對分析"
    }
    return analysis

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return redirect(url_for('index'))

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = users_collection.find_one({"username": username, "password": password})

    if user:
        session['user_id'] = str(user["_id"])
        session['username'] = user["username"]
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error="帳號或密碼錯誤")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    # 查詢該使用者的最近 5 筆聊天紀錄
    chats = list(chats_collection.find({"userId": session['user_id']}).sort("createdAt", -1).limit(5))
    return render_template('dashboard.html', username=session['username'], chats=chats)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # 修正 1: 安全取得 JSON，防呆
    data = request.get_json(silent=True) or {}
    content = data.get('content', '')
    if not content:
        return jsonify({"error": "內容不能為空"}), 400

    conversation_id = str(uuid.uuid4())
    user_id = session['user_id']

    payload = {
        "userId": user_id,
        "conversationId": conversation_id,
        "content": content
    }

    try:
        # 修正 2: 增加 timeout 以及錯誤狀態檢查 (加長至 60 秒，Gemini 處理長文需要較久)
        response = requests.post(NODE_API_URL, json=payload, timeout=60)
        response.raise_for_status() 
        
        result = response.json()
        ai_reply = result.get("aiResponse", "")
        
        # 同步存入 MongoDB (保險起見)
        chats_collection.insert_one({
            "userId": user_id,
            "conversationId": conversation_id,
            "message": content,
            "aiResponse": ai_reply,
            "createdAt": time.time()
        })
    except Exception as e:
        return jsonify({"error": "Node.js AI 服務無法連線或處理失敗", "details": str(e)}), 500

    return jsonify({
        "conversationId": conversation_id,
        "aiResponse": ai_reply
    })


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

# --- Auto-start Node.js Server ---
import subprocess
import atexit

node_process = None

def cleanup_node_server():
    global node_process
    if node_process:
        print("\n=== [System] Terminating Node.js AI Server ===")
        node_process.terminate()
        try:
            node_process.wait(timeout=3)
        except Exception:
            node_process.kill()

atexit.register(cleanup_node_server)

if __name__ == '__main__':
    # Flask in debug mode restarts the script. We only want to spawn Node from the parent process.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print("\n=== [System] Starting Node.js AI Server on port 5003... ===")
        node_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node")
        # Uses Popen to start node server in the background
        node_process = subprocess.Popen(
            ["node", "server.js"],
            cwd=node_dir,
            shell=True # For Windows compatibility
        )

    app.run(debug=True, port=5002)
