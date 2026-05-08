import os, requests, json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

# Excluyendo Asva por petición previa
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

# Esta semana: lunes 4-may CDMX 00:00 a ahora
cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
# Calcular lunes de esta semana
days_since_monday=cdmx.weekday()  # Monday=0
monday_cdmx=(cdmx-timedelta(days=days_since_monday)).replace(hour=0,minute=0,second=0,microsecond=0)
monday_utc=monday_cdmx+timedelta(hours=6)
date_from=monday_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"=== GANANCIAS SEMANA (lun {monday_cdmx.strftime('%d-%b')} a {cdmx.strftime('%d-%b %H:%M')} CDMX) ===")
print(f"date_from = {date_from}\n")

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
    
    orders=[]; offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
        res=rr.get("results",[])
        if not res: break
        orders.extend(res)
        if len(res)<50: break
        offset+=50
    
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
        with ThreadPoolExecutor(max_workers=15) as ex:
            futs=[ex.submit(get_ship,sid,H) for sid in sids]
            for f in as_completed(futs):
                ship+=f.result()
    
    iva = (gross-refund) * 0.16 / 1.16 if (gross-refund)>0 else 0
    neto_mp = gross - fees - ship - refund
    neto_real = neto_mp - iva
    
    results[label]={"nick":nick,"uid":uid,"paid":len(paid),"cancelled":len(cancelled),"qty":qty,
                    "gross":gross,"fees":fees,"ship":ship,"refund":refund,"iva":iva,
                    "neto_mp":neto_mp,"neto_real":neto_real}
    print(f"{label:<14} órd={len(paid):>3} un={qty:>3} bruto=${gross:>10,.2f} comis=-${fees:>9,.2f} envío=-${ship:>8,.2f} refund=-${refund:>8,.2f} IVA=-${iva:>8,.2f} NETO MP=${neto_mp:>10,.2f} NETO Real=${neto_real:>10,.2f}")

print(f"\n=== TOTAL SEMANA ===")
T={k:0 for k in ['gross','fees','ship','refund','iva','neto_mp','neto_real','q','o']}
for k,v in results.items():
    if "err" in v: continue
    T['gross']+=v['gross']; T['fees']+=v['fees']; T['ship']+=v['ship']
    T['refund']+=v['refund']; T['iva']+=v['iva']
    T['neto_mp']+=v['neto_mp']; T['neto_real']+=v['neto_real']
    T['q']+=v['qty']; T['o']+=v['paid']

print(f"  Órdenes:   {T['o']}")
print(f"  Unidades:  {T['q']}")
print(f"  Bruto:        ${T['gross']:>12,.2f}")
print(f"  Comis MELI:  -${T['fees']:>12,.2f}")
print(f"  Envío seller:-${T['ship']:>12,.2f}")
print(f"  Refunds:     -${T['refund']:>12,.2f}")
print(f"  IVA 16%:     -${T['iva']:>12,.2f}")
print(f"  ────────────────────────")
print(f"  NETO MP:      ${T['neto_mp']:>12,.2f}")
print(f"  NETO REAL:    ${T['neto_real']:>12,.2f}  ← lo que realmente ganamos esta semana")

print("\n=== JSON ===")
print(json.dumps({"period":f"{monday_cdmx.strftime('%Y-%m-%d')} to {cdmx.strftime('%Y-%m-%d %H:%M')}","results":results,"totals":T},ensure_ascii=False))
