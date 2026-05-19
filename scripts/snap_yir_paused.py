import os,requests,json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
ids=[]; off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=paused&limit=100&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    ids+=res; off+=100
    if off>=r.get("paging",{}).get("total",0): break
print(f"Total paused: {len(ids)}")
# Get details
detail=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    mg=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,sub_status,last_updated",headers=H).json()
    for x in mg:
        b=x.get("body",{}) or {}
        if not b.get("id"): continue
        detail.append({"id":b["id"],"title":(b.get("title") or "")[:60],"price":b.get("price"),"sub":b.get("sub_status",[]),"last_updated":b.get("last_updated")})
# Filter sub_status=paused_by_seller AND last_updated today
import datetime as dt
from datetime import timezone, timedelta
TZ=timezone(timedelta(hours=-6))
today=dt.datetime.now(TZ).date()
to_reactivate=[]
for d in detail:
    if "paused_by_seller" not in d["sub"]: continue
    # only items paused after we ran emergency pause (~last 30 min)
    try:
        lu=dt.datetime.fromisoformat(d["last_updated"].replace("Z","+00:00"))
        delta=(dt.datetime.now(timezone.utc)-lu).total_seconds()
        if delta>1800: continue  # más de 30 min, ignore
    except: continue
    to_reactivate.append(d)
print(f"\nA reactivar mañana 6am Mérida: {len(to_reactivate)}")
for d in to_reactivate: print(f"  {d['id']} ${d['price']} '{d['title']}'")
# Save
with open("/tmp/snap_out.json","w") as f: json.dump(to_reactivate,f,indent=2,ensure_ascii=False)
