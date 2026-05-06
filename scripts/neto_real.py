import os, requests, json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

ACCOUNTS=[
    ("JUAN","MELI_REFRESH_TOKEN"),
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
    ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
]

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since=cdmx-timedelta(days=60)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"=== NETO REAL v2 (envío seller + refunds reales) — desde {date_from} ===\n")

def get_ship_cost(sid, headers):
    if not sid: return 0.0, "no_sid"
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=headers,timeout=10)
        if r.status_code!=200: return 0.0, f"http{r.status_code}"
        j=r.json()
        senders=j.get("senders",[])
        if isinstance(senders,list):
            cost=sum((s.get("cost",0) or 0) for s in senders)
        else:
            cost=senders.get("cost",0) or 0
        return float(cost), "ok"
    except Exception as e:
        return 0.0, f"err"

results={}
for label,env in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
    if "access_token" not in r:
        results[label]={"err":"refresh"}; continue
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
    uid=me["id"]; nick=me.get("nickname")
    print(f"--- {label} ({nick} {uid}) ---")
    
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
    
    gross=fees=qty=0
    sids=[]
    for o in paid:
        for it in o.get("order_items",[]):
            q=it.get("quantity",0) or 0
            gross+=(it.get("unit_price",0) or 0)*q
            fees+=(it.get("sale_fee",0) or 0)*q
            qty+=q
        sid=(o.get("shipping",{}) or {}).get("id")
        if sid: sids.append(sid)
    
    # REFUNDS: only count payments with status='refunded' or 'refund' in cancelled orders
    refund_total=0.0
    cancel_real=0
    for o in cancelled:
        order_refund=0.0
        for p in (o.get("payments") or []):
            pst=p.get("status","")
            ra=p.get("transaction_amount_refunded",0) or 0
            if pst=="refunded" and ra>0:
                order_refund+=ra
        if order_refund>0:
            refund_total+=order_refund
            cancel_real+=1
    
    # Shipping cost in parallel
    ship_total=0.0; ship_ok=ship_err=0
    print(f"  paid={len(paid)}  shipments={len(sids)}  consultando costos…")
    with ThreadPoolExecutor(max_workers=15) as ex:
        futs={ex.submit(get_ship_cost, sid, H): sid for sid in sids}
        for f in as_completed(futs):
            cost, st=f.result()
            ship_total+=cost
            if st=="ok": ship_ok+=1
            else: ship_err+=1
    
    net = gross - fees - ship_total - refund_total
    print(f"  Bruto:        ${gross:>13,.2f}")
    print(f"  Comis:       -${fees:>13,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
    print(f"  Envío seller:-${ship_total:>13,.2f}  (avg ${ship_total/ship_ok if ship_ok else 0:.2f}/ord, ok={ship_ok}, err={ship_err})")
    print(f"  Refunds:     -${refund_total:>13,.2f}  ({cancel_real} de {len(cancelled)} canceladas con reembolso real)")
    print(f"  NETO REAL:    ${net:>13,.2f}\n")
    
    results[label]={"nick":nick,"uid":uid,"paid":len(paid),"cancelled":len(cancelled),"cancelled_refunded":cancel_real,
                    "qty":qty,"gross":gross,"fees":fees,"ship":ship_total,"refund":refund_total,"net":net}

print("\n=== RESUMEN ===")
print(f"{'Cuenta':<10} {'Órd':>4} {'Bruto':>14} {'Comis':>13} {'Envío':>13} {'Refund':>11} {'NETO':>14}")
print("-"*90)
T={k:0 for k in ['gross','fees','ship','refund','net','o']}
for k in ["JUAN","RAYMUNDO","CLARIBEL","ASVA","WILBERT"]:
    if k not in results: continue
    v=results[k]
    print(f"{k:<10} {v['paid']:>4} ${v['gross']:>13,.2f} ${v['fees']:>12,.2f} ${v['ship']:>12,.2f} ${v['refund']:>10,.2f} ${v['net']:>13,.2f}")
    T['gross']+=v['gross']; T['fees']+=v['fees']; T['ship']+=v['ship']; T['refund']+=v['refund']; T['net']+=v['net']; T['o']+=v['paid']
print("-"*90)
print(f"{'TOTAL':<10} {T['o']:>4} ${T['gross']:>13,.2f} ${T['fees']:>12,.2f} ${T['ship']:>12,.2f} ${T['refund']:>10,.2f} ${T['net']:>13,.2f}")

print("\n=== JSON ===")
print(json.dumps(results,ensure_ascii=False))
