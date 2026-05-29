import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
sid="MLM2967278997"
g=requests.get(f"{API}/items/{sid}",headers=H,timeout=20).json()
print(f"BEFORE: status={g.get('status')} sub={g.get('sub_status')} price={g.get('price')} title='{(g.get('title') or '')[:70]}'")
if g.get("status")=="active":
    print("pause:",requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=20).status_code); time.sleep(0.5)
print("close:",requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"closed"},timeout=20).status_code); time.sleep(0.5)
print("del-flag:",requests.put(f"{API}/items/{sid}",headers=HJ,json={"deleted":"true"},timeout=20).status_code)
g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=20).json()
print(f"AFTER: status={g2.get('status')}")
