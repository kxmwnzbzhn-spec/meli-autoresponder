import os, requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

ACCOUNTS=[
    ("JUAN",     "MELI_REFRESH_TOKEN",          120942.00, datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6))), 89865.00),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO", 338000.00, datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6))), 265000.00),
]

def is_post(o):
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    return ("mediation" in desc) or ("cancel_purchase" in desc) or ("buyer" in desc)

def get_ship(sid,h):
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json(); s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
print(f"=== AUDITORÍA PROFUNDA JUAN & RAYMUNDO — {cdmx.strftime('%d-%m-%Y %H:%M')} CDMX ===\n")

for label, env, anchor_amt, anchor_dt, retiro_hoy in ACCOUNTS:
    RT=os.environ[env]
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me["id"]; nick=me.get("nickname")
    
    date_from_utc=anchor_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    orders=[]; offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from_utc}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
        res=rr.get("results",[])
        if not res: break
        orders.extend(res)
        if len(res)<50: break
        offset+=50
        if offset>5000: break
    
    paid=[o for o in orders if o.get("status") in ("paid","shipped","delivered")]
    cancelled=[o for o in orders if o.get("status")=="cancelled"]
    
    gross=fees=qty=0; sids=[]
    for o in paid:
        for it in o.get("order_items",[]):
            q=it.get("quantity",0) or 0
            gross+=(it.get("unit_price",0) or 0)*q
            fees+=(it.get("sale_fee",0) or 0)*q
            qty+=q
        sid=(o.get("shipping",{}) or {}).get("id")
        if sid: sids.append(sid)
    
    refund=0; refund_orders=[]
    for o in cancelled:
        if not is_post(o): continue
        for p in (o.get("payments") or []):
            if p.get("status")=="refunded":
                ra=p.get("transaction_amount_refunded",0) or 0
                refund += ra
                if ra>0: refund_orders.append((o.get("id"),ra))
    
    ship=0.0
    if sids:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs=[ex.submit(get_ship,sid,H) for sid in sids]
            for f in as_completed(futs):
                ship+=f.result()
    
    retencion = gross * 0.0228
    neto_delta = gross - fees - ship - refund - retencion
    saldo_pre_retiro = anchor_amt + neto_delta
    saldo_final = saldo_pre_retiro - retiro_hoy
    
    print(f"━━━ {label} ({nick} / UID {uid}) ━━━")
    print(f"  Ventana: desde {anchor_dt.strftime('%d-%b %H:%M')} hasta hoy")
    print(f"  Órdenes paid en ventana: {len(paid)} ({qty} unidades)")
    print(f"  Órdenes cancelled en ventana: {len(cancelled)} ({len(refund_orders)} con refund real)")
    print()
    print(f"  CÁLCULO PASO A PASO:")
    print(f"  (1) Ancla 5-may:                ${anchor_amt:>14,.2f}")
    print(f"  (2) Bruto desde ancla:          ${gross:>14,.2f}")
    print(f"  (3) -Comisión MELI:             ${-fees:>14,.2f}  ({fees/gross*100 if gross else 0:.2f}% del bruto)")
    print(f"  (4) -Envío seller:              ${-ship:>14,.2f}  (avg ${ship/len(sids) if sids else 0:.2f}/orden)")
    print(f"  (5) -Refunds post-release:      ${-refund:>14,.2f}  ({len(refund_orders)} orders)")
    print(f"  (6) -Retención MELI 2.28%:      ${-retencion:>14,.2f}")
    print(f"      = Delta NETO ({label}):     ${neto_delta:>14,.2f}")
    print(f"  (7) Saldo pre-retiro:           ${saldo_pre_retiro:>14,.2f}")
    print(f"  (8) -Retiro hoy:                ${-retiro_hoy:>14,.2f}")
    print(f"  (9) = SALDO FINAL:              ${saldo_final:>14,.2f}")
    print()
    
    # Lista las últimas 5 órdenes paid + 5 cancelled con refund
    print(f"  Últimas 5 órdenes paid (en ventana):")
    for o in paid[:5]:
        items=o.get("order_items",[])
        title=items[0].get("item",{}).get("title","")[:50] if items else ""
        amt=o.get("total_amount",0)
        print(f"    {o.get('date_created','')[:16]} ${amt:>6,.0f}  {title}")
    
    if refund_orders:
        print(f"\n  Refunds reales detectados:")
        for oid, ra in refund_orders[:5]:
            print(f"    Order {oid}: ${ra:,.2f}")
    
    print()
