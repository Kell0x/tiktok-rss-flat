import os
import asyncio
import csv
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
from TikTokApi import TikTokApi
import config
import requests
import xml.etree.ElementTree as ET

# Custom Domain
ghPagesURL = config.ghPagesURL

api = TikTokApi()

ms_token = os.environ.get(
    "MS_TOKEN", None
)

last_update = datetime.fromisoformat(os.environ.get("LAST_UPDATE", str).replace("Z", "+00:00"))

token = os.environ.get(
    "token", str
)

channel_id = os.environ.get(
    "channel_id", str
)

async def user_videos():

    with open('subscriptions.csv') as f:
        cf = csv.DictReader(f, fieldnames=['username'])
        for row in cf:
            user = row['username']

            print(f'Running for user \'{user}\'')

            fg = FeedGenerator()
            fg.id('https://www.tiktok.com/@' + user)
            fg.title(user + ' TikTok')
            fg.link( href=ghPagesURL + 'rss/' + user + '.xml', rel='self' )
            fg.language('en')

            # Set the last modification time for the feed to be the most recent post, else now.
            updated=None
            
            async with TikTokApi() as api:
                await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, headless=False)
                ttuser = api.user(user)
                user_data = await ttuser.info()
                print(user_data)

                async for video in ttuser.videos(count=10):
                    fe = fg.add_entry()
                    link = "https://tiktok.com/@" + user + "/video/" + video.id
                    fe.id(link)
                    ts = datetime.fromtimestamp(video.as_dict['createTime'], timezone.utc)
                    fe.published(ts)
                    fe.updated(ts)
                    updated = max(ts, updated) if updated else ts
                    if video.as_dict['desc']:
                        fe.title(video.as_dict['desc'][0:255])
                    else:
                        fe.title("No Title")
                    fe.link(href=link)
                    if video.as_dict['desc']:
                        fe.description(video.as_dict['desc'][0:255])
                    else:
                        fe.description( "No Description")        
                fg.updated(updated)
                fg.atom_file('rss/' + user + '.xml', pretty=True) # Write the RSS feed to a file

def check_rss():
    messages = []
    url = f"https://kell0x.github.io/tiktok-rss-flat/rss/superearthupdates"
    response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)

        for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
            updated = entry.find('{http://www.w3.org/2005/Atom}updated').text
            title = entry.find('{http://www.w3.org/2005/Atom}title').text
            id_ = entry.find('{http://www.w3.org/2005/Atom}id').text
            
            date_obj = datetime.fromisoformat(updated.replace("Z", "+00:00"))

            if most_recent_date is None or date_obj > most_recent_date:
                messages.append(f"**Message from Super Earth :** \"*{str(title).split('#')[0]}*\"\n{id_.replace('tiktok.com', 'vxtiktok.com')}")
        
        for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
            updated_str = entry.find('{http://www.w3.org/2005/Atom}updated').text
            updated_date = datetime.fromisoformat(updated_str)

            if most_recent_date is None or updated_date > most_recent_date:
                os.environ["LAST_UPDATE"] = updated
        
    return messages

def message_post(token, channel_id, message):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = { "Authorization": f"{token}",  }
    data = { "content": message }
    response = requests.post(url, headers=headers, json=data)
   
    if response.status_code == 200:
        print(f"Message sent successfully : {message}")
    else:
        print(f"Failed to send the message : {message}")
        print(response.text)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(user_videos())
    messages = check_rss()
    for message in messages:
        message_post(token, channel_id, message)
