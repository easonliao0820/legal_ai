from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import time

app = Flask(__name__)
app.secret_key = "legal_ai_secure_key" # In production, use environment variables

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
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    # Simple mock login
    username = request.form.get('username')
    if username:
        session['user'] = "admin"
        return redirect(url_for('dashboard'))
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    # Initialize mock cases if not present
    if 'cases' not in session:
        session['cases'] = [
            {"id": 1, "title": "民事訴訟：鄰損案件分析", "date": "2024-03-10", "snippet": "關於建築工地施工導致鄰房龜裂之損害賠償..."},
            {"id": 2, "title": "勞資糾紛：不當解雇諮詢", "date": "2024-03-11", "snippet": "員工主張公司未經預告即終止勞動契約，請求..."},
        ]
    
    return render_template('dashboard.html', username=session['user'], cases=session['cases'])

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    content = data.get('content', '')
    
    if not content:
        return jsonify({"error": "內容不能為空"}), 400
    
    result = simulate_legal_analysis(content)
    
    # Save to session history
    if 'cases' not in session:
        session['cases'] = []
    
    new_case = {
        "id": len(session['cases']) + 1,
        "title": f"新增分析：{content[:10]}...",
        "date": time.strftime("%Y-%m-%d"),
        "snippet": content[:50] + "..."
    }
    # Limit history to top 5
    session['cases'].insert(0, new_case)
    session['cases'] = session['cases'][:5]
    session.modified = True
    
    return jsonify(result)

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('cases', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5002) 

