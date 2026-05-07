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

print(f"=== AUDITORÍA cuenta VM (token MELI_REFRESH_TOKEN_ASGARI) ===")
print(f"Nick: {nick}  UID: {uid}  Email: {email}")
print(f"Site: {me.get('site_id')}  Status: {me.get('status',{}).get('site_status')}")
seller=me.get("seller_reputation") or {}
print(f"Reputación: {seller.get('level_id','?')} | Power seller: {seller.get('power_seller_status')}")

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since=cdmx-timedelta(days=60)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")

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
print(f"\n60d total={len(orders)} paid={len(paid)} cancelled={len(cancelled)}")

gross=fees=qty=0; sids=[]
items_count={}; by_day={}
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

def is_post(o):
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    return ("mediation" in desc) or ("cancel_purchase" in desc) or ("buyer" in desc)

refund_post=refund_pre=0; cancel_motivos={}
for o in cancelled:
    cd=o.get("cancel_detail") or {}
    rsn=cd.get("description") or "?"
    cancel_motivos[rsn]=cancel_motivos.get(rsn,0)+1
    for p in (o.get("payments") or []):
        if p.get("status")=="refunded":
            ra=p.get("transaction_amount_refunded",0) or 0
            if is_post(o): refund_post+=ra
            else: refund_pre+=ra

def get_ship(sid,h):
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json(); s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

ship_total=0.0
print(f"Consultando {len(sids)} shipments…")
if sids:
    with ThreadPoolExecutor(max_workers=15) as ex:
        futs=[ex.submit(get_ship,sid,H) for sid in sids]
        for f in as_completed(futs):
            ship_total+=f.result()

neto=gross-fees-ship_total-refund_post

print(f"\n=== TOTALES 60d ===")
print(f"Bruto:        ${gross:>13,.2f}")
print(f"Comis:       -${fees:>13,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
print(f"Envío seller:-${ship_total:>13,.2f}")
print(f"Refund post: -${refund_post:>13,.2f}")
print(f"Refund pre:   ${refund_pre:>13,.2f}")
print(f"NETO REAL:    ${neto:>13,.2f}")
print(f"Unidades:      {qty}")

print(f"\nTOP MODELOS:")
for t,e in sorted(items_count.items(),key=lambda x:-x[1]["r"])[:10]:
    print(f"  {e['u']:>4}u  ${e['r']:>10,.0f}  {t}")

print(f"\nPOR DÍA (top 14):")
for d,v in sorted(by_day.items(),reverse=True)[:14]:
    print(f"  {d}  ord={v['o']:>3}  un={v['u']:>3}  bruto=${v['g']:>10,.2f}")

print(f"\nMOTIVOS CANCELACIÓN:")
for rsn,c in sorted(cancel_motivos.items(),key=lambda x:-x[1])[:8]:
    print(f"  {c:>3}x  {rsn}")

items=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=1",headers=H,timeout=15).json()
items_p=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=paused&limit=1",headers=H,timeout=15).json()
print(f"\nINVENTARIO: activos={items.get('paging',{}).get('total','?')}  pausados={items_p.get('paging',{}).get('total','?')}")

print("\n=== JSON ===")
out={"nick":nick,"uid":uid,"email":email,"paid":len(paid),"cancelled":len(cancelled),
     "gross":gross,"fees":fees,"ship":ship_total,"refund_post":refund_post,"refund_pre":refund_pre,
     "neto":neto,"qty":qty,
     "items_active":items.get('paging',{}).get('total',0),"items_paused":items_p.get('paging',{}).get('total',0),
     "top_items":sorted([{"t":t,"u":v["u"],"r":v["r"]} for t,v in items_count.items()],key=lambda x:-x["r"])[:15],
     "by_day":dict(sorted(by_day.items(),reverse=True)),
     "cancel_motivos":cancel_motivos,
     "reputation":seller.get("level_id","?"),
     "first_day":min(by_day.keys()) if by_day else None,
     "last_day":max(by_day.keys()) if by_day else None}
print(json.dumps(out,ensure_ascii=False))
