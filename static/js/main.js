document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const docContent = document.getElementById('doc-content');
    const resultArea = document.getElementById('result-area');
    const welcomeMsg = document.getElementById('welcome-message');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsContent = document.getElementById('results-content');
    const statusBadge = document.getElementById('analysis-status');

    // Auto-analyze if text is pre-filled from Linked Search
    if (docContent.value.trim().length > 10) {
        setTimeout(() => analyzeBtn.click(), 500);
    }

    analyzeBtn.addEventListener('click', async () => {
        const text = docContent.value.trim();
        if (!text) {
            alert('請輸入文件內容');
            return;
        }

        // UI State Update
        welcomeMsg.classList.add('hidden');
        resultsContent.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 分析中...';
        statusBadge.innerText = '分析中';
        statusBadge.className = 'status-badge badge-gold';

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: text }),
            });

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                resetUI();
                return;
            }

            // Display Results
            displayResults(data);

            // Dynamically add to sidebar
            const caseList = document.querySelector('.case-list');
            if (caseList) {
                const newCaseHTML = `
                    <div class="case-item">
                        <div class="case-info">
                            <span class="case-title">分析：${text.substring(0, 10)}...</span>
                            <span class="case-date">${new Date().toLocaleDateString()}</span>
                        </div>
                        <p class="case-snippet">${text.substring(0, 50).replace(/\n/g, ' ')}...</p>
                    </div>
                `;
                caseList.insertAdjacentHTML('afterbegin', newCaseHTML);
                if (caseList.children.length > 8) caseList.lastElementChild.remove();
            }

        } catch (error) {
            console.error('Error:', error);
            alert('分析過程中發生錯誤，請稍後再試。');
            resetUI();
        }
    });

    function displayResults(data) {
        loadingSpinner.classList.add('hidden');
        resultsContent.classList.remove('hidden');
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-magic"></i> 開始 AI 比對分析';
        statusBadge.innerText = '已完成 AI 比對分析';
        statusBadge.className = 'status-badge badge-blue';

        // Enhanced Markdown Parsing
        let content = data.aiResponse || "";
        
        // Headers
        content = content.replace(/^### (.*$)/gim, '<h3 style="color:var(--accent);margin-top:20px;margin-bottom:10px;border-bottom:1px solid var(--glass-border);padding-bottom:5px;">$1</h3>');
        content = content.replace(/^## (.*$)/gim, '<h2 style="color:var(--accent);margin-top:25px;margin-bottom:15px;">$1</h2>');
        
        // Bold
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--text-white); font-weight:700;">$1</strong>');
        
        // Lists
        content = content.replace(/^\* (.*$)/gim, '<li style="margin-left:20px;margin-bottom:8px;color:var(--text-white);">$1</li>');
        content = content.replace(/^- (.*$)/gim, '<li style="margin-left:20px;margin-bottom:8px;color:var(--text-white);">$1</li>');

        // Detecting navigation intent
        const showSearchCTA = content.includes("司法院開放資料") || content.includes("裁判書");

        let html = `
            <div style="margin-bottom: 25px; padding: 15px; background: rgba(59, 130, 246, 0.1); border-radius: 12px; border-left: 4px solid var(--primary-light); display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: var(--text-white); margin: 0;"><i class="fas fa-robot"></i> AI 法律顧問深度分析報告</h4>
            </div>
            
            <div class="ai-report-body" style="line-height: 1.8; font-size: 1.05rem; padding: 10px;">
                ${content.replace(/\n\n/g, '<div style="margin-bottom:15px;"></div>').replace(/\n/g, '<br>')}
            </div>
        `;

        if (showSearchCTA) {
            html += `
                <div style="margin-top: 30px; padding: 20px; background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(212, 175, 55, 0.05)); border: 1px solid var(--accent); border-radius: 12px; text-align: center;">
                    <h4 style="color: var(--accent); margin-bottom: 15px;"><i class="fas fa-link"></i> 聯動搜索：獲取真實判例</h4>
                    <p style="font-size: 0.9rem; color: var(--text-dim); margin-bottom: 20px;">AI 建議您進一步比對真實司法數據，以強化法律立場。</p>
                    <a href="/judicial_data" class="btn-primary" style="display: inline-block; width: auto; padding: 10px 30px; text-decoration: none;">
                        <i class="fas fa-search"></i> 前往司法院開放資料
                    </a>
                </div>
            `;
        }

        resultsContent.innerHTML = html;
        resultsContent.scrollTop = 0;
    }

    function resetUI() {
        loadingSpinner.classList.add('hidden');
        welcomeMsg.classList.remove('hidden');
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-magic"></i> 開始 AI 比對分析';
        statusBadge.innerText = '等待輸入';
    }
});
