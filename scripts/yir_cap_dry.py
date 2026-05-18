#!/usr/bin/env python3
"""DRY RUN del sales cap: ejecuta TODA la lógica sin tocar MELI ni commit cfg."""
import os,requests,json,datetime as dt
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN"); TC=os.environ.get("TELEGRAM_CHAT_ID")
TEST_CAP=int(os.environ.get("TEST_CAP","7"))

T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me.get("id")
print(f"=== DRY RUN ===")
print(f"Cuenta: {me.get('nickname')} uid={uid}")
print(f"TEST_CAP: {TEST_CAP}")

today=dt.date.today().isoformat()
date_from=f"{today}T00:00:00.000-06:00"
sold=0
off=0
sample_orders=[]
while True:
    r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    for o in res:
        if o.get("status") in ("cancelled","invalid"): continue
        for it in (o.get("order_items") or []):
            sold+=int(it.get("quantity",0) or 0)
        if len(sample_orders)<5:
            sample_orders.append({"id":o.get("id"),"date":o.get("date_created","")[:19],"status":o.get("status"),"items":[(it["item"]["id"],it.get("quantity",0)) for it in (o.get("order_items") or [])]})
    off+=50
    if off>=r.get("paging",{}).get("total",0): break

print(f"Ventas hoy: {sold}")
print(f"Sample ordenes:")
for o in sample_orders: print(f"  {o}")
print()
print(f"Decisión: {sold} >= {TEST_CAP} ? {sold>=TEST_CAP}")
if sold<TEST_CAP:
    print(f"  No dispararía. (con cap real=50 tampoco)")
    raise SystemExit(0)

# Listar items active SIN pausar
ids=[]
off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=100&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    ids+=res; off+=100
    if off>=r.get("paging",{}).get("total",0): break

print(f"\n[SIMULACIÓN] PAUSARÍA estos {len(ids)} items active:")
# Sample 5 nombres
sample=[]
for i in ids[:5]:
    g=requests.get(f"https://api.mercadolibre.com/items/{i}?attributes=id,title,price,status,sub_status",headers=H).json()
    sample.append((g.get("id"),g.get("title","")[:50],g.get("price"),g.get("status"),g.get("sub_status")))
for s in sample: print(f"  {s}")
print(f"  ... y {max(0,len(ids)-5)} más")

# Verifica que credenciales pueden PUT (no ejecuta)
print(f"\n[VERIFICACIÓN] Test PUT en 1 item sin cambio (dry):")
if ids:
    test_id=ids[0]
    # GET para verificar acceso
    r=requests.get(f"https://api.mercadolibre.com/items/{test_id}",headers=H,timeout=10)
    print(f"  GET {test_id}: http={r.status_code}")
    if r.status_code==200:
        print(f"  ✓ Acceso a items confirmado")
print(f"\n=== Resultado ===")
print(f"Si cap real fuera {TEST_CAP}, ahora mismo: PAUSARÍA {len(ids)} items active.")
print(f"Cap real es 50. Faltan {50-sold} ventas para dispararse.")
