const express = require("express");
const cors = require("cors");
require("dotenv").config();
const connectMongo = require("./db/mongodb");
const Chat = require("./models/Chat");
const User = require("./models/User");
const askAI = require("./ai/aiService");

const app = express();
app.use(cors());
app.use(express.json());

connectMongo();

// API: 分析案件
app.post("/api/analyze", async (req, res) => {
    try {
        const { userId, conversationId, content } = req.body;

        if (!userId || !conversationId || !content) {
            return res.status(400).json({ error: "缺少參數" });
        }

        // 呼叫 Gemini AI
        const aiReply = await askAI(content);

        // 存 MongoDB 聊天紀錄
        const chat = await Chat.create({
            userId,
            conversationId,
            message: content,
            aiResponse: aiReply
        });

        res.json({
            chatId: chat._id,
            aiResponse: aiReply
        });

    } catch (err) {
        console.error("發生錯誤:", err);
        res.status(500).json({ error: "AI 或資料庫出錯", details: err.message, stack: err.stack });
    }
});

// 啟動 Node.js 伺服器
app.listen(5003, () => {
    console.log("Node.js AI API running on port 5003");
});