import os, requests, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]
all_ids=[]
for st in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        all_ids.extend(res)
        if len(res)<50 or off>1500: break
        off+=50
rows=[]
for i in range(0,len(all_ids),20):
    batch=",".join(all_ids[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,catalog_listing"},timeout=20).json()
    for x in mg:
        if x.get("code")==200 and x["body"].get("catalog_listing") is True:
            rows.append({"item_id":x["body"]["id"],"title":(x["body"].get("title") or "")[:60]})
print(json.dumps(rows))
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
