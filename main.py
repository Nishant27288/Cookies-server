import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import time
import random
import requests

TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"  # Telegram bot ka token yahan daalo

# Conversation states
(ASK_TOKENS, ASK_URL, ASK_COMMENT_ID, ASK_FILE, ASK_DELAY, START_REPLY) = range(6)

user_data = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Kitne Facebook tokens use karne hai?")
    return ASK_TOKENS

def ask_url(update: Update, context: CallbackContext):
    user_data["tokens_count"] = int(update.message.text)
    user_data["tokens"] = []
    update.message.reply_text("Facebook Post URL do:")
    return ASK_URL

def ask_comment_id(update: Update, context: CallbackContext):
    user_data["post_url"] = update.message.text
    update.message.reply_text("Jis comment pe reply dena hai uska ID do:")
    return ASK_COMMENT_ID

def ask_file(update: Update, context: CallbackContext):
    user_data["comment_id"] = update.message.text
    update.message.reply_text("Message file send karo:")
    return ASK_FILE

def ask_delay(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    file_path = "messages.txt"
    file.download(file_path)
    
    with open(file_path, "r", encoding="utf-8") as f:
        user_data["messages"] = [line.strip() for line in f.readlines()]

    update.message.reply_text("Kitne seconds ka delay chahiye?")
    return ASK_DELAY

def start_reply(update: Update, context: CallbackContext):
    user_data["delay"] = int(update.message.text)
    update.message.reply_text("Bot comments reply karna shuru kar raha hai!")

    while True:
        for message in user_data["messages"]:
            for token in user_data["tokens"]:
                headers = {"Authorization": f"Bearer {token}"}
                data = {
                    "message": message,
                    "comment_id": user_data["comment_id"]
                }
                response = requests.post("https://graph.facebook.com/v12.0/{comment-id}/comments", headers=headers, data=data)

                if response.status_code == 200:
                    update.message.reply_text(f"Comment sent: {message}")
                else:
                    update.message.reply_text(f"Error: {response.text}")

                time.sleep(user_data["delay"])  # Delay before next comment

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Process cancel kar diya gaya.")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_TOKENS: [MessageHandler(Filters.text & ~Filters.command, ask_url)],
            ASK_URL: [MessageHandler(Filters.text & ~Filters.command, ask_comment_id)],
            ASK_COMMENT_ID: [MessageHandler(Filters.text & ~Filters.command, ask_file)],
            ASK_FILE: [MessageHandler(Filters.document, ask_delay)],
            ASK_DELAY: [MessageHandler(Filters.text & ~Filters.command, start_reply)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
