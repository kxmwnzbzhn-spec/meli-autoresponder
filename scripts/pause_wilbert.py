import os, requests, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_WILBERT"]},timeout=20).json()
AT=r["access_token"]; NEW_RT=r.get("refresh_token")
print(f"NEW_RT_WILBERT={NEW_RT}")
H={"Authorization":f"Bearer {AT}"}
HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]; nick=me.get("nickname")
print(f"seller={uid} nick={nick}")

ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=20).json()
    res=r.get("results") or []
    if not res: break
    ids.extend(res)
    if len(res)<50: break
    off+=50
    if off>5000: break
print(f"ACTIVOS={len(ids)}")

ok=0; fail=0; err_samples=[]
for iid in ids:
    try:
        r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=12)
        if r2.status_code in (200,201): ok+=1
        else:
            fail+=1
            if len(err_samples)<5: err_samples.append(f"{iid}:{r2.status_code}:{r2.text[:120]}")
    except Exception as e:
        fail+=1
        if len(err_samples)<5: err_samples.append(f"{iid}:EXC:{e}")

print(f"PAUSED ok={ok} fail={fail}")
for s in err_samples: print("  ERR:",s)

# Telegram report
TG=os.environ.get("TELEGRAM_BOT_TOKEN",""); CID=os.environ.get("TELEGRAM_CHAT_ID","")
if TG and CID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
        json={"chat_id":CID,"text":f"WILBERT pausa total: ok={ok} fail={fail} de {len(ids)} activos"},timeout=10)
