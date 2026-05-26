import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_ANGEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_ANGEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
UID=3009687392

# all items across all statuses
all_ids=[]
for st in ["active","paused","under_review","inactive","closed"]:
    scroll=None
    while True:
        p={"search_type":"scan","limit":100,"status":st}
        if scroll: p["scroll_id"]=scroll
        r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params=p,timeout=30).json()
        all_ids+=[(i,st) for i in r.get("results",[])]
        scroll=r.get("scroll_id")
        if not scroll or not r.get("results"): break
print(f"\nTOTAL items in Angel (all statuses): {len(all_ids)}")
by_st={}
for i,st in all_ids: by_st.setdefault(st,[]).append(i)
for st,ids in by_st.items():
    print(f"  {st}: {len(ids)}")

# Sample titles
ids_only=[i for i,_ in all_ids]
print("\n--- DETAIL ---")
for i in range(0,len(ids_only),20):
    batch=",".join(ids_only[i:i+20])
    r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,status,sub_status,title,price,catalog_listing"},timeout=30).json()
    for x in r:
        if x.get("code")==200:
            b=x["body"]
            print(f"  {b['id']} {b.get('status'):<13} cat={b.get('catalog_listing')!s:<5} ${b.get('price')!s:>7} '{(b.get('title') or '')[:70]}'")
