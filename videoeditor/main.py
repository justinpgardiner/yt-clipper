import time
import yt_dlp
import ffmpeg
import pickle
import json
from google import genai
import shutil
from vid_queue import SQLiteQueue
import traceback
import logging
import os
import google.auth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from googleapiclient.errors import ResumableUploadError
from animate import add_asmr


logging.basicConfig(
    filename='clipper.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.pickle"

def get_authenticated_service():
    creds = None

    # Load cached credentials if available
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, run login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
            creds = flow.run_local_server(port=8080, prompt='consent')

        # Save the credentials for future use
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)

def upload_video(file_path, title, description, category_id="22", privacy_status="public"):
    youtube = get_authenticated_service()
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print("Upload complete. Video ID:", response["id"])
    

def clip_video(url):
    files_to_clean = []
    limit = False
    try:
        # Download video from yt
        logging.info("Downloading " + url + " from YouTube...")
        id = url[url.index("=") + 1:]
        test_opts = {
            'quiet': True,
            'skip_download': True,
        }

        with yt_dlp.YoutubeDL(test_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info.get("subtitles"):
                return
        ydl_opts = {
            'outtmpl': id + '.%(ext)s',
            'writesubtitles': True,
            'subtitleslangs': ['en'],
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Get Gemini opinion on how to clip
        # Want to get a video title, description, and hashtags
        print("Gemini...")
        logging.info("Prompting Gemini for clips for " + id)
        video_file = id + ".mp4"
        subtitle_file = id + ".en.vtt"
        files_to_clean.append(video_file)
        files_to_clean.append(subtitle_file)
        client = genai.Client(api_key=os.environ.load('API_KEY'))
        with open(subtitle_file) as f:
            subs = f.read()
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=
                    "Based on these subtitles: " + subs + ", output between 5 and 20 raw json formatted objects with other no explanation OR MARKDOWN (don't do json```) representing the most cohesive clips from this video with length from 30 seconds up to 90 seconds, only separated by ';', with the following properties: title, description, hashtags, start_time, duration. Start time and duration in format 'XX:XX:XX.XXX' Use this as an example for formatting, don't change the formatting at all."
                )
                clip_data = [json.loads(clip) for clip in response.text.split(";")]
            except Exception as e:
                logging.error("Gemini failed, cooling down..." + e['message'])
                time.sleep(10)
                return
        subs_list = {content[:12] : content for content in subs.split('\n\n')}

        # Go through each clip
        for i, clip in enumerate(clip_data):
            logging.info('Building clip "' + clip['title'])
            clip_id = id + str(i)
            shutil.copy('template.en.ass', clip_id + '.en.ass')
            # Need to format the dialague to fit the clip and look better
            dialogue = format_subtitle_dialogue(clip['start_time'], clip['duration'], subs_list)
            with open(clip_id + '.en.ass', 'a') as f:
                f.write("\n" + dialogue)
            # Compile the clip
            sub_path = clip_id + ".en.ass"
            ffmpeg.input(video_file).output(
                clip_id + ".mp4",
                ss=clip['start_time'], 
                t=clip['duration'],
                vf=f"setpts=PTS-STARTPTS,scale=-1:1280,crop=720:1280,subtitles={sub_path}",
                af="asetpts=PTS-STARTPTS",
                vcodec="libx264",
                acodec="aac",
                crf=18,
                fflags='+genpts',
                avoid_negative_ts='make_zero',
            ).run()
            files_to_clean.append(clip_id + ".mp4")
            files_to_clean.append(clip_id + ".en.ass")
            add_asmr(clip_id)
            # logging.info('Uploading clip "' + clip['title'])
            # upload_video(
            #     file_path= clip_id + ".mp4",
            #     title=clip['title'],
            #     description=clip['description'] + '\n#shorts ' + str(clip['hashtags'])
            # )
    except ResumableUploadError as rue:
        if rue['reason'] == 'uploadLimitExceeded':
            logging.warning("Limit for posting today reached, ending program")
            limit = True
        else:
            logging.warning("Some error occured: " + rue['message'])
    except Exception as e:
        logging.warning("Some error occured: " + e['message'])
    finally:
        # for file in files_to_clean:
        #     os.remove(file)
        return limit


def format_subtitle_dialogue(start, duration, subs_list):
    end = ms_to_time(time_to_ms(start) + time_to_ms(duration))
    key_list = list(subs_list.keys())
    index = key_list.index(start)
    dialogue = ""
    while index < len(key_list) - 1 and time_to_ms(key_list[index]) < time_to_ms(end):
        key = key_list[index]
        temp_start = key
        temp_end = subs_list[key][subs_list[key].index('--> ') + 4: subs_list[key].index('--> ') + 16]
        temp_content = subs_list[key][subs_list[key].index('\n') + 1:]
        dialogue += f"Dialogue: 0,{ms_to_time(time_to_ms(temp_start))},{ms_to_time(time_to_ms(temp_end))},Default,,0,0,0,,{temp_content}".replace('\n', '\\N') + "\n"
        index += 1
    return dialogue

def time_to_ms(t):
    h, m, s = t.split(':')
    s, ms = s.split('.')
    total_ms = (int(h)*3600 + int(m)*60 + int(s)) * 1000 + int(ms)
    return total_ms

def ms_to_time(ms):
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    cs = ms // 10
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

if __name__ == '__main__':
    # queue = SQLiteQueue('vid_links.db')
    # size = queue.size()
    # # limit = False
    # # while not limit and queue.peek() is not None:
    clip_video('https://www.youtube.com/watch?v=cjG0m9QUF34')
    # # logging.info("Uploaded all clips from " + queue.peek() + ", dequeuing")
    # # queue.dequeue()
    # add_asmr('rNxC16mlO600')