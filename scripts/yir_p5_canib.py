import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

PAUSE5=["MLM2909179599","MLM2909183135","MLM5291772440","MLM5291776046","MLM5291788552"]
print("=== PAUSING 5 ===")
for iid in PAUSE5:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"paused"})
    print(f"  {iid} '{(g.get('title') or '')[:45]}' was={g.get('status')} → http={r.status_code}")
    time.sleep(0.3)

# Audit canibalización: group active items by catalog_product_id
print("\n=== AUDIT CANIBALIZACIÓN ===")
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
ids=[]; off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=100&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    ids+=res; off+=100
    if off>=r.get("paging",{}).get("total",0): break
print(f"Total active Yiriam: {len(ids)}")
by_cpid={}
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    mg=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,catalog_product_id,price,sold_quantity",headers=H).json()
    for x in mg:
        b=x.get("body",{}) or {}
        cpid=b.get("catalog_product_id")
        if not cpid: continue
        by_cpid.setdefault(cpid,[]).append({"id":b["id"],"title":(b.get("title") or "")[:50],"price":b.get("price"),"sold":b.get("sold_quantity") or 0})

duplicates=[(cpid,lst) for cpid,lst in by_cpid.items() if len(lst)>1]
print(f"\nCPIDs duplicados (canibalización): {len(duplicates)}")
for cpid,lst in duplicates:
    lst.sort(key=lambda x:-x["sold"])
    print(f"\n  CPID={cpid} → {len(lst)} listings:")
    for d in lst: print(f"    {d['id']} sold={d['sold']} ${d['price']} '{d['title']}'")
    print(f"    → KEEP: {lst[0]['id']} (más ventas)")
    # Pause duplicates (keep top)
    for d in lst[1:]:
        r=requests.put(f"https://api.mercadolibre.com/items/{d['id']}",headers=HJ,json={"status":"paused"})
        print(f"    → PAUSE {d['id']} http={r.status_code}")
        time.sleep(0.3)
