import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
ids=[]
for st in ["active","paused"]:
    off=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H).json()
        res=r.get("results",[])
        if not res: break
        ids+=res; off+=100
        if off>=r.get("paging",{}).get("total",0): break
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,variations,available_quantity,status",headers=H).json()
    for x in r:
        b=x.get("body",{}) or {}
        t=(b.get("title") or "").lower()
        vrs=b.get("variations") or []
        if ("go 4" in t or "go4" in t) and len(vrs)>=2:
            print(f"MULTI {b['id']} st={b.get('status')} qty={b.get('available_quantity')} vars={len(vrs)} title={b.get('title','')[:70]}")
            for v in vrs:
                color=""
                for c in v.get("attribute_combinations",[]):
                    if c.get("id")=="COLOR": color=c.get("value_name")
                print(f"    vid={v.get('id')} color={color} qty={v.get('available_quantity')}")
