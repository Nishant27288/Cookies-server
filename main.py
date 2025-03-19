import requests
import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7629260838:AAE7CiSi3caTmuwHvxlxsMpNW7dCnUnCOJo"

# List of sticker generation styles (for example, fonts, colors, or effects)
STICKER_STYLES = [
    "bold", "italic", "outline", "shadow", "neon", "3d", "colorful"
]

# Define conversation states
TOKEN, POST_URL, DELAY, TEXT_INPUT = range(4)

# Function to generate sticker with different styles
def generate_sticker(text, style):
    # This is where you would call an API or your custom method to generate stickers
    # For this example, we are just creating a URL that pretends to be a generated sticker.
    # You should replace this with a real API or your own image service for sticker generation
    sticker_url = f"https://example.com/sticker/{style}/{text}.png"
    return sticker_url

# Function to send the sticker as a comment on Facebook
def send_facebook_message(access_token, post_url, sticker_url):
    url = f"{post_url}/comments"
    payload = {"access_token": access_token, "message": sticker_url}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return True
    return False

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Please provide your Facebook token.")
    return TOKEN

# Function to handle Facebook token input
async def get_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["access_token"] = update.message.text
    await update.message.reply_text("✅ Token received! Please provide the Post URL.")
    return POST_URL

# Function to handle Post URL input
async def get_post_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["post_url"] = update.message.text
    await update.message.reply_text("✅ Post URL received! Now, please provide the delay in seconds.")
    return DELAY

# Function to handle delay input
async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        delay = int(update.message.text)
        context.user_data["delay"] = delay
        await update.message.reply_text(f"✅ Delay of {delay} seconds set! Please send the text for the sticker.")
        return TEXT_INPUT
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for the delay.")
        return DELAY

# Function to handle text input for sticker generation
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    style = random.choice(STICKER_STYLES)  # Choose a random style for the sticker
    sticker_url = generate_sticker(user_text, style)  # Generate sticker URL with style

    # Get the Facebook token, post URL, and delay from context
    access_token = context.user_data.get("access_token")
    post_url = context.user_data.get("post_url")
    delay = context.user_data.get("delay")

    # Simulate sending sticker via Facebook
    success = send_facebook_message(access_token, post_url, sticker_url)

    if success:
        await update.message.reply_text(f"✅ Sticker with text '{user_text}' sent successfully!")
        await asyncio.sleep(delay)  # Wait for the delay time before responding
    else:
        await update.message.reply_text(f"❌ Failed to send sticker with the provided token.")

    # Return to waiting for text input
    return TEXT_INPUT

# Function to handle the /stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Stopping the process.")
    return ConversationHandler.END

# Main function to start the bot
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Create a conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token)],
            POST_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_post_url)],
            DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay)],
            TEXT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    # Add the conversation handler to the application
    app.add_handler(conversation_handler)

    # Start polling for messages
    app.run_polling()

if __name__ == "__main__":
    main()
