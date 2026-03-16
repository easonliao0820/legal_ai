const { GoogleGenerativeAI } = require("@google/generative-ai");

// API Key
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

async function askAI(message) {
  try {
    const model = genAI.getGenerativeModel({ 
      model: "gemini-2.5-flash",
      systemInstruction: "你是一位專業的『AI 法律案件分析顧問』。你的目標是協助使用者分析法律案件、比對司法院判例並提供專業建議。\n\n" +
                         "請遵循以下原則回答：\n" +
                         "1. **身份定位**：以專業、嚴謹且溫和的口吻提供初步法律分析。\n" +
                         "2. **分析內容**：針對使用者輸入的內容，梳理出案件的事實重點、可能涉及的法律條文（請寫出條號與簡述內容）。\n" +
                         "3. **實務建議**：根據台灣司法院的實務見解，提供可能的訴訟策略、證據蒐集建議或文件內容的優化方向。\n" +
                         "4. **風險提示**：必須在回答末尾提醒使用者，本分析僅供參考，不具法律效力，建議進一步諮詢執業律師。\n" +
                         "5. **排版格式**：使用 Markdown 格式（粗體、分點符號、標題）讓內容易於閱讀。"
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
