import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
print("YIRIAM_UID:",uid)
ids=[]
for status in ["active","paused"]:
    off=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={status}&limit=100&offset={off}",headers=H).json()
        res=r.get("results",[])
        if not res: break
        ids+=res; off+=100
        if off>=r.get("paging",{}).get("total",0): break
print(f"YIRIAM_TOTAL:{len(ids)}")
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,sold_quantity,status,sub_status,catalog_product_id",headers=H).json()
    for x in r:
        b=x.get("body",{}) or {}
        if not b.get("id"): continue
        t=(b.get("title") or "").lower()
        # match the 3 targets
        if ("go 4" in t and ("roj" in t or "rojo" in t)) or ("go 3" in t and "negr" in t) or ("xb100" in t or "xb-100" in t) or ("sony" in t and "altavoz" in t):
            print("MATCH:",json.dumps({"id":b["id"],"title":b.get("title","")[:80],"price":b.get("price"),"sold":b.get("sold_quantity"),"st":b.get("status"),"sub":b.get("sub_status"),"cpid":b.get("catalog_product_id")},ensure_ascii=False))
