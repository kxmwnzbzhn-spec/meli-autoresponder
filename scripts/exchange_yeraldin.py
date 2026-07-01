"""Exchange OAuth code -> store tokens as YERALDIN in Supabase"""
import os, requests, json, sys

APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
CODE=os.environ["OAUTH_CODE"]
REDIRECT="https://meli-webhook.elite-market-1779161651.workers.dev/oauth/callback"
SB_URL=os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY=os.environ["SUPABASE_SERVICE_KEY"]
ACCOUNT=os.environ.get("ACCOUNT","YERALDIN")

SBH={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=representation"}

r=requests.post("https://api.mercadolibre.com/oauth/token",data={
  "grant_type":"authorization_code","client_id":APP_ID,"client_secret":APP_SECRET,
  "code":CODE,"redirect_uri":REDIRECT
},timeout=25)
print(f"[oauth] status={r.status_code}",flush=True)
if r.status_code>=300:
  print(r.text[:600],flush=True)
  sys.exit(1)
j=r.json()
AT=j["access_token"]; RT=j["refresh_token"]; UID=j["user_id"]

me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
NICK=me.get("nickname","?")
FN=me.get("first_name","")
LN=me.get("last_name","")
print(f"[user] uid={UID} nickname={NICK} name={FN} {LN}",flush=True)

# Delete existing if any
requests.delete(f"{SB_URL}/rest/v1/meli_tokens?account=eq.{ACCOUNT}",headers=SBH,timeout=10)

# Insert
body={
  "account":ACCOUNT,
  "meli_user_id":UID,
  "access_token":AT,
  "refresh_token":RT,
  "expires_at":None,
  "active":True
}
r=requests.post(f"{SB_URL}/rest/v1/meli_tokens",headers=SBH,json=body,timeout=10)
print(f"[tokens insert] status={r.status_code} body={r.text[:200]}",flush=True)

# Also register in accounts table
body_acc={
  "nickname":ACCOUNT,
  "meli_user_id":UID,
  "active":True,
  "notes":f"Cuenta nueva Yeraldin - {NICK} - {FN} {LN} - added 2026-07-01"
}
r2=requests.post(f"{SB_URL}/rest/v1/accounts",headers=SBH,json=body_acc,timeout=10)
print(f"[accounts insert] status={r2.status_code} body={r2.text[:200]}",flush=True)
print("SUCCESS",flush=True)
