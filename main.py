import requests
import random
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 🔹 Telegram Bot Token (Replace with your token)
TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

# 🔹 Sticker Styles List
STICKER_STYLES = ["bold", "italic", "outline", "shadow", "neon", "3d", "colorful"]

# 🔹 Function to generate sticker (Replace with actual API if needed)
def generate_sticker(text, style):
    return f"https://example.com/sticker/{style}/{text}.png"

# 🔹 Function to send the sticker as a Facebook comment
def send_facebook_comment(access_token, post_id, sticker_url):
    url = f"https://graph.facebook.com/v17.0/{post_id}/comments"
    payload = {"access_token": access_token, "message": sticker_url}

    response = requests.post(url, json=payload)
    return response.status_code == 200

# 🔹 Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Welcome! Please send your Facebook tokens one by one.")
    context.user_data["tokens"] = []
    return "TOKEN_INPUT"

# 🔹 Collect Tokens
async def collect_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tokens"].append(update.message.text)

    await update.message.reply_text(f"✅ Token saved! Send another token or type /done when finished.")
    return "TOKEN_INPUT"

# 🔹 Finish Token Input
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data["tokens"]:
        await update.message.reply_text("❌ No tokens entered. Please start again with /start.")
        return

    await update.message.reply_text("✅ All tokens saved! Now send the Facebook post URL.")
    return "POST_INPUT"

# 🔹 Collect Post ID
async def collect_post_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["post_id"] = update.message.text
    await update.message.reply_text("✅ Post ID saved! Now enter the delay time (in seconds).")
    return "DELAY_INPUT"

# 🔹 Collect Delay
async def collect_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        delay = int(update.message.text)
        context.user_data["delay"] = delay
        await update.message.reply_text("✅ Delay time set! Now send the text you want to convert into a sticker.")
        return "TEXT_INPUT"
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return "DELAY_INPUT"

# 🔹 Generate & Post Sticker
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    style = random.choice(STICKER_STYLES)
    sticker_url = generate_sticker(user_text, style)

    post_id = context.user_data["post_id"]
    tokens = context.user_data["tokens"]
    delay = context.user_data["delay"]

    for token in tokens:
        success = send_facebook_comment(token, post_id, sticker_url)

        if success:
            await update.message.reply_text(f"✅ Sticker '{user_text}' posted successfully!")
            time.sleep(delay)
        else:
            await update.message.reply_text(f"❌ Failed with token {token[:10]}... Switching token.")

    await update.message.reply_text("🎉 All stickers posted! Send another text or type /stop to exit.")

# 🔹 Stop Command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Stopping the process.")
    return "STOP"

# 🔹 Main Function
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("stop", stop))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_tokens))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_post_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_delay))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()

if __name__ == "__main__":
    main()
