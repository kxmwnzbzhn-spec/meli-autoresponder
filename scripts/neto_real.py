import os, requests, json, time
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
print(f"=== NETO REAL incluyendo envíos — desde {date_from} ===\n")

def get_ship_cost(sid, headers):
    """Returns sender's cost for a shipment (what seller pays)."""
    if not sid: return 0.0, "no_sid"
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=headers,timeout=10).json()
        sc=r.get("senders",{}).get("cost") if "senders" in r else r.get("senders_cost",{}).get("cost",0)
        if sc is None: sc=0
        return float(sc), "ok"
    except Exception as e:
        return 0.0, f"err:{e}"

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
    
    # Pull orders
    orders=[]; offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
        res=rr.get("results",[])
        if not res: break
        orders.extend(res)
        if len(res)<50: break
        offset+=50
        if offset>5000: break
    
    paid_orders=[o for o in orders if o.get("status") in ("paid","shipped","delivered")]
    cancelled=[o for o in orders if o.get("status")=="cancelled"]
    refunded=[o for o in orders if "refunded" in (o.get("status_detail") or "")]
    
    # Compute bruto, comisión, qty
    gross=fees=qty=0
    sids=[]
    for o in paid_orders:
        for it in o.get("order_items",[]):
            q=it.get("quantity",0) or 0
            gross+= (it.get("unit_price",0) or 0)*q
            fees += (it.get("sale_fee",0) or 0)*q
            qty  += q
        sid=(o.get("shipping",{}) or {}).get("id")
        if sid: sids.append(sid)
    
    # Query shipments in parallel for sender cost
    ship_total=0.0; ship_ok=0; ship_err=0; ship_zero=0
    print(f"  paid={len(paid_orders)}  shipments={len(sids)}  consultando costos…")
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs={ex.submit(get_ship_cost, sid, H): sid for sid in sids}
        for f in as_completed(futs):
            cost, st = f.result()
            ship_total += cost
            if st=="ok": ship_ok+=1
            else: ship_err+=1
            if cost==0: ship_zero+=1
    
    # Cancelled refunds: total_amount of cancelled orders that were refunded
    refund_total=0
    for o in cancelled:
        # if cancelled by seller after payment, refund happened
        # heuristic: if there's a refunded payment
        for p in (o.get("payments") or []):
            ra=p.get("transaction_amount_refunded",0) or 0
            refund_total+=ra
    
    net_real = gross - fees - ship_total - refund_total
    print(f"  Bruto:        ${gross:>12,.2f}")
    print(f"  Comis:       -${fees:>12,.2f}  ({fees/gross*100 if gross else 0:.1f}%)")
    print(f"  Envío seller:-${ship_total:>12,.2f}  (avg ${ship_total/len(sids) if sids else 0:.2f}/orden, ok={ship_ok}, err={ship_err}, zero={ship_zero})")
    print(f"  Refunds:     -${refund_total:>12,.2f}  ({len(cancelled)} canceladas)")
    print(f"  NETO REAL:    ${net_real:>12,.2f}\n")
    
    results[label]={
        "nick":nick,"uid":uid,
        "paid":len(paid_orders),"cancelled":len(cancelled),"qty":qty,
        "gross":gross,"fees":fees,"ship":ship_total,"refund":refund_total,
        "net_real":net_real,
        "ship_ok":ship_ok,"ship_err":ship_err,"ship_zero":ship_zero
    }

print("\n=== RESUMEN ===")
print(f"{'Cuenta':<10} {'Órd':>4} {'Bruto':>14} {'Comis':>12} {'Envío':>12} {'Refund':>10} {'NETO REAL':>14}")
print("-"*90)
T={k:0 for k in ['gross','fees','ship','refund','net','o']}
for k in ["JUAN","RAYMUNDO","CLARIBEL","ASVA","WILBERT"]:
    if k not in results: continue
    v=results[k]
    print(f"{k:<10} {v['paid']:>4} ${v['gross']:>13,.2f} ${v['fees']:>11,.2f} ${v['ship']:>11,.2f} ${v['refund']:>9,.2f} ${v['net_real']:>13,.2f}")
    T['gross']+=v['gross']; T['fees']+=v['fees']; T['ship']+=v['ship']; T['refund']+=v['refund']
    T['net']+=v['net_real']; T['o']+=v['paid']
print("-"*90)
print(f"{'TOTAL':<10} {T['o']:>4} ${T['gross']:>13,.2f} ${T['fees']:>11,.2f} ${T['ship']:>11,.2f} ${T['refund']:>9,.2f} ${T['net']:>13,.2f}")

print("\n=== JSON ===")
print(json.dumps(results,ensure_ascii=False))
