import os, requests, json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
if "access_token" not in r:
    print(f"REFRESH FAIL: {r}"); raise SystemExit(1)
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]; nick=me.get("nickname"); email=me.get("email","")

print(f"=== AUDITORÍA RAYMUNDO MAY CHI ===")
print(f"Nick: {nick}")
print(f"UID: {uid}")
print(f"Email: {email}")
print(f"Site: {me.get('site_id')}  Status: {me.get('status',{}).get('site_status')}")
print(f"User type: {me.get('user_type')}")
seller=me.get("seller_reputation") or {}
print(f"Reputación: {seller.get('level_id','?')} | Power seller: {seller.get('power_seller_status')}")

# Pull TODAS las orders 60d (sort=date_desc)
cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since=cdmx-timedelta(days=60)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"\n=== Auditoría últimos 60 días — desde {date_from} ===")

orders=[]; offset=0
while True:
    rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
    res=rr.get("results",[])
    if not res: break
    orders.extend(res)
    if len(res)<50: break
    offset+=50
    if offset>5000: break

paid=[o for o in orders if o.get("status") in ("paid","shipped","delivered")]
cancelled=[o for o in orders if o.get("status")=="cancelled"]
print(f"Total órdenes 60d: {len(orders)}  (paid={len(paid)}, cancelled={len(cancelled)})")

gross=fees=qty=0
sids=[]
items_count={}
by_day={}
for o in paid:
    day=o.get("date_created","")[:10]
    g_o=f_o=q_o=0
    for it in o.get("order_items",[]):
        q=it.get("quantity",0) or 0
        up=it.get("unit_price",0) or 0
        sf=it.get("sale_fee",0) or 0
        g_o+=up*q; f_o+=sf*q; q_o+=q
        title=it.get("item",{}).get("title","")[:55]
        if title:
            e=items_count.setdefault(title,{"u":0,"r":0})
            e["u"]+=q; e["r"]+=up*q
    gross+=g_o; fees+=f_o; qty+=q_o
    d=by_day.setdefault(day,{"o":0,"u":0,"g":0})
    d["o"]+=1; d["u"]+=q_o; d["g"]+=g_o
    sid=(o.get("shipping",{}) or {}).get("id")
    if sid: sids.append(sid)

# Refunds (con heurística post-release)
def is_post_release(o):
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    return ("mediation" in desc) or ("cancel_purchase" in desc) or ("buyer" in desc)

refund_post=refund_pre=0
cancel_motivos={}
for o in cancelled:
    cd=o.get("cancel_detail") or {}
    rsn=cd.get("description") or "?"
    cancel_motivos[rsn]=cancel_motivos.get(rsn,0)+1
    for p in (o.get("payments") or []):
        if p.get("status")=="refunded":
            ra=p.get("transaction_amount_refunded",0) or 0
            if is_post_release(o): refund_post+=ra
            else: refund_pre+=ra

# Shipping costs (parallel)
def get_ship(sid,h):
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json()
        s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

ship_total=0.0
print(f"\nConsultando {len(sids)} shipments costos…")
with ThreadPoolExecutor(max_workers=15) as ex:
    futs=[ex.submit(get_ship,sid,H) for sid in sids]
    for f in as_completed(futs):
        ship_total+=f.result()

neto = gross - fees - ship_total - refund_post

print(f"\n=== TOTALES 60d ===")
print(f"Bruto:         ${gross:>13,.2f}")
print(f"Comis MELI:   -${fees:>13,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
print(f"Envío seller: -${ship_total:>13,.2f}  (avg ${ship_total/len(sids) if sids else 0:.2f}/orden)")
print(f"Refund post:  -${refund_post:>13,.2f}")
print(f"Refund pre:    ${refund_pre:>13,.2f}  (NO descuenta MP, ventas que MELI canceló pre-release)")
print(f"NETO REAL:     ${neto:>13,.2f}")
print(f"Unidades:       {qty:>5}")

print(f"\n=== Reconciliación contra saldo MP $81,126 ===")
diff = 81126 - neto
print(f"Saldo MP REAL hoy: $81,126.00")
print(f"NETO 60d libros:   ${neto:,.2f}")
print(f"Diferencia:        ${diff:,.2f}  → ventas pre-60d ya liberadas + dinero en garantía")

print(f"\n=== TOP MODELOS 60d ===")
for t,e in sorted(items_count.items(),key=lambda x:-x[1]["r"])[:10]:
    print(f"  {e['u']:>4}u  ${e['r']:>10,.0f}  {t}")

print(f"\n=== POR DÍA (últimos 14 con ventas) ===")
days=sorted(by_day.items(),reverse=True)[:14]
for d,v in days:
    print(f"  {d}  ord={v['o']:>3}  un={v['u']:>3}  bruto=${v['g']:>10,.2f}")

print(f"\n=== MOTIVOS CANCELACIÓN ===")
for r,c in sorted(cancel_motivos.items(),key=lambda x:-x[1])[:8]:
    print(f"  {c:>3}x  {r}")

# Items activos
items=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=1",headers=H,timeout=15).json()
items_paused=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=paused&limit=1",headers=H,timeout=15).json()
print(f"\n=== INVENTARIO ===")
print(f"Activos: {items.get('paging',{}).get('total','?')}")
print(f"Pausados: {items_paused.get('paging',{}).get('total','?')}")

# Restrictions
rest=requests.get("https://api.mercadolibre.com/users/me/restrictions",headers=H,timeout=15).json()
print(f"\n=== RESTRICCIONES ===")
print(json.dumps(rest,ensure_ascii=False)[:600])

# Output JSON
print("\n=== JSON ===")
out={"nick":nick,"uid":uid,"email":email,"paid":len(paid),"cancelled":len(cancelled),
     "gross":gross,"fees":fees,"ship":ship_total,"refund_post":refund_post,"refund_pre":refund_pre,
     "neto":neto,"qty":qty,"saldo_real":81126,"diff":diff,
     "top_items":sorted([{"t":t,"u":v["u"],"r":v["r"]} for t,v in items_count.items()],key=lambda x:-x["r"])[:15],
     "by_day":dict(sorted(by_day.items(),reverse=True)),
     "cancel_motivos":cancel_motivos}
print(json.dumps(out,ensure_ascii=False))
