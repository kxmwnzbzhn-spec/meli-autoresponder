import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]
print(f"seller={UID} nick={me.get('nickname')}")

for st in ("active","paused","under_review","closed","inactive","programmed"):
    total=0
    off=0
    ids=[]
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        ids.extend(res)
        if len(res)<50 or off>2000: break
        off+=50
    print(f"  {st}: {len(ids)} items")
    if st=="active" and ids:
        # sample first 5
        for i in ids[:5]:
            g=requests.get(f"{API}/items/{i}",headers=H,timeout=10).json()
            print(f"    {i} ${g.get('price')} status={g.get('status')} sub={g.get('sub_status')} | {(g.get('title') or '')[:50]}")
