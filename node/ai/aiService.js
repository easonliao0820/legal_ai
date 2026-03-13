const { GoogleGenerativeAI } = require("@google/generative-ai");

// API Key
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

async function askAI(message) {
  try {

    // 必須使用金鑰支援的模型 (gemini-2.5-flash)
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const result = await model.generateContent(message);
    const response = await result.response;

    return response.text();

  } catch (error) {
    console.error("印出錯誤(拜託不要再404了我求你)：", error.message);
    throw error;
  }
}

module.exports = askAI;
