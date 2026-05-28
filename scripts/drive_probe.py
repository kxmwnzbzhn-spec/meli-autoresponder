import os, json, sys
from google.oauth2.credentials import Credentials as UC
from google.oauth2 import service_account as SA
from googleapiclient.discovery import build

FOLDER = "1aIDN3iq6zwCacL57iamptvQCPoSDyRbL"
SCOPES = ["https://www.googleapis.com/auth/drive"]

print("=== OAuth test ===")
try:
    creds = UC(token=None, refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
               token_uri="https://oauth2.googleapis.com/token",
               client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
               client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
               scopes=SCOPES)
    svc = build("drive","v3",credentials=creds,cache_discovery=False)
    f = svc.files().get(fileId=FOLDER, fields="id,name,driveId,parents", supportsAllDrives=True).execute()
    print("OAUTH_OK:", json.dumps(f))
except Exception as e:
    print("OAUTH_FAIL:", str(e)[:300])

print("\n=== SA test ===")
try:
    sa_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(sa_json)
    print("SA_EMAIL:", info.get("client_email"))
    creds2 = SA.Credentials.from_service_account_info(info, scopes=SCOPES)
    svc2 = build("drive","v3",credentials=creds2,cache_discovery=False)
    f2 = svc2.files().get(fileId=FOLDER, fields="id,name,driveId,parents,capabilities", supportsAllDrives=True).execute()
    print("SA_OK:", json.dumps(f2))
except Exception as e:
    print("SA_FAIL:", str(e)[:300])
