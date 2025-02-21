from telethon import TelegramClient, events
import os, json, time, re

# Telegram API credentials (Get these from https://my.telegram.org/)
API_ID = "21552265"
API_HASH = "1c971ae7e62cc416ca977e040e700d09"
BOT_TOKEN = "7772588358:AAHwmx5uXG6m9t-hTccrcV8ftFjr_Ay8vJ0"

# Destination group ID where downloaded videos should be sent
DESTINATION_GROUP_ID = -1002136294449  # Replace with your group ID

# Admin users who can manage the bot
ADMIN_USERS = {7256617868, 7408008545}  # Replace with Telegram Admin User IDs

# Whitelist of users allowed to download
WHITELIST_USERS = {123456789, 987654321}  # Replace with Telegram User IDs

# Limitations per user per day
DAILY_LIMIT = 3  # Maximum downloads allowed per user per day
USER_DOWNLOADS = {}  # Dictionary to track user downloads
LOG_FILE = "download_log.json"

# Load previous logs if available
def load_logs():
    global USER_DOWNLOADS
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            USER_DOWNLOADS = json.load(f)

# Save logs to a file
def save_logs():
    with open(LOG_FILE, "w") as f:
        json.dump(USER_DOWNLOADS, f)

# Initialize the Telegram client
client = TelegramClient("session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Send start message when bot starts
async def send_start_message():
    owner_message = "😊 SAVE RESTRICTED CONTENT SAVE BOT 😊\n\nBOT OWNER = @RU_DRA_65\nOWNER = @KAARTIK_NISHAD"
    try:
        await client.send_message(DESTINATION_GROUP_ID, owner_message)
    except Exception as e:
        print(f"Error sending start message: {e}")

@client.on(events.NewMessage(pattern='/addwhitelist (\d+)'))
async def add_whitelist(event):
    sender = await event.get_sender()
    if sender.id in ADMIN_USERS:  # Only allow admins to add users
        new_user_id = int(event.pattern_match.group(1))
        WHITELIST_USERS.add(new_user_id)
        await event.reply(f"✅ User {new_user_id} has been added to the whitelist!")
    else:
        await event.reply("❌ You are not authorized to add users to the whitelist!")

# Function to download media from link
async def download_from_link(event, link):
    match = re.search(r"t\.me/(c/)?([-\d]+)/?(\d+)?", link)
    if not match:
        await event.reply("❌ Invalid Telegram link!")
        return
    
    chat_id = int(match.group(2)) if match.group(1) else -1000000000000 + int(match.group(2))
    message_id = int(match.group(3)) if match.group(3) else None
    
    if not message_id:
        await event.reply("❌ Message ID not found in link!")
        return
    
    try:
        message = await client.get_messages(chat_id, ids=message_id)
        if message.video or message.audio:
            file_path = await message.download_media()
            await client.send_file(DESTINATION_GROUP_ID, file_path, caption=f"📩 Forwarded from {chat_id}")
            await client.send_file(event.chat_id, file_path, caption="✅ Your requested media")
            os.remove(file_path)
            await event.reply("✅ Downloaded & forwarded successfully!")
        else:
            await event.reply("❌ No media found in the message!")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    user_id = sender.id
    
    # Check if user is in whitelist
    if user_id not in WHITELIST_USERS:
        await event.reply("❌ You are not authorized to download content!")
        return
    
    # Reset daily limit at midnight
    current_time = time.time()
    if user_id in USER_DOWNLOADS and current_time - USER_DOWNLOADS[user_id]["timestamp"] > 86400:
        USER_DOWNLOADS[user_id] = {"count": 0, "timestamp": current_time}
    
    # Check daily download limit
    if user_id in USER_DOWNLOADS and USER_DOWNLOADS[user_id]["count"] >= DAILY_LIMIT:
        await event.reply("⚠️ You have reached your daily download limit!")
        return
    
    # Check for video or audio in message
    if event.video or event.audio:
        print(f"Downloading file from {sender.username or sender.id}")
        file_path = await event.download_media()
        await client.send_file(DESTINATION_GROUP_ID, file_path, caption=f"📩 Forwarded from {sender.username or user_id}")
        await client.send_file(event.chat_id, file_path, caption="✅ Your requested media")
        os.remove(file_path)
        await event.reply("✅ Your video/audio has been downloaded and shared to the group & to you personally.")
    
    # Check for Telegram link in message
    elif "t.me/" in event.raw_text:
        await download_from_link(event, event.raw_text)

# Load logs on startup
load_logs()
print("Bot is running...")

# Run startup function to send message
with client:
    client.loop.run_until_complete(send_start_message())
    client.run_until_disconnected()
