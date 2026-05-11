import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
ids=[]
for status in ["active","paused"]:
    off=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={status}&limit=100&offset={off}",headers=H).json()
        res=r.get("results",[])
        if not res: break
        ids+=res
        off+=100
        if off>=r.get("paging",{}).get("total",0): break
print(f"total ids: {len(ids)}",flush=True)
items=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,sold_quantity,available_quantity,status,sub_status",headers=H).json()
    for x in r:
        b=x.get("body",{})
        if b.get("id"):
            items.append(b)
items.sort(key=lambda x:(-(x.get("sold_quantity") or 0), x.get("title","")))
print("RANK_START")
for it in items:
    print(json.dumps({"id":it["id"],"sold":it.get("sold_quantity",0),"price":it.get("price"),"stock":it.get("available_quantity"),"st":it.get("status"),"sub":it.get("sub_status"),"title":(it.get("title") or "")[:80]},ensure_ascii=False))
print("RANK_END")
