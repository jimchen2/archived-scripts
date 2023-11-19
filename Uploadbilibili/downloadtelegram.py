import os
import asyncio
import datetime

from telethon import TelegramClient, events

# Use your own API ID and hash from https://my.telegram.org
api_id = 21302408  # Your API ID
api_hash = 'd9264adaabf488ea1601f5f55083d879'  # Your API hash

# The channel to download videos from
channel_url = 'kamilavalieva26official'
channel_url='fiejbz'
# Set download path to ~/Downloads
download_path = os.path.expanduser('~/Videos/')

# Ensure the download path exists
os.makedirs(download_path, exist_ok=True)

# Define the event handler
async def handler(event):
    if event.video:
        # Create a unique file name using current timestamp
        unique_filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".mp4"
        # Specify the full path where the video will be saved
        path = os.path.join(download_path, unique_filename)
        
        # Download video files to specified path
        downloaded_path = await event.download_media(file=path)
        print(f"Downloaded video to {downloaded_path}")


# Connect to the client and handle incoming video messages
async def main():
    # 'anon' will be replaced by your phone number for a named session
    async with TelegramClient('15109265354', api_id, api_hash) as client:
        await client.start()
        print("Client Created")
        # Ensure you're authorized
        if await client.is_user_authorized() is False:
            await client.send_code_request(phone)
            try:
                await client.sign_in(phone, input('Enter the code: '))
            except SessionPasswordNeededError:
                await client.sign_in(password=input('Password: '))
        client.add_event_handler(handler, events.NewMessage(chats=channel_url))
        await client.run_until_disconnected()

# This check ensures that the following code only runs if the script is executed directly (not imported)
if __name__ == '__main__':
    # Proper way to run the async main function
    asyncio.run(main())

