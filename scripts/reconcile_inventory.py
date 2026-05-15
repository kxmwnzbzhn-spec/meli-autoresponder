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
        if kw in t:
            modelo=name; break
    if not modelo: return None
    color=None
    src=(var_color or "").lower()+" "+t  # variation color preferred
    for kw,name in COLOR_KW:
        if kw in src:
            color=name; break
    if modelo=="Sony XB100": return "Sony XB100|Negro"
    if modelo=="JBL Grip" and not color: color="Negro"
    if modelo=="Dashcam ASV-DC170": return "Dashcam ASV-DC170|-"
    if modelo=="Bose": return f"Bose|{color or 'Negro'}"
    if modelo=="Redmi Buds 4 Lite": return "Redmi Buds 4 Lite|Negro"
    if not color: return None
    if modelo=="JBL Go 4" and color=="Azul": color="Azul Marino"
    if modelo=="JBL Clip 5" and color=="Aqua": color="Azul"
    return f"{modelo}|{color}"

FROM_DATE="2026-04-28T00:00:00.000-06:00"
EXCLUDED_STATUS={"cancelled","invalid"}
accounts=[("Wilbert",tok(RT_W)),("Yiriam",tok(RT_Y)),("Juan",tok(RT_J)),("Raymundo",tok(RT_R))]
sold_by_sku={}
order_counts={}
ungrouped={}
for name,T in accounts:
    if not T: 
        print(f"  {name}: NO TOKEN")
        continue
    H={"Authorization":f"Bearer {T}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me["id"]
    off=0; total_orders=0; processed=0
    while True:
        url=f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={FROM_DATE}&sort=date_desc&limit=50&offset={off}"
        r=requests.get(url,headers=H,timeout=20).json()
        results=r.get("results",[])
        if not results: break
        total_orders=r.get("paging",{}).get("total",0)
        for o in results:
            status=o.get("status","")
            if status in EXCLUDED_STATUS: continue
            for it in (o.get("order_items") or []):
                item=it.get("item",{}) or {}
                title=item.get("title","")
                # check variation_attributes for COLOR
                var_color=""
                for va in (item.get("variation_attributes") or []):
                    if va.get("id")=="COLOR":
                        var_color=va.get("value_name","")
                qty=int(it.get("quantity",0) or 0)
                sku=smart(title,var_color)
                if sku:
                    d=sold_by_sku.setdefault(sku,{"total":0,"by_acct":{}})
                    d["total"]+=qty
                    d["by_acct"][name]=d["by_acct"].get(name,0)+qty
                else:
                    ungrouped.setdefault(title[:60],0)
                    ungrouped[title[:60]]+=qty
                processed+=1
        off+=50
        if off>=total_orders: break
    order_counts[name]={"total":total_orders,"items_processed":processed}
    print(f"  {name}: {total_orders} orders, {processed} order_items procesados")

print(f"\n=== Ventas desde {FROM_DATE[:10]} (Orders API, excl. cancelled) ===")
print(f"{'SKU':<32} {'BODEGA':>7} {'VENDIDO':>8} {'STOCK':>7}")
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
    flag=" ⚠️" if rem<0 else ""
    if not (inv_qty==0 and sold==0):
        print(f"{sku:<32} {inv_qty:>7} {sold:>8} {rem:>7}{flag}  {detail}")
    total_inv+=inv_qty; total_sold+=sold
    if rem<0: oversold.append((sku,inv_qty,sold,rem))
    if rem>0: total_rem+=rem

print(f"\n=== TOTALES ===")
print(f"Inventario bodega snapshot 28-Abr-2026: {total_inv}")
print(f"Vendido post-snapshot (Orders API):     {total_sold}")
print(f"Stock REAL restante (suma positivos):   {total_rem}")
print(f"\nOrders por cuenta:",order_counts)
if oversold:
    print(f"\n⚠️ SOBREVENTAS (post-snapshot):")
    for sku,inv,s,r in oversold: print(f"  {sku}: bodega={inv} vendido={s} → debes {-r}")
if ungrouped:
    print(f"\nUNGROUPED (no se mapearon a inventario):")
    for t,q in sorted(ungrouped.items(),key=lambda x:-x[1])[:20]:
        print(f"  qty={q:>3}  {t}")
