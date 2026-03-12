const mongoose = require("mongoose");
const MONGO_URI = 'mongodb://127.0.0.1:27017/ai_law';

async function connectMongo() {
  try {
    await mongoose.connect(MONGO_URI);

    console.log("MongoDB connected");
  } catch (err) {
    console.error("MongoDB connection error:", err);
  }
}

module.exports = connectMongo;