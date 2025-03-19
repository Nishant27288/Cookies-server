import requests
import random
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7629260838:AAE7CiSi3caTmuwHvxlxsMpNW7dCnUnCOJo"

# List of sticker generation styles (for example, fonts, colors, or effects)
STICKER_STYLES = [
    "bold", "italic", "outline", "shadow", "neon", "3d", "colorful"
]

# Function to generate sticker with different styles
def generate_sticker(text, style):
    # This is where you would call an API or your custom method to generate stickers
    # For this example, we are just creating a URL that pretends to be a generated sticker.
    # You should replace this with a real API or your own image service for sticker generation
    sticker_url = f"https://example.com/sticker/{style}/{text}.png"
    return sticker_url

# Function to send the sticker as a comment on Facebook
def send_facebook_message(access_token, chat_id, sticker_url):
    url = f"https://graph.facebook.com/v15.0/{chat_id}/comments"
    payload = {"access_token": access_token, "message": sticker_url}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return True
    return False

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Please send the text you want to convert into a sticker.")
    return "TEXT_INPUT"

# Function to handle the sticker generation and posting
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    style = random.choice(STICKER_STYLES)  # Choose a random style for the sticker
    sticker_url = generate_sticker(user_text, style)  # Generate sticker URL with style

    # Simulating sending sticker via Facebook (you'll replace it with actual logic)
    # Get Facebook tokens from the user
    tokens = context.user_data.get("tokens", [])
    chat_id = context.user_data.get("chat_id")

    if not tokens or not chat_id:
        await update.message.reply_text("❌ Missing Facebook token or chat ID.")
        return

    # Loop through tokens and send the sticker
    for token in tokens:
        success = send_facebook_message(token, chat_id, sticker_url)

        if success:
            await update.message.reply_text(f"✅ Sticker with text '{user_text}' sent successfully!")
        else:
            await update.message.reply_text(f"❌ Failed to send sticker with token {token[:10]}... switching token.")

# Function to get the tokens from the user
async def get_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tokens"] = []
    await update.message.reply_text("🤖 How many Facebook tokens do you want to use? Send the number.")
    return "TOKEN_COUNT"

# Handle number of tokens
async def get_token_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        token_count = int(update.message.text)
        if token_count < 1:
            raise ValueError
        context.user_data["token_count"] = token_count
        await update.message.reply_text(f"✅ Send {token_count} tokens one by one.")
        return "GET_TOKENS"
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number (1 or more).")
        return "TOKEN_COUNT"

# Function to receive tokens from the user
async def get_tokens_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tokens"].append(update.message.text)

    token_count = context.user_data["token_count"]
    if len(context.user_data["tokens"]) < token_count:
        await update.message.reply_text(f"✅ Token {len(context.user_data['tokens'])} saved. Send the next one.")
        return "GET_TOKENS"

    await update.message.reply_text("✅ All tokens saved! Now enter the **Facebook Chat ID**:")
    return "CHAT_ID"

# Get chat ID
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["chat_id"] = update.message.text
    await update.message.reply_text("✅ Chat ID saved! Now send your text to create a sticker.")
    return "TEXT_INPUT"

# Function to handle the /stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Stopping the process.")
    return "STOP"

# Main function to start the bot
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handler to process the start command
    app.add_handler(CommandHandler("start", start))

    # Handler to receive tokens from the user
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens_input))

    # ConversationHandler
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("get_tokens", get_tokens))
    app.add_handler(CommandHandler("get_token_count", get_token_count))
    
    # Main function to start the process
    app.run_polling()

if __name__ == "__main__":
    main()
