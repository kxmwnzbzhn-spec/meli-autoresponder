import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5705933616"
g=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=10).json()
print(f"BEFORE: status={g.get('status')} sub={g.get('sub_status')} title={g.get('title','?')[:60]}",flush=True)
st=g.get("status")
if st=="active":
    pr=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"paused"},timeout=10).json()
    print(f"paused: {pr.get('status')} err={pr.get('message','')}",flush=True)
    time.sleep(1)
if st not in ("closed","under_review"):
    cr=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"closed"},timeout=10).json()
    print(f"closed: {cr.get('status')} err={cr.get('message','')}",flush=True)
elif st=="under_review":
    cr=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"closed"},timeout=10).json()
    print(f"closed_attempt: {cr.get('status')} err={cr.get('message','')}",flush=True)
g2=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,status",headers=H,timeout=10).json()
print(f"FINAL: status={g2.get('status')}",flush=True)
