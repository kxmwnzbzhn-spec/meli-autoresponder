import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

creds=Credentials(token=None, refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/drive"])
creds.refresh(Request())
svc=build("drive","v3",credentials=creds,cache_discovery=False)
FID=os.environ["FILE_ID"]
svc.files().update(fileId=FID, body={"trashed":True}, supportsAllDrives=True).execute()
print(f"✓ trashed: {FID}")
