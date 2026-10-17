
import os
import glob
from datetime import date

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

client_id = os.environ["YOUTUBE_CLIENT_ID"]
client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]
refresh_token = os.environ["YOUTUBE_REFRESH_TOKEN"]

credentials = Credentials(
    token=None,
    refresh_token=refresh_token,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret,
    scopes=SCOPES,
)

credentials.refresh(Request())

youtube = build("youtube", "v3", credentials=credentials)

videos = sorted(glob.glob("output/*.mp4"))

if not videos:
    raise FileNotFoundError("No MP4 video found in output/")

video_path = videos[-1]

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": f"Daily Motivation | {date.today().isoformat()}",
            "description": (
                "Daily Hindi-English motivational typography. "
                "#Motivation #Shorts #SahinTypography"
            ),
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False,
        },
    },
    media_body=MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
    ),
)

response = request.execute()
print("YouTube upload successful. Video ID:", response["id"])
