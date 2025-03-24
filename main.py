import requests
import time
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Telegram Bot Token (Replace with your own bot token)
TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

# States for conversation
TOKEN_COUNT, TIME_DELAY, MESSAGE_FILE, POST_URL, TARGET_COMMENT = range(5)

# Store user inputs
user_data = {}

# Function to start bot
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("👋 Welcome! Kitne Facebook Tokens Use Karne Hain?")
    return TOKEN_COUNT

# Step 1: Get number of tokens
def get_token_count(update: Update, context: CallbackContext) -> int:
    user_data["token_count"] = int(update.message.text)
    update.message.reply_text("⏳ Time Delay (seconds) Kitna Rakhna Hai?")
    return TIME_DELAY

# Step 2: Get time delay
def get_time_delay(update: Update, context: CallbackContext) -> int:
    user_data["time_delay"] = int(update.message.text)
    update.message.reply_text("📁 Message File Path Send Karo:")
    return MESSAGE_FILE

# Step 3: Get message file path
def get_message_file(update: Update, context: CallbackContext) -> int:
    user_data["message_file"] = update.message.text
    update.message.reply_text("📌 Facebook Post URL Send Karo:")
    return POST_URL

# Step 4: Get Facebook Post URL
def get_post_url(update: Update, context: CallbackContext) -> int:
    user_data["post_url"] = update.message.text
    update.message.reply_text("💬 Jis Comment Pe Reply Karna Hai, Wo Comment Send Karo:")
    return TARGET_COMMENT

# Step 5: Get target comment and start replying
def get_target_comment(update: Update, context: CallbackContext) -> int:
    user_data["target_comment"] = update.message.text
    update.message.reply_text("🚀 Bot Start Ho Raha Hai...")

    # Call function to start replying
    start_comment_reply()

    return ConversationHandler.END

# Function to read messages from file
def read_messages(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file.readlines() if line.strip()]

# Function to reply to comment
def reply_to_comment(access_token, comment_id, message):
    url = f"https://graph.facebook.com/v18.0/{comment_id}/comments"
    data = {"message": message, "access_token": access_token}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        print(f"✅ Successfully replied: {message}")
    else:
        print(f"❌ Error: {response.json()}")

# Function to start replying process
def start_comment_reply():
    tokens = ["YOUR_FB_TOKEN_1", "YOUR_FB_TOKEN_2"]  # Add more tokens if needed
    messages = read_messages(user_data["message_file"])
    delay = user_data["time_delay"]
    post_url = user_data["post_url"]
    target_comment = user_data["target_comment"]

    if not messages:
        print("❌ No messages found in the file!")
        return

    # Get Comment ID using Facebook Graph API
    post_id = post_url.split("/")[-1]
    comment_api = f"https://graph.facebook.com/v18.0/{post_id}/comments?access_token={tokens[0]}"
    response = requests.get(comment_api)

    if response.status_code == 200:
        comments = response.json().get("data", [])
        comment_id = None

        for comment in comments:
            if comment["message"] == target_comment:
                comment_id = comment["id"]
                break

        if comment_id:
            print(f"✅ Found Comment ID: {comment_id}")
        else:
            print("❌ Comment not found!")
            return
    else:
        print("❌ Error fetching comments:", response.json())
        return

    # Start replying to the comment
    token_index = 0
    while True:
        current_token = tokens[token_index]
        message = random.choice(messages)

        reply_to_comment(current_token, comment_id, message)
        time.sleep(delay)

        # Switch token if needed
        token_index = (token_index + 1) % len(tokens)

# Telegram bot handlers
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOKEN_COUNT: [MessageHandler(Filters.text & ~Filters.command, get_token_count)],
            TIME_DELAY: [MessageHandler(Filters.text & ~Filters.command, get_time_delay)],
            MESSAGE_FILE: [MessageHandler(Filters.text & ~Filters.command, get_message_file)],
            POST_URL: [MessageHandler(Filters.text & ~Filters.command, get_post_url)],
            TARGET_COMMENT: [MessageHandler(Filters.text & ~Filters.command, get_target_comment)],
        },
        fallbacks=[],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
