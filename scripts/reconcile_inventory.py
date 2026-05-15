import os,json,base64,requests
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_Y=os.environ.get("MELI_REFRESH_TOKEN_YC_NEW","")
RT_J=os.environ.get("MELI_REFRESH_TOKEN_JUAN","")
RT_R=os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO","")
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]

def tok(rt):
    if not rt: return None
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15)
        return r.json().get("access_token")
    except: return None

# Load inventario_master from repo
GHT=os.environ["GH_TOKEN"]
repo="kxmwnzbzhn-spec/meli-autoresponder"
g=requests.get(f"https://api.github.com/repos/{repo}/contents/inventario_master.json",headers={"Authorization":f"Bearer {GHT}"}).json()
inv=json.loads(base64.b64decode(g["content"]))
keywords=inv.get("_categorize_keywords",{})
stock=inv.get("stock",{})
stock_perf=inv.get("stock_perfumes",{})
print("=== INVENTARIO BODEGA (snapshot 2026-04-28) ===")
total_inicial=0
for k,v in stock.items():
    qty=v if isinstance(v,int) else v.get("qty",0)
    total_inicial+=qty
    print(f"  {k:<30} {qty:>4}")
for k,v in stock_perf.items():
    qty=v if isinstance(v,int) else v.get("qty",0)
    total_inicial+=qty
print(f"\nTotal inicial bodega: {total_inicial}\n")

# Classify function from inventario_master
def classify(title):
    t=(title or "").lower()
    for sku, kws in keywords.items():
        for kw in kws:
            if kw.lower() in t:
                return sku
    return None

# Collect sales across all accounts
accounts=[("Wilbert",tok(RT_W)),("Yiriam",tok(RT_Y)),("Juan",tok(RT_J)),("Raymundo",tok(RT_R))]
sold_by_sku={}
for name,T in accounts:
    if not T: continue
    H={"Authorization":f"Bearer {T}"}
    try:
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
        uid=me["id"]
    except: continue
    ids=[]
    for st in ("active","paused","closed"):
        off=0
        while True:
            r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H,timeout=15).json()
            res=r.get("results",[])
            if not res: break
            ids+=res; off+=100
            if off>=r.get("paging",{}).get("total",0): break
    print(f"  {name}: {len(ids)} items")
    for i in range(0,len(ids),20):
        batch=",".join(ids[i:i+20])
        r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,sold_quantity,status",headers=H).json()
        for x in r:
            b=x.get("body",{}) or {}
            t=b.get("title","")
            sku=classify(t)
            if sku:
                sold_by_sku.setdefault(sku,{"total":0,"by_acct":{}})
                s=int(b.get("sold_quantity",0) or 0)
                sold_by_sku[sku]["total"]+=s
                sold_by_sku[sku]["by_acct"][name]=sold_by_sku[sku]["by_acct"].get(name,0)+s

print("\n=== RECONCILIACION ===")
print(f"{'SKU':<30} {'INV':>5} {'VTAS':>5} {'STOCK':>6}")
total_real=0
for sku in sorted(set(list(stock.keys())+list(stock_perf.keys())+list(sold_by_sku.keys()))):
    inv_qty=0
    if sku in stock:
        v=stock[sku]; inv_qty=v if isinstance(v,int) else v.get("qty",0)
    if sku in stock_perf:
        v=stock_perf[sku]; inv_qty=v if isinstance(v,int) else v.get("qty",0)
    sold=sold_by_sku.get(sku,{}).get("total",0)
    rem=inv_qty-sold
    total_real+=rem if rem>0 else 0
    flag=" ⚠️ OVERSOLD" if rem<0 else ""
    print(f"{sku:<30} {inv_qty:>5} {sold:>5} {rem:>6}{flag}")
print(f"\nStock REAL restante (suma positivos): {total_real}")
