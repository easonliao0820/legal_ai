from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response, send_file
from datetime import datetime
import os
import hashlib
import uuid
import time
import json
import subprocess
import atexit

# Modular Imports
from core.database import db, init_db
from core.ai_service import AIService
from core.judicial_client import JudicialOpenDataAPI
from utils.file_handler import FileHandler

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "legal_ai_secure_key")

# Service Initializations
NODE_API_URL = "http://localhost:5003/api/analyze"
ai_service = AIService(NODE_API_URL)
judicial_api = JudicialOpenDataAPI()

# Initialize Database on Startup
init_db()

# ---------------- Auth Routes ----------------

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

    # Simplified login (matches user password as is for now)
    user = db.users.find_one({"username": username, "password": password})

    if user:
        session['user_id'] = str(user["_id"])
        session['username'] = user["username"]
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error="帳號或密碼錯誤")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('register.html', error="兩次輸入的密碼不一致")

        if db.users.find_one({"username": username}):
            return render_template('register.html', error="該用戶名稱已被註冊")

        if db.users.find_one({"email": email}):
            return render_template('register.html', error="該電子郵件已被註冊")

        # Create new user
        db.users.insert_one({
            "username": username,
            "password": password, # In production, use hashing!
            "email": email,
            "createdAt": time.time()
        })
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ---------------- Dashboard & AI Routes ----------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    # Fetch and format recent chats for the sidebar
    recent_chats = list(db.chats.find({"userId": session['user_id']}).sort("createdAt", -1).limit(5))
    cases = []
    for chat in recent_chats:
        content = chat.get('content', chat.get('message', ''))
        created_at = chat.get('createdAt')
        
        date_str = "未知時間"
        if created_at:
            if isinstance(created_at, (int, float)):
                date_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M")
            elif hasattr(created_at, 'strftime'):
                date_str = created_at.strftime("%Y-%m-%d %H:%M")
        
        cases.append({
            "id": str(chat.get('_id')),
            "title": content[:15] + ("..." if len(content) > 15 else ""),
            "date": date_str,
            "snippet": content[:50] + ("..." if len(content) > 50 else "")
        })
    
    analyze_text = request.args.get('analyze_text', '')
    return render_template('dashboard.html', username=session['username'], cases=cases, prefill_text=analyze_text)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    content = data.get('content', '')
    if not content:
        return jsonify({"error": "內容不能為空"}), 400

    conv_id = str(uuid.uuid4())
    user_id = session['user_id']

    try:
        # Call Node.js AI Service
        result = ai_service.analyze_content(user_id, conv_id, content)
        ai_reply = result.get("aiResponse", "")
        
        # Save to DB
        db.chats.insert_one({
            "userId": user_id,
            "conversationId": conv_id,
            "content": content,
            "message": content, # Legacy support
            "aiResponse": ai_reply,
            "createdAt": time.time()
        })
    except Exception as e:
        return jsonify({"error": "AI 處理失敗", "details": str(e)}), 500

    return jsonify({
        "conversationId": conv_id,
        "aiResponse": ai_reply
    })

# ---------------- Judicial Data Routes ----------------

@app.route('/judicial_data')
@app.route('/judicial_data/<category_no>')
def judicial_data(category_no=None):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    try:
        all_categories = judicial_api.get_categories()
        # Filter unwanted categories
        exclude_kw = ['統計', '預算', '支出', '諮詢', '代碼']
        categories = [c for c in all_categories if not any(kw in c['categoryName'] for kw in exclude_kw)]
        categories.reverse()
    except Exception as e:
        categories = []
        print(f"API Error: {e}")

    resources = []
    search_query = request.args.get('search', '').strip().lower()
    
    if category_no:
        try:
            resources = judicial_api.get_category_resources(category_no)
            if search_query:
                resources = [r for r in resources if search_query in r['title'].lower() or search_query in r.get('description', '').lower()]
            resources.reverse()
        except Exception as e:
            print(f"Resource Load Error: {e}")

    return render_template('judicial_data.html', 
                           username=session.get('username'),
                           categories=categories,
                           selected_category=category_no,
                           resources=resources)

@app.route('/judicial_download/<file_set_id>/<format>')
def judicial_download(file_set_id, format):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    try:
        data = judicial_api.get_file(file_set_id)
        if isinstance(data, (dict, list)):
            resp = make_response(json.dumps(data, ensure_ascii=False))
            resp.headers["Content-Disposition"] = f"attachment; filename=ds_{file_set_id}.json"
            resp.headers["Content-Type"] = "application/json; charset=utf-8"
            return resp
        else:
            resp = make_response(data)
            resp.headers["Content-Disposition"] = f"attachment; filename=ds_{file_set_id}.{format.lower()}"
            return resp
    except Exception as e:
        return f"下載失敗: {e}", 500

@app.route('/judicial_preview/<file_set_id>/<format>')
def judicial_preview(file_set_id, format):
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    cache_dir = f"/tmp/legal_ai_cache/{file_set_id}"
    
    # Check cache
    if not os.path.exists(cache_dir) or not os.listdir(cache_dir):
        FileHandler.cleanup_dir(cache_dir)
        os.makedirs(cache_dir, exist_ok=True)
        try:
            data = judicial_api.get_file(file_set_id)
            if not isinstance(data, bytes):
                with open(os.path.join(cache_dir, f"data.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            else:
                temp_path = os.path.join(cache_dir, f"temp.{format.lower()}")
                with open(temp_path, "wb") as f:
                    f.write(data)
                
                # Use util for extraction
                extracted = FileHandler.extract_archive(temp_path, cache_dir, format)
                
                if extracted and os.path.exists(temp_path):
                    os.remove(temp_path)
                elif not extracted:
                    os.rename(temp_path, os.path.join(cache_dir, f"data.{format.lower()}"))
        except Exception as e:
            FileHandler.cleanup_dir(cache_dir)
            return f"處理失敗: {e}", 500
            
    # File listing for sidebar
    all_files = []
    for root, _, files in os.walk(cache_dir):
        for f in files:
            if f.startswith('.'): continue
            all_files.append(os.path.relpath(os.path.join(root, f), cache_dir))
            
    selected_file = request.args.get('file')
    content, json_data, error = None, None, None
    
    if selected_file and selected_file in all_files:
        filepath = os.path.join(cache_dir, selected_file)
        text_content = FileHandler.read_text_file(filepath)
        
        if text_content:
            if selected_file.lower().endswith('.json'):
                try:
                    json_parsed = json.loads(text_content)
                    json_data = json_parsed[0] if isinstance(json_parsed, list) and len(json_parsed) > 0 else json_parsed
                    content = json_data.get('JFULL', text_content) if isinstance(json_data, dict) else text_content
                except:
                    content = text_content
            else:
                content = text_content
        else:
            error = "無法讀取該檔案編碼或檔案為二進制格式"
            
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
        return send_file(full_path, as_attachment=True)
    return "檔案不存在", 404

# ---------------- Process Management ----------------

node_process = None

def stop_node():
    global node_process
    if node_process:
        print("\n=== [System] Stopping Node AI Server ===")
        node_process.terminate()

atexit.register(stop_node)

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print("\n=== [System] Starting Background Node AI Server... ===")
        node_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node")
        node_process = subprocess.Popen(["node", "server.js"], cwd=node_path, shell=True)

    app.run(debug=True, port=5002)
