import schedule
import time
from instabot import Bot
import requests
import random
import os
from PIL import Image
from io import BytesIO

# Initialize the bot
bot = Bot()
bot.login(username="memeworld6451", password="Ni$h@nt21")

# Fetching random meme from an API (Imgflip)
def get_random_meme():
    url = 'https://api.imgflip.com/get_memes'
    response = requests.get(url)
    
    if response.status_code == 200:
        memes = response.json()['data']['memes']
        meme = random.choice(memes)  # Choose a random meme
        meme_url = meme['url']
        meme_name = meme['name']
        return meme_url, meme_name
    return None, None

# Download meme image
def download_meme(meme_url):
    response = requests.get(meme_url)
    img = Image.open(BytesIO(response.content))
    
    # Save the meme locally
    meme_filename = 'meme.jpg'
    img.save(meme_filename)
    return meme_filename

# Upload meme to Instagram
def upload_meme_to_instagram(meme_filename, caption):
    bot.upload_photo(meme_filename, caption=caption)
    os.remove(meme_filename)  # Clean up the local file after upload

# Function to schedule meme upload
def post_meme():
    meme_url, meme_name = get_random_meme()
    
    if meme_url:
        print(f"Fetched Meme: {meme_name}")
        
        # Download meme
        meme_filename = download_meme(meme_url)
        
        # Set a random caption (you can use a list of meme captions)
        captions = [
            "This is a hilarious meme!",
            "Who doesn't love a good meme?",
            f"Here's a trending meme: {meme_name}!",
        ]
        caption = random.choice(captions)
        
        # Upload meme to Instagram
        upload_meme_to_instagram(meme_filename, caption)
        print(f"Meme uploaded successfully with caption: {caption}")
    else:
        print("Failed to fetch meme.")

# Scheduling the posts at specific times
def schedule_posts():
    # Schedule posts
    schedule.every().day.at("06:00").do(post_meme)  # 6 AM
    schedule.every().day.at("09:00").do(post_meme)  # 9 AM
    schedule.every().day.at("13:00").do(post_meme)  # 1 PM
    schedule.every().day.at("16:00").do(post_meme)  # 4 PM
    schedule.every().day.at("21:00").do(post_meme)  # 9 PM

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Main function to start the scheduling
def main():
    schedule_posts()

if __name__ == '__main__':
    main()
