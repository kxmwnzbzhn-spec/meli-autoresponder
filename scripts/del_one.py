import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
sid="MLM5245546734"
g=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
print(f"BEFORE: status={g.get('status')} sold={g.get('sold_quantity')} price={g.get('price')} title='{(g.get('title') or '')[:80]}'")
if g.get("status")=="active":
    print("pause:",requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=30).status_code); time.sleep(1)
print("close:",requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"closed"},timeout=30).status_code); time.sleep(1)
print("del-flag:",requests.put(f"{API}/items/{sid}",headers=HJ,json={"deleted":"true"},timeout=30).status_code); time.sleep(1)
g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
print(f"AFTER: status={g2.get('status')}")
