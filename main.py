import logging
import random
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7635741820:AAGAks8tA7qTJb5W6lSOpE1uMqG2Y9POvdg"

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Variables
tokens = []
post_url = ""
target_comment = ""
comment_id = ""
messages = []
delay = 0
step = 0  # Step to track the current stage of setup


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("👋 Welcome! Mujhe setup karne ke liye /setup likho.")


async def setup(update: Update, context: CallbackContext):
    global step
    step = 1
    await update.message.reply_text("🔹 Kitne tokens use karne hai? (1 ya more)\n\nExample: token1 token2 token3")
    return step


async def get_tokens(update: Update, context: CallbackContext):
    global tokens, step
    tokens_input = update.message.text.strip()

    if tokens_input:
        tokens = tokens_input.split()
        step = 2  # Move to next step after tokens are received
        await update.message.reply_text(f"✅ {len(tokens)} tokens save ho gaye. \n🔹 Ab Post URL bhejo:")
        return step
    else:
        await update.message.reply_text("⚠️ Tokens provide karo, space se separate karke.")
        return step


async def get_post_url(update: Update, context: CallbackContext):
    global post_url, step
    post_url = update.message.text
    step = 3  # Move to next step after URL is received
    await update.message.reply_text("✅ Post URL save ho gaya.\n🔹 Ab Jis Comment Pe Reply Karna Hai, Wo Comment Paste Karo:")
    return step


async def get_target_comment(update: Update, context: CallbackContext):
    global target_comment, comment_id, step
    target_comment = update.message.text
    comment_id = get_comment_id_from_text(target_comment)

    if comment_id:
        step = 4  # Move to next step after comment ID is found
        await update.message.reply_text(f"✅ Comment ID `{comment_id}` mil gaya. \n🔹 Ab Message file bhejo:")
        return step
    else:
        await update.message.reply_text("⚠️ Comment ID nahi mila! Ensure karo ke tumne sahi comment diya hai.")
        return step


async def get_message_file(update: Update, context: CallbackContext):
    global messages, step
    file_id = update.message.document.file_id
    new_file = await context.bot.get_file(file_id)
    file_path = "messages.txt"
    await new_file.download_to_drive(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        messages = [line.strip() for line in f.readlines() if line.strip()]

    step = 5  # Move to next step after message file is received
    await update.message.reply_text(f"✅ {len(messages)} messages load ho gaye. \n🔹 Ab delay (seconds) bhejo:")
    return step


async def get_delay(update: Update, context: CallbackContext):
    global delay, step
    try:
        delay = int(update.message.text)
        step = -1  # Final step, ready to reply
        await update.message.reply_text("✅ Setup Complete! Bot ab reply karega. 🚀 /start_reply use karo.")
    except ValueError:
        await update.message.reply_text("⚠️ Galat input! Delay sirf number me likho.")
    return step


async def start_reply(update: Update, context: CallbackContext):
    global tokens, post_url, comment_id, messages, delay, step

    if not tokens or not post_url or not comment_id or not messages or delay <= 0:
        await update.message.reply_text("⚠️ Setup incomplete hai! Pehle /setup complete karo.")
        return

    await update.message.reply_text("✅ Bot ab reply kar raha hai...")

    token_index = 0
    while True:
        token = tokens[token_index % len(tokens)]
        message = random.choice(messages)

        post_comment(token, post_url, comment_id, message)

        token_index += 1
        time.sleep(delay)


def get_comment_id_from_text(comment_text):
    """
    Yeh function Facebook Graph API se comment ID dhoondhne ki koshish karega
    agar original post aur comment text diya gaya ho.
    """
    global post_url, tokens
    if not tokens:
        return None

    # Pehla token use karke try karega
    token = tokens[0]

    # Post ID extract karo
    post_id = post_url.split("/")[-1].split("?")[0]  # URL se post ID nikalna

    api_url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
    params = {"access_token": token}

    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        comments = response.json().get("data", [])
        for comment in comments:
            if comment["message"].strip() == comment_text.strip():
                return comment["id"]  # Agar match mil gaya toh ID return karo

    return None


def post_comment(token, post_url, comment_id, message):
    api_url = f"https://graph.facebook.com/v18.0/{comment_id}/comments"
    payload = {"message": message, "access_token": token}

    response = requests.post(api_url, data=payload)
    if response.status_code == 200:
        logger.info(f"✅ Successfully replied: {message}")
    else:
        logger.error(f"❌ Error: {response.text}")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setup", setup))
    app.add_handler(CommandHandler("start_reply", start_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_post_url))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_target_comment))
    app.add_handler(MessageHandler(filters.Document.ALL, get_message_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay))

    logger.info("🤖 Bot Started...")
    app.run_polling()


if __name__ == "__main__":
    main()
