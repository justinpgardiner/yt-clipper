# from bs4 import BeautifulSoup
# import requests

# soup = BeautifulSoup(requests.get('https://www.youtube.com/@TED/videos').content, 'html.parser')
# print(soup.find_all('a', href=True))
import json
import yt_dlp

from vid_queue import SQLiteQueue

ydl_opts = {
    'quiet': True,
    'skip_download': True,
    "extract_flat": "in_playlist"
}


# queue = SQLiteQueue('vid_links.db')
# # https://www.youtube.com/podcasts/popularshows
# with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#     values = ydl.extract_info ('https://www.youtube.com/@TED', download=False)
#     print(values)
#     for entry in values['entries']:
#         print(entry)
#         if entry['_type'] == 'url' and entry['ie_key'] == 'Youtube':
#             queue.enqueue(entry['url'])
# print(queue.size())
# queue.close()

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    values = ydl.extract_info ('https://www.youtube.com/shorts/V_C8yFL-zVA', download=False)
    with open('output.json', 'w') as file:
        json.dump(values, file, indent=4)
    # # urls = []
    # for entry in values['entries']:
    #     print(entry['url'])