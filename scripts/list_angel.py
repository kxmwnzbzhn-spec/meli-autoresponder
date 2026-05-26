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

# scan ALL without status filter
all_ids=set()
scroll=None
while True:
    p={"search_type":"scan","limit":100}
    if scroll: p["scroll_id"]=scroll
    r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params=p,timeout=30).json()
    all_ids.update(r.get("results",[]))
    scroll=r.get("scroll_id")
    if not scroll or not r.get("results"): break
print(f"scan_all_total: {len(all_ids)}")

# Also try the legacy endpoint
r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params={"limit":50,"offset":0},timeout=30).json()
print(f"legacy: paging.total={r.get('paging',{}).get('total')} results={len(r.get('results',[]))}")
all_ids.update(r.get("results",[]))
# offsets
total=r.get("paging",{}).get("total",0)
for off in range(50,min(total,1000),50):
    r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params={"limit":50,"offset":off},timeout=30).json()
    all_ids.update(r.get("results",[]))

print(f"FINAL union: {len(all_ids)} ids")

# detail each
ids=list(all_ids)
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,status,sub_status,title,price,catalog_listing"},timeout=30).json()
    for x in r:
        if x.get("code")==200:
            b=x["body"]
            print(f"  {b['id']:<14} {b.get('status'):<13} cat={b.get('catalog_listing')!s:<5} ${b.get('price')!s:>7} '{(b.get('title') or '')[:65]}'")
