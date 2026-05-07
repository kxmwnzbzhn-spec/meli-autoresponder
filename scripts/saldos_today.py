import os, requests, json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

# Anclas: snapshot real 5-may CDMX (00:00) confirmados por el usuario
# Para esas cuentas: saldo_today = snapshot + delta_5may_to_today
# Wilbert no tiene snapshot, se calcula con 60d completo
ANCHOR_5MAY = {
    "JUAN": 120942.00,
    "RAYMUNDO": 338000.00,
    "CLARIBEL": 34517.00,  # ya post retiro de Claribel a Asva del 5-may
}

ACCOUNTS=[
    ("JUAN","MELI_REFRESH_TOKEN"),
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
    ("BREN","MELI_REFRESH_TOKEN_BREN"),
    ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
]

# Para cuentas con ancla: from = 5-may 00:00 CDMX
DT_5MAY_UTC = datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6))).astimezone(timezone.utc)
date_from_anchor = DT_5MAY_UTC.strftime("%Y-%m-%dT%H:%M:%S.000Z")
# Para Wilbert: 60d
cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since60=cdmx-timedelta(days=60)
date_from_60=since60.strftime("%Y-%m-%dT%H:%M:%S.000Z")

print(f"=== SALDOS PROYECTADOS HOY {cdmx.strftime('%d-%m-%Y %H:%M')} CDMX ===")
print(f"Anclas 5-may: Juan ${ANCHOR_5MAY['JUAN']:,.2f}, Raymundo ${ANCHOR_5MAY['RAYMUNDO']:,.2f}, Claribel ${ANCHOR_5MAY['CLARIBEL']:,.2f}")
print(f"Para cuentas con ancla: delta desde {date_from_anchor}")
print(f"Wilbert (sin ancla): 60d desde {date_from_60}\n")

def get_ship_cost(sid, headers):
    if not sid: return 0.0
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=headers,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json()
        s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

def is_post_release(o):
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    return ("mediation" in desc) or ("cancel_purchase" in desc) or ("buyer" in desc)

results={}
for label,env in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT: results[label]={"err":"no token"}; continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r: results[label]={"err":"refresh fail"}; continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        uid=me["id"]; nick=me.get("nickname","")
    except Exception as e:
        results[label]={"err":f"auth:{e}"}; continue
    
    df = date_from_anchor if label in ANCHOR_5MAY else date_from_60
    has_anchor = label in ANCHOR_5MAY
    
    orders=[]; offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={df}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
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
    
    refund_real=0
    for o in cancelled:
        if not is_post_release(o): continue
        for p in (o.get("payments") or []):
            if p.get("status")=="refunded":
                refund_real += p.get("transaction_amount_refunded",0) or 0
    
    ship_total=0.0
    if sids:
        with ThreadPoolExecutor(max_workers=15) as ex:
            futs=[ex.submit(get_ship_cost, sid, H) for sid in sids]
            for f in as_completed(futs):
                ship_total+=f.result()
    
    neto_periodo = gross - fees - ship_total - refund_real
    
    if has_anchor:
        anchor = ANCHOR_5MAY[label]
        saldo = anchor + neto_periodo
        method = f"ancla 5-may + delta"
    else:
        saldo = neto_periodo
        method = "60d completo (sin ancla)"
    
    print(f"--- {label} ({nick}) — {method} ---")
    print(f"  paid_periodo={len(paid)}  cancelled_periodo={len(cancelled)}")
    print(f"  Bruto:        ${gross:>13,.2f}")
    print(f"  Comis:       -${fees:>13,.2f}")
    print(f"  Envío seller:-${ship_total:>13,.2f}")
    print(f"  Refund post-release:-${refund_real:>13,.2f}")
    print(f"  NETO periodo: ${neto_periodo:>13,.2f}")
    if has_anchor:
        print(f"  + Ancla 5-may:${ANCHOR_5MAY[label]:>12,.2f}")
    print(f"  >>> SALDO HOY: ${saldo:>13,.2f}\n")
    
    results[label]={"nick":nick,"uid":uid,"has_anchor":has_anchor,
                    "paid":len(paid),"cancelled":len(cancelled),
                    "gross":gross,"fees":fees,"ship":ship_total,"refund":refund_real,
                    "neto_periodo":neto_periodo,"anchor":ANCHOR_5MAY.get(label,0),"saldo":saldo}

# Resumen
print("\n=== RESUMEN — Saldo proyectado HOY ===")
print(f"{'Cuenta':<10} {'Método':<28} {'Saldo':>14}")
print("-"*60)
total=0
for k,v in results.items():
    if "err" in v: 
        print(f"{k:<10} {v['err']}"); continue
    m="ancla 5-may + delta" if v['has_anchor'] else "60d (sin ancla)"
    print(f"{k:<10} {m:<28} ${v['saldo']:>13,.2f}")
    total+=v['saldo']
print("-"*60)
print(f"{'TOTAL':<10} {'(excluyendo Asva)':<28} ${total:>13,.2f}")

print("\n=== JSON ===")
print(json.dumps(results,ensure_ascii=False))
