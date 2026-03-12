const mongoose = require("mongoose");

const ChatSchema = new mongoose.Schema({

  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "User"
  },

  conversationId: {
    type: String,
    required: true
  },

  message: String,

  aiResponse: String,

  createdAt: {
    type: Date,
    default: Date.now
  }

});

module.exports = mongoose.model("Chat", ChatSchema);