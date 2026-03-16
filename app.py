from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
import os
import requests
import hashlib
import uuid
from pymongo import MongoClient
import time
import tempfile
import zipfile
import shutil
import rarfile
import py7zr
import subprocess
from judicial_api import JudicialOpenDataAPI

app = Flask(__name__)
app.secret_key = "legal_ai_secure_key" # In production, use environment variables

# ---------------- MongoDB ----------------
MONGO_URI = "mongodb://127.0.0.1:27017/"
client = MongoClient(MONGO_URI)
db = client["ai_law"]
users_collection = db["users"]
chats_collection = db["chats"]

# --- 自動初始化資料庫 (Auto-Init) ---
try:
    if users_collection.count_documents({}) == 0:
        print("\n=== [System] 檢測到資料庫為空，正在進行自動初始化... ===")
        # 建立預設帳號
        users_collection.insert_one({
            "username": "admin",
            "password": "password123", # 您的登入邏輯目前比對明文
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
    analyze_text = request.args.get('analyze_text', '')
    return render_template('dashboard.html', username=session['username'], chats=chats, prefill_text=analyze_text)

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


@app.route('/judicial_data')
@app.route('/judicial_data/<category_no>')
def judicial_data(category_no=None):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    api = JudicialOpenDataAPI()
    try:
        all_categories = api.get_categories()
        # 排除對一般民眾較無用的分類：統計、預算、支出、諮詢、代碼等
        exclude_keywords = ['統計', '預算', '支出', '諮詢', '代碼']
        categories = [
            cat for cat in all_categories 
            if not any(kw in cat['categoryName'] for kw in exclude_keywords)
        ]
        categories.reverse() # 倒敘顯示
    except Exception as e:
        categories = []
        print(f"Error fetching categories: {e}")

    resources = []
    if category_no:
        try:
            resources = api.get_category_resources(category_no)
            resources.reverse() # 倒敘顯示
        except Exception as e:
            print(f"Error fetching resources for {category_no}: {e}")

    return render_template('judicial_data.html', 
                           username=session.get('username'),
                           categories=categories,
                           selected_category=category_no,
                           resources=resources)

@app.route('/judicial_download/<file_set_id>/<format>')
def judicial_download(file_set_id, format):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    api = JudicialOpenDataAPI()
    try:
        data = api.get_file(file_set_id)
        
        # Determine if data is JSON (dict/list)
        if isinstance(data, (dict, list)):
            # It's JSON parsed by our API client
            import json
            response = make_response(json.dumps(data, ensure_ascii=False))
            response.headers["Content-Disposition"] = f"attachment; filename=dataset_{file_set_id}.json"
            response.headers["Content-Type"] = "application/json; charset=utf-8"
            return response
        else:
            # It's raw bytes (like CSV, 7Z, etc.)
            response = make_response(data)
            ext = format.lower() if format else "bin"
            response.headers["Content-Disposition"] = f"attachment; filename=dataset_{file_set_id}.{ext}"
            return response
            
    except Exception as e:
        return f"下載檔案失敗: {e}", 500

@app.route('/judicial_preview/<file_set_id>/<format>')
def judicial_preview(file_set_id, format):
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    cache_dir = f"/tmp/legal_ai_cache/{file_set_id}"
    api = JudicialOpenDataAPI()
    
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        try:
            data = api.get_file(file_set_id)
            if not isinstance(data, bytes):
                import json
                with open(os.path.join(cache_dir, f"dataset_{file_set_id}.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            else:
                archive_path = os.path.join(cache_dir, f"temp.{format.lower()}")
                with open(archive_path, "wb") as f:
                    f.write(data)
                
                fmt = format.lower()
                try:
                    if fmt == '7z':
                        with py7zr.SevenZipFile(archive_path, 'r') as z:
                            z.extractall(cache_dir)
                    elif fmt == 'zip':
                        with zipfile.ZipFile(archive_path, 'r') as z:
                            z.extractall(cache_dir)
                    elif fmt == 'rar':
                        # Use bsdtar because unrar is often missing on Mac
                        try:
                            subprocess.run(['bsdtar', '-xf', archive_path, '-C', cache_dir], check=True)
                        except Exception as e:
                            # Fallback to rarfile if bsdtar fails
                            with rarfile.RarFile(archive_path, 'r') as z:
                                z.extractall(cache_dir)
                except Exception as e:
                    pass # Migh not be an archive, ignore extraction error
                
                if os.path.exists(archive_path):
                    os.remove(archive_path)
        except Exception as e:
            # Cleanup if failed
            shutil.rmtree(cache_dir, ignore_errors=True)
            return f"處理資料失敗: {e}", 500
            
    # List files
    all_files = []
    for root, _, files in os.walk(cache_dir):
        for f in files:
            if f.startswith('.'): continue
            rel_path = os.path.relpath(os.path.join(root, f), cache_dir)
            all_files.append(rel_path)
            
    selected_file = request.args.get('file')
    content = None
    json_data = None
    error = None
    
    if selected_file and selected_file in all_files:
        filepath = os.path.join(cache_dir, selected_file)
        try:
            with open(filepath, 'rb') as f:
                raw_bytes = f.read(1024 * 500) # Read up to 500KB
                
                # Check encoding
                try:
                    text_content = raw_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text_content = raw_bytes.decode('big5')
                    except Exception:
                        text_content = None
                
                if text_content:
                    if selected_file.lower().endswith('.json'):
                        try:
                            import json
                            json_parsed = json.loads(text_content)
                            # If it's a list with one item (sometimes Judicial data is wrapped)
                            if isinstance(json_parsed, list) and len(json_parsed) > 0:
                                json_data = json_parsed[0]
                            else:
                                json_data = json_parsed
                            
                            # If it has JFULL, we extract it for prominent display
                            if isinstance(json_data, dict) and 'JFULL' in json_data:
                                content = json_data.get('JFULL', '')
                            else:
                                content = text_content
                        except:
                            content = text_content
                    else:
                        content = text_content
        except Exception as e:
            error = f"讀取檔案失敗: {e}"
            
    return render_template('judicial_preview.html',
                           file_set_id=file_set_id,
                           files=sorted(all_files),
                           selected_file=selected_file,
                           content=content,
                           json_data=json_data,
                           error=error)

@app.route('/judicial_preview_download/<file_set_id>/<path:filepath>')
def judicial_preview_download(file_set_id, filepath):
    cache_dir = f"/tmp/legal_ai_cache/{file_set_id}"
    full_path = os.path.join(cache_dir, filepath)
    if os.path.exists(full_path) and os.path.abspath(full_path).startswith(os.path.abspath(cache_dir)):
        from flask import send_file
        return send_file(full_path, as_attachment=True)
    return "檔案不存在", 404

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
