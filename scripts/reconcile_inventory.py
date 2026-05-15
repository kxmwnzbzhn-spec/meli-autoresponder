import os,json,base64,requests,datetime as dt
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

GHT=os.environ["GH_TOKEN"]
repo="kxmwnzbzhn-spec/meli-autoresponder"
g=requests.get(f"https://api.github.com/repos/{repo}/contents/inventario_master.json",headers={"Authorization":f"Bearer {GHT}"}).json()
inv=json.loads(base64.b64decode(g["content"]))
stock=inv.get("stock",{})

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
def smart(title,var_color=None):
    t=(title or "").lower()
    modelo=None
    for kw,name in MODELO_KW:
        if kw in t: modelo=name; break
    if not modelo: return None
    color=None
    src=(var_color or "").lower()+" "+t
    for kw,name in COLOR_KW:
        if kw in src: color=name; break
    if modelo=="Sony XB100": return "Sony XB100|Negro"
    if modelo=="JBL Grip" and not color: color="Negro"
    if modelo=="Dashcam ASV-DC170": return "Dashcam ASV-DC170|-"
    if modelo=="Bose": return f"Bose|{color or 'Negro'}"
    if modelo=="Redmi Buds 4 Lite": return "Redmi Buds 4 Lite|Negro"
    if not color: return None
    if modelo=="JBL Go 4" and color=="Azul": color="Azul Marino"
    if modelo=="JBL Clip 5" and color=="Aqua": color="Azul"
    return f"{modelo}|{color}"

EXCLUDED_STATUS={"cancelled","invalid"}
# Use day-by-day windows from 2026-04-28 to today
start=dt.date(2026,4,28)
end=dt.date(2026,5,16)  # tomorrow inclusive

def fetch_orders(name,T):
    H={"Authorization":f"Bearer {T}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me["id"]
    sold_local={}
    total_orders=0; processed=0
    d=start
    while d<end:
        nd=d+dt.timedelta(days=1)
        d_from=f"{d.isoformat()}T00:00:00.000-06:00"
        d_to=f"{nd.isoformat()}T00:00:00.000-06:00"
        off=0
        while True:
            url=f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={d_from}&order.date_created.to={d_to}&sort=date_desc&limit=50&offset={off}"
            r=requests.get(url,headers=H,timeout=20).json()
            results=r.get("results",[])
            if not results: break
            tot_day=r.get("paging",{}).get("total",0)
            for o in results:
                total_orders+=1
                if o.get("status","") in EXCLUDED_STATUS: continue
                for it in (o.get("order_items") or []):
                    item=it.get("item",{}) or {}
                    title=item.get("title","")
                    var_color=""
                    for va in (item.get("variation_attributes") or []):
                        if va.get("id")=="COLOR": var_color=va.get("value_name","")
                    qty=int(it.get("quantity",0) or 0)
                    sku=smart(title,var_color)
                    if sku:
                        sold_local[sku]=sold_local.get(sku,0)+qty
                    processed+=1
            off+=50
            if off>=tot_day: break
        d=nd
    return sold_local,total_orders,processed

accounts=[
  ("Wilbert",tok(RT_W)),
  ("Yiriam",tok(RT_Y)),
  ("Juan",tok(RT_J)),
  ("Raymundo",tok(RT_R)),
  ("Claribel",tok(os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL",""))),
  ("Asva",tok(os.environ.get("MELI_REFRESH_TOKEN_ASVA",""))),
  ("Mildred",tok(os.environ.get("MELI_REFRESH_TOKEN_MILDRED",""))),
  ("Dilcie",tok(os.environ.get("MELI_REFRESH_TOKEN_DILCIE",""))),
  ("Bren",tok(os.environ.get("MELI_REFRESH_TOKEN_BREN",""))),
]
sold_by_sku={}
order_counts={}
detail_by_acct={}
for name,T in accounts:
    if not T: continue
    local,orders,proc=fetch_orders(name,T)
    order_counts[name]={"orders":orders,"items":proc}
    detail_by_acct[name]=local
    for sku,q in local.items():
        sold_by_sku[sku]=sold_by_sku.get(sku,0)+q
    print(f"  {name}: {orders} orders, {proc} items procesados, {len(local)} SKUs")

print(f"\n=== STOCK REAL post-28-abr (Orders API por día, todas cuentas) ===")
print(f"{'SKU':<32} {'BODEGA':>7} {'VENDIDO':>8} {'STOCK':>7}  Wb / Yr / Jn / Rm")
total_rem=0; total_inv=0; total_sold=0; oversold=[]
all_skus=sorted(set(list(stock.keys())+list(sold_by_sku.keys())))
for sku in all_skus:
    inv_qty=0
    if sku in stock:
        v=stock[sku]; inv_qty=v if isinstance(v,int) else v.get("total",0)
    sold=sold_by_sku.get(sku,0)
    rem=inv_qty-sold
    detail=' '.join(f"{a[:2]}:{detail_by_acct.get(a,{}).get(sku,0)}" for a in ['Wilbert','Yiriam','Juan','Raymundo','Claribel','Asva','Mildred','Dilcie','Bren'] if detail_by_acct.get(a,{}).get(sku,0)>0)
    flag=" ⚠️" if rem<0 else ""
    if not (inv_qty==0 and sold==0):
        print(f"{sku:<32} {inv_qty:>7} {sold:>8} {rem:>7}{flag}  {detail}")
    total_inv+=inv_qty; total_sold+=sold
    if rem<0: oversold.append((sku,inv_qty,sold,rem))
    if rem>0: total_rem+=rem

print(f"\nOrders/items por cuenta:",order_counts)
print(f"\n=== TOTALES ===")
print(f"Bodega snapshot 28-Abr-2026:          {total_inv}")
print(f"Vendido post-snapshot:                {total_sold}")
print(f"Stock REAL restante (suma positivos): {total_rem}")
if oversold:
    print(f"\n⚠️ SOBREVENTAS:")
    for sku,inv,s,r in sorted(oversold,key=lambda x:x[3]):
        print(f"  {sku}: bodega={inv} vendido={s} debes={-r}")
