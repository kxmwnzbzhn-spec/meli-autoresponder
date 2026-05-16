import os, requests, json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

# Anclas validadas con snapshots reales del Sr. Luis
ACCOUNTS=[
    ("JUAN",         "MELI_REFRESH_TOKEN",              120942.00, datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6))), 89865.00),
    ("RAYMUNDO",     "MELI_REFRESH_TOKEN_RAYMUNDO",     29000.00,  datetime(2026,5,15,9,14,0,tzinfo=timezone(timedelta(hours=-6))), 0.00),  # nuevo ancla post-retiro
    ("CLARIBEL",     "MELI_REFRESH_TOKEN_CLARIBEL",     34517.00,  datetime(2026,5,5,23,59,0,tzinfo=timezone(timedelta(hours=-6))), 3338.00),
    ("WILBERT",      "MELI_REFRESH_TOKEN_WILBERT",      338291.62, datetime(2026,5,11,17,20,0,tzinfo=timezone(timedelta(hours=-6))), 31018.00+42797.00),
    ("RAYMUNDO_MAY", "MELI_REFRESH_TOKEN_RAYMUNDO_MAY", 81126.00,  datetime(2026,5,7,0,0,0,tzinfo=timezone(timedelta(hours=-6))), 0.00),
    ("ANGEL_DAMIAN", "MELI_REFRESH_TOKEN_ANGEL_DAMIAN", 60000.00,  datetime(2026,5,7,0,0,0,tzinfo=timezone(timedelta(hours=-6))), 0.00),
    ("ASGARI",       "MELI_REFRESH_TOKEN_ASGARI",       50000.00,  datetime(2026,5,7,0,0,0,tzinfo=timezone(timedelta(hours=-6))), 0.00),
]

def get_ship(sid,h):
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json(); s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
print(f"=== AUDITORÍA — {cdmx.strftime('%d-%m-%Y %H:%M')} CDMX ===\n")

results={}
for label, env, anchor_amt, anchor_dt, retiros in ACCOUNTS:
    RT=os.environ.get(env)
    if not RT: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
    if "access_token" not in r: continue
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me["id"]
    
    orders=[]; offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from=2026-04-01T00:00:00.000Z&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
        res=rr.get("results",[])
        if not res: break
        orders.extend(res)
        if len(res)<50: break
        offset+=50
        if offset>10000: break
    
    gross=fees=qty=0; sids=[]
    for o in orders:
        if o.get("status") not in ("paid","shipped","delivered"): continue
        try:
            o_dt=datetime.fromisoformat(o.get("date_created","").replace("Z","+00:00")).astimezone(timezone(timedelta(hours=-6)))
            if o_dt <= anchor_dt: continue
        except: continue
        for it in o.get("order_items",[]):
            q=it.get("quantity",0) or 0
            gross+=(it.get("unit_price",0) or 0)*q
            fees+=(it.get("sale_fee",0) or 0)*q
            qty+=q
        sid=(o.get("shipping",{}) or {}).get("id")
        if sid: sids.append(sid)
    
    refund=0
    for o in orders:
        for p in (o.get("payments") or []):
            if p.get("status")!="refunded": continue
            ra=p.get("transaction_amount_refunded",0) or 0
            if ra<=0: continue
            d_str=p.get("date_last_modified") or o.get("last_updated") or o.get("date_created","")
            try:
                d=datetime.fromisoformat(d_str.replace("Z","+00:00")).astimezone(timezone(timedelta(hours=-6)))
                if d > anchor_dt: refund += ra
            except: pass
    
    ship=0.0
    if sids:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs=[ex.submit(get_ship,sid,H) for sid in sids]
            for f in as_completed(futs):
                ship+=f.result()
    
    retencion = gross * 0.0228
    neto_delta = gross - fees - ship - refund - retencion
    saldo_final = anchor_amt + neto_delta - retiros
    
    results[label]={"saldo":saldo_final,"anchor":anchor_amt,"gross":gross,"fees":fees,"ship":ship,"refund":refund,"qty":qty,"retiros":retiros}
    print(f"{label:<14} ancla=${anchor_amt:>10,.2f} delta=${neto_delta:>11,.2f} retiros=${retiros:>9,.2f} = ${saldo_final:>11,.2f}")

total=sum(v.get('saldo',0) for v in results.values() if 'err' not in v)
print(f"\nTOTAL MELI: ${total:,.2f}")
print("\n=== JSON ===")
print(json.dumps(results,ensure_ascii=False))
