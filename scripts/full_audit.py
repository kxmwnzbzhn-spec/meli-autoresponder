import os, requests, json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

# Saldos confirmados por el usuario (snapshots post-IVA)
SALDOS_USER={
    "JUAN":120942.00,
    "RAYMUNDO":338000.00,
    "CLARIBEL":34517.00,  # post-retiro a Asva
    "RAYMUNDO_MAY":81126.00,
    "ANGEL_DAMIAN":60000.00,
    "ASGARI":50000.00,
}

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
since=cdmx-timedelta(days=90)
date_from=since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"=== AUDITORÍA COMPLETA — {cdmx.strftime('%d-%m-%Y %H:%M')} CDMX ===\n")

def get_ship(sid,h):
    try:
        r=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=h,timeout=10)
        if r.status_code!=200: return 0.0
        j=r.json(); s=j.get("senders",[])
        if isinstance(s,list): return float(sum(x.get("cost",0) or 0 for x in s))
        return float(s.get("cost",0) or 0)
    except: return 0.0

def is_post(o):
    cd=o.get("cancel_detail") or {}
    desc=(cd.get("description") or "").lower()
    return ("mediation" in desc) or ("cancel_purchase" in desc) or ("buyer" in desc)

results={}
for label,env in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT: 
        results[label]={"err":"no token"}; continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r:
            results[label]={"err":"refresh"}; continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        uid=me["id"]; nick=me.get("nickname","")
    except Exception as e:
        results[label]={"err":f"auth:{e}"}; continue
    
    # Active claims (disputas abiertas, potencial deducción al saldo)
    claims_open=0; claims_amount=0
    try:
        c=requests.get("https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&limit=50",headers=H,timeout=20).json()
        if isinstance(c,dict):
            claims_open=len(c.get("data") or [])
            # Estimate amount (varía, no siempre viene)
            for cl in (c.get("data") or []):
                amt=cl.get("amount") or (cl.get("resource_id") and 0)
                claims_amount += float(amt) if isinstance(amt,(int,float)) else 0
    except: pass
    
    # Recent orders with pending payments / pending refunds
    orders=[]; offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
        res=rr.get("results",[])
        if not res: break
        orders.extend(res)
        if len(res)<50: break
        offset+=50
        if offset>5000: break
    
    # Active mediations / pending refunds: orders with status paid but with mediations array non-empty
    active_med=[]
    pending_refund_amount=0
    for o in orders:
        meds=o.get("mediations") or []
        if meds and o.get("status") in ("paid","shipped","delivered"):
            for it in o.get("order_items",[]):
                pending_refund_amount += (it.get("unit_price",0) or 0) * (it.get("quantity",0) or 0)
            active_med.append(o.get("id"))
    
    # For Wilbert: compute NETO real desde inicio
    saldo_confirmed = SALDOS_USER.get(label)
    if saldo_confirmed is None and label=="WILBERT":
        # Compute properly
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
                    refund+=p.get("transaction_amount_refunded",0) or 0
        ship=0.0
        if sids:
            with ThreadPoolExecutor(max_workers=15) as ex:
                futs=[ex.submit(get_ship,sid,H) for sid in sids]
                for f in as_completed(futs):
                    ship+=f.result()
        iva=(gross-refund)*0.16/1.16 if (gross-refund)>0 else 0
        saldo_calc = gross - fees - ship - refund - iva
        saldo_confirmed = saldo_calc
        results[label]={"nick":nick,"saldo":saldo_calc,"source":"calculated (post-IVA)",
                        "claims_open":claims_open,"active_med":len(active_med),"pending_refund":pending_refund_amount,
                        "neto_realizable":saldo_calc - pending_refund_amount}
    elif saldo_confirmed is not None:
        results[label]={"nick":nick,"saldo":saldo_confirmed,"source":"snapshot user (post-IVA)",
                        "claims_open":claims_open,"active_med":len(active_med),"pending_refund":pending_refund_amount,
                        "neto_realizable":saldo_confirmed - pending_refund_amount}
    else:
        # cuentas sin ventas (Dilcie, Bren, YC_NEW)
        results[label]={"nick":nick,"saldo":0,"source":"sin ventas",
                        "claims_open":claims_open,"active_med":len(active_med),"pending_refund":pending_refund_amount,
                        "neto_realizable":0}

# Print table
print(f"{'Cuenta':<14} {'Saldo MP':>13} {'Med abiertas':>13} {'Refund pend':>13} {'NETO realiz.':>15}")
print("-"*75)
T={"saldo":0,"pend":0,"realiz":0,"med":0,"claims":0}
for k,_ in ACCOUNTS:
    if k=="ASVA": continue  # excluida
    v=results.get(k,{})
    if "err" in v:
        print(f"{k:<14} ERR: {v['err']}"); continue
    print(f"{k:<14} ${v['saldo']:>12,.2f} {v['active_med']:>13} ${v['pending_refund']:>12,.2f} ${v['neto_realizable']:>14,.2f}")
    T['saldo']+=v['saldo']; T['pend']+=v['pending_refund']; T['realiz']+=v['neto_realizable']
    T['med']+=v['active_med']; T['claims']+=v['claims_open']
print("-"*75)
print(f"{'TOTAL':<14} ${T['saldo']:>12,.2f} {T['med']:>13} ${T['pend']:>12,.2f} ${T['realiz']:>14,.2f}")
print(f"\nClaims abiertos en total: {T['claims']}")
print(f"\nNOTA: 'Refund pending' = órdenes con mediations en curso que podrían reembolsarse.")

print("\n=== JSON ===")
print(json.dumps({"results":results,"totals":T},ensure_ascii=False))
