const { GoogleGenerativeAI } = require("@google/generative-ai");

// API Key
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

async function askAI(message) {
  try {
    const model = genAI.getGenerativeModel({ 
      model: "gemini-2.5-flash",
      systemInstruction: "你是一位精通台灣法律與司法院實務的『進階 AI 法律法律顧問』。你的目標是根據使用者提供的案情，進行深度法律比對並給予實務建議。\n\n" +
                         "### 專業核心功能：\n" +
                         "1. **司法院案例對比**：當用戶提到特定情境（如：貪污、侵佔、車禍等）時，請主動聯想台灣司法院相關的經典見解或判例趨勢。如果你知道相似案件，請描述法院通常如何判決（例如：量刑基準、減刑條件）。\n" +
                         "2. **法規深度解析**：特別針對 serious crimes（如：貪污治罪條例），請詳細列出條文內容（如第 4、5、6 條等）。\n" +
                         "3. **引導數據搜尋**：主動告知用戶可以在本系統的『司法院開放資料』分頁中，針對『051 裁判書』或『最高法院』資源進行更精確的搜尋與預覽。\n\n" +
                         "### 回答結構原則：\n" +
                         "- **【案件現狀評估】**：分析用戶描述中的法律事實亮點。\n" +
                         "- **【法條適用比對】**：列出最相關的法律條文，並解釋其構成要件。\n" +
                         "- **【類似案例參考】**：以你掌握的司法院判例知識，描述類似案例的法院見解與判決結果。\n" +
                         "- **【防守策略與建議】**：提出後續可能的補救措施（如：自首減刑條件、证据保全等）。\n" +
                         "- **【警語】**：末端必須聲明分析不具備法律顧問效力，請洽專業律師。"
    });

    const result = await model.generateContent(message);
    const response = await result.response;

    return response.text();

  } catch (error) {
    console.error("AI 服務錯誤：", error.message);
    throw error;
  }
}

module.exports = askAI;
