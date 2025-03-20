import requests
import random
import time
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

# List of sticker styles
STICKER_STYLES = ["bold", "italic", "outline", "shadow", "neon", "3d", "colorful"]

# Dictionary to store user data
user_data = {}

# Function to generate a sticker (Dummy URL, replace with real API)
def generate_sticker(text, style):
    return f"https://example.com/sticker/{style}/{text}.png"

# Function to send sticker comment to Facebook
def send_facebook_comment(access_token, post_id, sticker_url):
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {"access_token": access_token, "message": sticker_url}
    response = requests.post(url, json=payload)
    return response.status_code == 200

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {}
    await update.message.reply_text("🤖 Send the number of Facebook tokens you want to use.")
    return "TOKEN_COUNT"

# Get token count
async def get_token_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        token_count = int(update.message.text)
        if token_count < 1:
            raise ValueError
        user_data[update.effective_user.id]["token_count"] = token_count
        user_data[update.effective_user.id]["tokens"] = []
        await update.message.reply_text(f"✅ Send {token_count} tokens one by one.")
        return "GET_TOKENS"
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number (1 or more).")
        return "TOKEN_COUNT"

# Receive tokens
async def get_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["tokens"].append(update.message.text)
    if len(user_data[user_id]["tokens"]) < user_data[user_id]["token_count"]:
        await update.message.reply_text(f"✅ Token {len(user_data[user_id]['tokens'])} saved. Send the next one.")
        return "GET_TOKENS"
    await update.message.reply_text("✅ All tokens saved! Now send the Facebook post URL.")
    return "POST_URL"

# Receive post URL
async def get_post_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["post_url"] = update.message.text
    await update.message.reply_text("✅ Post URL saved! Now enter the delay (in seconds).")
    return "DELAY"

# Receive delay time
async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        delay = int(update.message.text)
        user_data[update.effective_user.id]["delay"] = delay
        await update.message.reply_text("✅ Delay saved! Now enter the text for the sticker comment.")
        return "STICKER_TEXT"
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number.")
        return "DELAY"

# Receive sticker text and start commenting
async def get_sticker_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    style = random.choice(STICKER_STYLES)
    sticker_url = generate_sticker(text, style)
    post_url = user_data[user_id]["post_url"]
    tokens = user_data[user_id]["tokens"]
    delay = user_data[user_id]["delay"]

    for token in tokens:
        success = send_facebook_comment(token, post_url, sticker_url)
        if success:
            await update.message.reply_text(f"✅ Sticker comment posted successfully!")
        else:
            await update.message.reply_text(f"❌ Failed to comment with token {token[:10]}... Trying next.")
        time.sleep(delay)

    await update.message.reply_text("✅ All sticker comments sent!")
    return "DONE"

# Main function
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_token_count))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_post_url))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_sticker_text))

    app.run_polling()

if __name__ == "__main__":
    main()
