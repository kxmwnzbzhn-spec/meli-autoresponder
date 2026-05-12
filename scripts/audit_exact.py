import os, requests, json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

# Anchors confirmados por Sr. Luis con sus fechas
# Format: (anchor_amount, anchor_date_cdmx, label)
ANCHORS={
    "JUAN":          (120942.00, datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6)))),
    "RAYMUNDO":      (338000.00, datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6)))),
    "CLARIBEL":      (34517.00,  datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6)))),
    "RAYMUNDO_MAY":  (81126.00,  datetime(2026,5,7,0,0,0,tzinfo=timezone(timedelta(hours=-6)))),
    "ANGEL_DAMIAN":  (60000.00,  datetime(2026,5,7,0,0,0,tzinfo=timezone(timedelta(hours=-6)))),
    "ASGARI":        (50000.00,  datetime(2026,5,7,0,0,0,tzinfo=timezone(timedelta(hours=-6)))),
    "WILBERT":       (338291.62, datetime(2026,5,11,17,20,0,tzinfo=timezone(timedelta(hours=-6)))),
}

# Retiros confirmados después de cada ancla
RETIROS=[
    # (label, fecha_cdmx, monto)
    ("CLARIBEL", datetime(2026,5,5,12,0,0,tzinfo=timezone(timedelta(hours=-6))), 22405.00),  # ya en ancla
    ("CLARIBEL", datetime(2026,5,10,12,0,0,tzinfo=timezone(timedelta(hours=-6))), 3338.00),
    ("WILBERT",  datetime(2026,5,10,12,0,0,tzinfo=timezone(timedelta(hours=-6))), 18300.00), # ya en ancla
]

ACCOUNTS=[
    ("JUAN","MELI_REFRESH_TOKEN"),
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
    ("BREN","MELI_REFRESH_TOKEN_BREN"),
    ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
    ("RAYMUNDO_MAY","MELI_REFRESH_TOKEN_RAYMUNDO_MAY"),
    ("ANGEL_DAMIAN","MELI_REFRESH_TOKEN_ANGEL_DAMIAN"),
    ("ASGARI","MELI_REFRESH_TOKEN_ASGARI"),
]

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
print(f"=== AUDITORÍA EXACTA — {cdmx.strftime('%d-%m-%Y %H:%M')} CDMX ===\n")

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

results={}
for label,env in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT: continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r:
            results[label]={"err":"refresh"}; continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        uid=me["id"]; nick=me.get("nickname","")
    except Exception as e:
        results[label]={"err":f"auth:{e}"}; continue
    
    anchor_info = ANCHORS.get(label)
    if anchor_info:
        anchor_amount, anchor_date = anchor_info
        date_from_utc = anchor_date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    else:
        # cuentas sin ancla: pull 60d completo
        anchor_amount = 0
        anchor_date = cdmx - timedelta(days=60)
        date_from_utc = anchor_date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    # Pull orders desde anchor
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
    
    refund=0
    for o in cancelled:
        if not is_post(o): continue
        for p in (o.get("payments") or []):
            if p.get("status")=="refunded":
                refund += p.get("transaction_amount_refunded",0) or 0
    
    ship=0.0
    if sids:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs=[ex.submit(get_ship,sid,H) for sid in sids]
            for f in as_completed(futs):
                ship+=f.result()
    
    # Retención MELI 2.28%
    retencion = gross * 0.0228
    
    # NETO delta desde ancla
    neto_delta = gross - fees - ship - refund - retencion
    
    # Retiros desde ancla
    retiros_desde_ancla = 0
    for rl, rd, rm in RETIROS:
        if rl==label and rd > anchor_date:
            retiros_desde_ancla += rm
    
    saldo_final = anchor_amount + neto_delta - retiros_desde_ancla
    
    results[label]={
        "nick":nick,"uid":uid,
        "anchor":anchor_amount, "anchor_date": anchor_date.strftime("%Y-%m-%d %H:%M"),
        "paid":len(paid),"cancelled":len(cancelled),"qty":qty,
        "gross":gross,"fees":fees,"ship":ship,"refund":refund,
        "retencion":retencion,"neto_delta":neto_delta,
        "retiros":retiros_desde_ancla,"saldo":saldo_final
    }
    print(f"{label:<14} ancla=${anchor_amount:>10,.2f} + delta=${neto_delta:>10,.2f} - retiros=${retiros_desde_ancla:>9,.2f} = ${saldo_final:>11,.2f}   ({len(paid)} paid since {anchor_date.strftime('%d-%b')})")

print("\n=== RESUMEN ===")
total_meli=0
for k,v in results.items():
    if "err" in v: 
        print(f"{k:<14} ERROR"); continue
    print(f"  {k:<14}  ${v['saldo']:>13,.2f}")
    total_meli += v['saldo']

print(f"\nTOTAL MELI (suma todas las cuentas): ${total_meli:,.2f}")

print("\n=== JSON ===")
print(json.dumps(results,ensure_ascii=False))
