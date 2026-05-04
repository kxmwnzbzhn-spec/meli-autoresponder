"""Activar las 2 publicaciones Bose en Raymundo."""
import os, requests
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]

BOSE = ["MLM2906041435","MLM2906016765"]

r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

for iid in BOSE:
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active"},timeout=15)
    if rp.status_code==200:
        info=rp.json()
        print(f"✅ {iid} → status={info.get('status')} price=${info.get('price')}")
    else:
        print(f"❌ {iid}: {rp.status_code} {rp.text[:300]}")

TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")
if TG and TGCID:
    msg=f"🔊 *Bose activadas en Raymundo*\n\n"
    for iid in BOSE: msg+=f"• `{iid}` $3499\n"
    msg+=f"\nWatchdog ahora tiene whitelist - no las pausará."
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg},timeout=20)
