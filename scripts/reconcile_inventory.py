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

# Load inventario from repo
GHT=os.environ["GH_TOKEN"]
repo="kxmwnzbzhn-spec/meli-autoresponder"
g=requests.get(f"https://api.github.com/repos/{repo}/contents/inventario_master.json",headers={"Authorization":f"Bearer {GHT}"}).json()
inv=json.loads(base64.b64decode(g["content"]))
stock=inv.get("stock",{})

# Smart classifier
MODELO_KW=[
    ("flip 7","JBL Flip 7"),("flip7","JBL Flip 7"),
    ("clip 7","JBL Clip 7"),("clip7","JBL Clip 7"),
    ("charge 6","JBL Charge 6"),("charge6","JBL Charge 6"),
    ("clip 5","JBL Clip 5"),("clip5","JBL Clip 5"),
    ("clip 4","JBL Clip 4"),("clip4","JBL Clip 4"),
    ("go 4","JBL Go 4"),("go4","JBL Go 4"),
    ("go 3","JBL Go 3"),("go3","JBL Go 3"),
    ("grip","JBL Grip"),
    ("xb100","Sony XB100"),("xb-100","Sony XB100"),("xb 100","Sony XB100"),
    ("bose","Bose"),("soundlink","Bose"),
    ("redmi buds","Redmi Buds 4 Lite"),
    ("dashcam","Dashcam ASV-DC170"),
]
COLOR_KW=[
    ("camuflaj","Camuflaje"),("camuflad","Camuflaje"),("squad","Camuflaje"),("camo","Camuflaje"),("verde musg","Camuflaje"),
    ("aqua","Aqua"),("celeste","Aqua"),
    ("azul marino","Azul Marino"),("azul oscuro","Azul Marino"),
    ("morad","Morado"),("violeta","Morado"),("purpur","Morado"),("púrp","Morado"),
    ("rosa","Rosa"),("pink","Rosa"),
    ("roj","Rojo"),
    ("blanc","Blanco"),
    ("azul","Azul"),
    ("negr","Negro"),
]
def smart(title):
    t=(title or "").lower()
    modelo=None
    for kw,name in MODELO_KW:
        if kw in t:
            modelo=name; break
    if not modelo: return None
    color=None
    for kw,name in COLOR_KW:
        if kw in t:
            color=name; break
    if modelo=="Sony XB100": return "Sony XB100|Negro"
    if modelo=="JBL Grip" and not color: color="Negro"
    if modelo=="Dashcam ASV-DC170": return "Dashcam ASV-DC170|-"
    if modelo=="Bose": return f"Bose|{color or 'Negro'}"
    if modelo=="Redmi Buds 4 Lite": return "Redmi Buds 4 Lite|Negro"
    if not color: return None
    if modelo=="JBL Go 4" and color=="Azul": color="Azul Marino"
    if modelo=="JBL Clip 5" and color=="Aqua": color="Azul"  # no Aqua for Clip 5
    return f"{modelo}|{color}"

# Collect sales
accounts=[("Wilbert",tok(RT_W)),("Yiriam",tok(RT_Y)),("Juan",tok(RT_J)),("Raymundo",tok(RT_R))]
sold_by_sku={}
totals_acct={}
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
    totals_acct[name]=len(ids)
    for i in range(0,len(ids),20):
        batch=",".join(ids[i:i+20])
        r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,sold_quantity",headers=H).json()
        for x in r:
            b=x.get("body",{}) or {}
            t=b.get("title","")
            sku=smart(t)
            if sku:
                d=sold_by_sku.setdefault(sku,{"total":0,"by_acct":{}})
                s=int(b.get("sold_quantity",0) or 0)
                d["total"]+=s
                d["by_acct"][name]=d["by_acct"].get(name,0)+s

print("ITEMS POR CUENTA:",totals_acct)
print("\n=== RECONCILIACION (BODEGA - VENTAS = STOCK RESTANTE) ===")
print(f"{'SKU':<30} {'BODEGA':>7} {'VENDIDO':>8} {'STOCK':>7}  {'detalle ventas':<30}")
total_rem=0; total_inv=0; total_sold=0; oversold=[]
all_skus=sorted(set(list(stock.keys())+list(sold_by_sku.keys())))
for sku in all_skus:
    inv_qty=0
    if sku in stock:
        v=stock[sku]; inv_qty=v if isinstance(v,int) else v.get("total",0)
    d=sold_by_sku.get(sku,{})
    sold=d.get("total",0)
    rem=inv_qty-sold
    detail=" ".join(f"{a}:{q}" for a,q in d.get("by_acct",{}).items()) if d else ""
    flag=" ⚠️OVERSOLD" if rem<0 else ""
    if not (inv_qty==0 and sold==0):
        print(f"{sku:<30} {inv_qty:>7} {sold:>8} {rem:>7}  {detail:<30}{flag}")
    total_inv+=inv_qty; total_sold+=sold
    if rem<0: oversold.append((sku,rem))
    if rem>0: total_rem+=rem

print(f"\n=== TOTALES ===")
print(f"Inventario inicial bodega (snapshot 28-Abr-2026): {total_inv}")
print(f"Vendido total (todas cuentas históricos):         {total_sold}")
print(f"Stock REAL restante (suma positivos):             {total_rem}")
if oversold:
    print(f"\n⚠️ SOBREVENTAS:")
    for sku,r in oversold: print(f"  {sku}: {r}")
