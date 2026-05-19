"""Lista detallada de Wilbert printed."""
import os, requests, time, re
from datetime import datetime, timedelta, timezone

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_WILBERT"]

r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
at=r["access_token"]
H={"Authorization":f"Bearer {at}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
uid=me["id"]
TZ=timezone(timedelta(hours=-6))
NOW=datetime.now(timezone.utc); START=NOW-timedelta(days=60)

orders=[]; offset=0
while True:
    r=requests.get("https://api.mercadolibre.com/orders/search",headers=H,timeout=20,
        params={"seller":uid,"order.status":"paid",
                "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "limit":50,"offset":offset}).json()
    res=r.get("results",[])
    if not res: break
    orders.extend(res); offset+=len(res)
    if offset>=r.get("paging",{}).get("total",0): break
obs={o.get("shipping",{}).get("id"):o for o in orders if o.get("shipping",{}).get("id")}

def _color_map(t):
    if not t: return None
    tl=" "+t.lower()+" "
    cm=[("camuflaj","Camuflaje"),("camo","Camuflaje"),("azul marino","Azul Marino"),
        ("aqua","Aqua"),("celeste","Celeste"),("negr","Negro"),(" black","Negro"),
        ("roj","Rojo"),(" red","Rojo"),("rosa","Rosa"),("pink","Rosa"),
        ("morad","Morado"),("violeta","Morado"),("purple","Morado"),
        (" azul","Azul"),(" blue","Azul"),("blanco","Blanco"),("white","Blanco")]
    for k,v in cm:
        if k in tl: return v
    return t.strip().title() if t.strip() else None

def get_color(item_obj):
    for a in (item_obj.get("variation_attributes") or []):
        if a.get("id")=="COLOR":
            c=_color_map(a.get("value_name") or "")
            if c: return c
    return None

def get_model(t):
    t=t.replace("Bocina ","").replace("JBL ","").replace("Sony ","").replace("Bose ","")
    tl=t.lower()
    if "go 4" in tl or "go4" in tl: return "Go 4"
    if "go 3" in tl or "go3" in tl: return "Go 3"
    if "clip 5" in tl or "clip5" in tl: return "Clip 5"
    if "charge 6" in tl: return "Charge 6"
    if "flip 7" in tl: return "Flip 7"
    if "grip" in tl: return "Grip"
    if "xb100" in tl: return "Sony XB100"
    if "soundlink" in tl: return "Bose SoundLink"
    return t[:24]

rows=[]
for sid, ord_o in obs.items():
    try:
        sh=requests.get(f"https://api.mercadolibre.com/shipments/{sid}",headers=H,timeout=10).json()
        if sh.get("status")!="ready_to_ship" or sh.get("substatus")!="printed": continue
        items=ord_o.get("order_items",[])
        prods=[]; iids=[]
        for it in items:
            io_obj = it.get("item") or {}
            model=get_model(io_obj.get("title",""))
            color=get_color(io_obj) or _color_map(io_obj.get("title","")) or ""
            qty=it.get("quantity",1)
            prods.append(f"{model} {color} x{qty}".strip())
            iids.append(io_obj.get("id"))
        buyer=(ord_o.get("buyer") or {}).get("nickname","?")
        # handling_limit
        dl=""
        lt=sh.get("lead_time",{}).get("estimated_handling_limit",{})
        if isinstance(lt,dict):
            ed=lt.get("date")
            if ed:
                try: dl=datetime.fromisoformat(ed.replace("Z","+00:00")).astimezone(TZ).strftime("%a %d %H:%M")
                except: pass
        rows.append({"sid":sid,"prods":" + ".join(prods),"buyer":buyer,"deadline":dl,
                     "iids":",".join(iids)})
        time.sleep(0.03)
    except Exception as e:
        print(f"  err {sid}: {str(e)[:80]}")

# Ordena por producto
rows.sort(key=lambda r: (r["prods"], r["deadline"], r["sid"]))
print(f"\n=== Wilbert PRINTED (listas para enviar): {len(rows)} ===\n")
print(f"{'#':>3}  {'SID':>13}  {'DEADLINE':<15}  {'PRODUCTO':<35}  {'COMPRADOR'}")
for i,r in enumerate(rows,1):
    print(f"{i:>3}  {r['sid']:>13}  {r['deadline'][:15]:<15}  {r['prods'][:35]:<35}  {r['buyer'][:25]}")
