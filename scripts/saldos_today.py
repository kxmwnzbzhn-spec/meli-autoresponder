import os, requests, json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

# EXCLUYE ASVA por petición
ACCOUNTS=[
    ("JUAN","MELI_REFRESH_TOKEN", 0),       # baseline se aplica abajo
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO", 0),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL", -22405.00),  # retiro a Asva
    ("WILBERT","MELI_REFRESH_TOKEN_WILBERT", 0),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE", 0),
    ("MILDRED","MELI_REFRESH_TOKEN_MILDRED", 0),
    ("BREN","MELI_REFRESH_TOKEN_BREN", 0),
    ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW", 0),
]

# Juan tiene cuenta OLD, su saldo MP de 5-may era $120,942 (snapshot real del usuario)
# Para Juan se calcula: saldo_5may + activity_desde_5may
JUAN_BASELINE_5MAY = 120942.00
DATE_BASELINE = datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6)))  # 5-may 00:00 CDMX

cdmx=datetime.now(timezone.utc)-timedelta(hours=6)
since=cdmx-timedelta(days=60)
date_from_60=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
date_from_juan = (DATE_BASELINE.astimezone(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"=== SALDOS PROYECTADOS HOY {cdmx.strftime('%d-%m-%Y %H:%M')} CDMX ===")
print(f"60d window: {date_from_60}")
print(f"Juan baseline: $120,942 al 5-may, acumular desde {date_from_juan}\n")

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

results={}

def is_post_release_refund(o):
    """Heuristic: refund affected MP saldo if cancel reason indicates post-delivery dispute."""
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    if "mediation" in desc: return True
    if "cancel_purchase" in desc: return True
    if "feedback from buyer" in desc: return True
    return False  # default: assume pre-release, didn't take from MP

for label,env,retiro in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT:
        results[label]={"err":"no token"}; continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r:
            results[label]={"err":"refresh fail"}; continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        uid=me["id"]; nick=me.get("nickname","")
    except Exception as e:
        results[label]={"err":f"auth:{e}"}; continue
    
    # Para Juan: solo desde 5-may. Para otros: 60d.
    df = date_from_juan if label=="JUAN" else date_from_60
    
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
    
    # Refunds (solo post-release, heurística)
    refund_real=0; refund_total_all=0
    cancel_post=cancel_pre=0
    for o in cancelled:
        order_refund=0
        for p in (o.get("payments") or []):
            if p.get("status")=="refunded":
                ra=p.get("transaction_amount_refunded",0) or 0
                order_refund+=ra
        refund_total_all+=order_refund
        if is_post_release_refund(o):
            refund_real+=order_refund; cancel_post+=1
        else:
            cancel_pre+=1
    
    # Shipping cost (paralelo)
    ship_total=0.0
    if sids:
        with ThreadPoolExecutor(max_workers=15) as ex:
            futs=[ex.submit(get_ship_cost, sid, H) for sid in sids]
            for f in as_completed(futs):
                ship_total+=f.result()
    
    neto = gross - fees - ship_total - refund_real
    
    # Saldo proyectado: para Juan suma baseline; para otros es directamente NETO + retiro
    if label=="JUAN":
        saldo = JUAN_BASELINE_5MAY + neto + retiro
    else:
        saldo = neto + retiro
    
    print(f"--- {label} ({nick}) ---")
    print(f"  paid={len(paid)} canc_pre={cancel_pre} canc_post={cancel_post}")
    print(f"  Bruto:        ${gross:>13,.2f}")
    print(f"  Comis:       -${fees:>13,.2f}")
    print(f"  Envío seller:-${ship_total:>13,.2f}")
    print(f"  Refunds (post-release):-${refund_real:>13,.2f}  (de ${refund_total_all:,.2f} total refunded en API)")
    print(f"  NETO periodo: ${neto:>13,.2f}")
    if label=="JUAN":
        print(f"  + Baseline 5-may: ${JUAN_BASELINE_5MAY:,.2f}")
    if retiro:
        print(f"  + Retiro:    ${retiro:,.2f}")
    print(f"  >>> SALDO PROYECTADO HOY: ${saldo:>13,.2f}\n")
    
    results[label]={"nick":nick,"uid":uid,"paid":len(paid),"cancelled":len(cancelled),
                    "cancel_pre":cancel_pre,"cancel_post":cancel_post,
                    "gross":gross,"fees":fees,"ship":ship_total,
                    "refund_real":refund_real,"refund_total_all":refund_total_all,
                    "neto":neto,"retiro":retiro,"saldo":saldo}

# Resumen
print("\n=== RESUMEN ===")
print(f"{'Cuenta':<10} {'Órd':>4} {'Bruto':>14} {'Costos':>14} {'Refund':>11} {'NETO/Periodo':>14} {'Retiro':>10} {'SALDO HOY':>14}")
print("-"*110)
total=0
for k,v in results.items():
    if "err" in v:
        print(f"{k:<10} {v['err']}")
        continue
    costos = v['fees']+v['ship']
    print(f"{k:<10} {v['paid']:>4} ${v['gross']:>13,.2f} ${costos:>13,.2f} ${v['refund_real']:>10,.2f} ${v['neto']:>13,.2f} ${v['retiro']:>9,.2f} ${v['saldo']:>13,.2f}")
    total+=v.get('saldo',0)
print("-"*110)
print(f"{'TOTAL':<10} {'':<4} {'':<14} {'':<14} {'':<11} {'':<14} {'':<10} ${total:>13,.2f}")

print(f"\n=== JSON ===")
print(json.dumps(results,ensure_ascii=False))
