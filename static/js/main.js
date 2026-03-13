document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const docContent = document.getElementById('doc-content');
    const resultArea = document.getElementById('result-area');
    const welcomeMsg = document.getElementById('welcome-message');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsContent = document.getElementById('results-content');
    const statusBadge = document.getElementById('analysis-status');

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
                            <span class="case-title">新增分析：${text.substring(0, 10)}...</span>
                            <span class="case-date">${new Date().toISOString().split('T')[0]}</span>
                        </div>
                        <p class="case-snippet">${text.substring(0, 50)}...</p>
                    </div>
                `;
                caseList.insertAdjacentHTML('afterbegin', newCaseHTML);
                // Maintain only top 5 cases in view
                if (caseList.children.length > 5) {
                    caseList.removeChild(caseList.lastElementChild);
                }
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

        // 轉換 AI 的純文字回應 (保留換行與粗體)
        const formattedResponse = (data.aiResponse || "").replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');

        let html = `
            <div style="margin-bottom: 25px; padding: 15px; background: rgba(59, 130, 246, 0.1); border-radius: 12px; border-left: 4px solid var(--primary-light);">
                <h4 style="color: var(--text-white); margin-bottom: 5px;">AI 法律顧問回覆</h4>
            </div>
            <div class="suggestion-card" style="white-space: pre-wrap; line-height: 1.6;">
                ${formattedResponse}
            </div>
        `;

        resultsContent.innerHTML = html;
        
        // Auto scroll to bottom
        resultArea.scrollTo({
            top: resultArea.scrollHeight,
            behavior: 'smooth'
        });
    }


    function resetUI() {
        loadingSpinner.classList.add('hidden');
        welcomeMsg.classList.remove('hidden');
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-magic"></i> 開始 AI 比對分析';
        statusBadge.innerText = '等待輸入';
    }
});
