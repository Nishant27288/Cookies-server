import requests
import time
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Telegram Bot Token (Replace with your bot token)
TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

# States for conversation
TOKEN_COUNT, TIME_DELAY, MESSAGE_FILE, POST_URL, TARGET_COMMENT, TOKEN_LIST = range(6)

# Store user inputs
user_data = {}

# Function to start bot
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("👋 Welcome! Kitne Facebook Tokens Use Karne Hain?")
    return TOKEN_COUNT

# Step 1: Get number of tokens
async def get_token_count(update: Update, context: CallbackContext) -> int:
    user_data["token_count"] = int(update.message.text)
    await update.message.reply_text(f"👍 {user_data['token_count']} Tokens Chahiye. Ab Time Delay (seconds) Kitna Rakhna Hai?")
    return TIME_DELAY

# Step 2: Get time delay
async def get_time_delay(update: Update, context: CallbackContext) -> int:
    user_data["time_delay"] = int(update.message.text)
    await update.message.reply_text("📁 Message File Path Send Karo:")
    return MESSAGE_FILE

# Step 3: Get message file path
async def get_message_file(update: Update, context: CallbackContext) -> int:
    user_data["message_file"] = update.message.text
    await update.message.reply_text("📌 Facebook Post URL Send Karo:")
    return POST_URL

# Step 4: Get Facebook Post URL
async def get_post_url(update: Update, context: CallbackContext) -> int:
    user_data["post_url"] = update.message.text
    await update.message.reply_text("💬 Jis Comment Pe Reply Karna Hai, Wo Comment Send Karo:")
    return TARGET_COMMENT

# Step 5: Get target comment
async def get_target_comment(update: Update, context: CallbackContext) -> int:
    user_data["target_comment"] = update.message.text
    await update.message.reply_text("⚙️ Facebook Tokens List Send Karo (Comma Separated):")
    return TOKEN_LIST

# Step 6: Process Tokens List and Start Replying
async def process_tokens(update: Update, context: CallbackContext) -> int:
    # Get the list of tokens from user
    tokens = update.message.text.split(",")
    tokens = [token.strip() for token in tokens]  # Remove extra spaces

    # Save the tokens to user_data
    user_data["tokens"] = tokens
    await update.message.reply_text(f"✅ Tokens Successfully Saved: {', '.join(tokens)}\n\n🚀 Bot Start Ho Raha Hai...")

    # Start the comment reply process with tokens
    await start_comment_reply(tokens)

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
async def start_comment_reply(tokens):
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
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOKEN_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token_count)],
            TIME_DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time_delay)],
            MESSAGE_FILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message_file)],
            POST_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_post_url)],
            TARGET_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_target_comment)],
            TOKEN_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_tokens)],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
