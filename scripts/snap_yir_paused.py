import os,requests,json,datetime as dt
from datetime import timezone, timedelta
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

# Listed que user pidió mantener pausados PERMANENTEMENTE (NO reactivar)
DO_NOT_REACTIVATE={
  "MLM5363147396",  # user pidió pausar
  "MLM5363023018",  # user pidió pausar
  "MLM2940673601",  # eliminada
  "MLM2935447531",  # eliminada
}

to_reactivate=[]
all_paused=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    mg=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,sub_status,last_updated,status",headers=H).json()
    for x in mg:
        b=x.get("body",{}) or {}
        if not b.get("id"): continue
        all_paused.append({"id":b["id"],"title":(b.get("title") or "")[:55],"price":b.get("price"),"sub":b.get("sub_status",[]),"last_updated":b.get("last_updated"),"status":b.get("status")})

print(f"Total paused now: {len(all_paused)}")
for d in all_paused:
    if d["id"] in DO_NOT_REACTIVATE: 
        print(f"  SKIP {d['id']} (lista do_not_reactivate)"); continue
    if d["status"]!="paused": continue
    if "paused_by_seller" not in d["sub"]: 
        print(f"  SKIP {d['id']} sub={d['sub']}"); continue
    # last_updated <= 8 hours ago
    try:
        lu=dt.datetime.fromisoformat(d["last_updated"].replace("Z","+00:00"))
        delta_h=(dt.datetime.now(timezone.utc)-lu).total_seconds()/3600
        if delta_h>8:
            print(f"  SKIP {d['id']} (paused hace {delta_h:.1f}h, no reciente)"); continue
    except: continue
    to_reactivate.append(d)

print(f"\n=== A REACTIVAR mañana 6am Mérida: {len(to_reactivate)} ===")
for d in to_reactivate: print(f"  {d['id']} ${d['price']} '{d['title']}'")

with open("/tmp/snap_out.json","w") as f:
    json.dump({"_meta":{"created":dt.datetime.now(timezone(timedelta(hours=-6))).isoformat(),"count":len(to_reactivate)},"items":to_reactivate,"do_not_reactivate":list(DO_NOT_REACTIVATE)},f,indent=2,ensure_ascii=False)
