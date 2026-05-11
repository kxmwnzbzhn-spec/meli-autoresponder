import os, requests, json
from concurrent.futures import ThreadPoolExecutor, as_completed

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

SALDOS_USER={"JUAN":120942.00,"RAYMUNDO":338000.00,"CLARIBEL":34517.00,
             "RAYMUNDO_MAY":81126.00,"ANGEL_DAMIAN":60000.00,"ASGARI":50000.00}

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

def fetch_order_amount(oid, H):
    try:
        r=requests.get(f"https://api.mercadolibre.com/orders/{oid}",headers=H,timeout=10)
        if r.status_code==200:
            return float(r.json().get("total_amount",0) or 0)
    except: pass
    return 0.0

print(f"=== AUDITORÍA v2 — disputas REALMENTE abiertas ===\n")

results={}
for label,env in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT: continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r: continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        uid=me["id"]; nick=me.get("nickname")
    except: continue
    
    # Pull SOLO claims opened
    claims_open=[]; offset=0
    while True:
        c=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&limit=50&offset={offset}",headers=H,timeout=30).json()
        if not isinstance(c,dict): break
        items=c.get('data') or []
        if not items: break
        claims_open.extend(items)
        if len(items)<50: break
        offset+=50
        if offset>2000: break
    
    # Para cada claim opened, obtener el total_amount de la orden
    order_ids=[]
    for cl in claims_open:
        if cl.get("resource")=="order" and cl.get("resource_id"):
            order_ids.append(cl.get("resource_id"))
    
    # Fetch amounts en paralelo
    total_at_risk=0
    if order_ids:
        with ThreadPoolExecutor(max_workers=15) as ex:
            futs=[ex.submit(fetch_order_amount, oid, H) for oid in order_ids]
            for f in as_completed(futs):
                total_at_risk += f.result()
    
    saldo = SALDOS_USER.get(label, 0)
    if label=="WILBERT": saldo = 223937.34  # de cálculo anterior
    
    realizable = saldo - total_at_risk
    
    results[label]={"nick":nick,"saldo":saldo,
                    "claims_opened":len(claims_open),
                    "amount_at_risk":total_at_risk,
                    "realizable":realizable}
    print(f"{label:<14} saldo=${saldo:>11,.2f}  claims opened={len(claims_open):>3}  en riesgo=${total_at_risk:>10,.2f}  realizable=${realizable:>11,.2f}")

print("\n=== TOTALES ===")
T={"saldo":0,"risk":0,"real":0,"open":0}
for v in results.values():
    T['saldo']+=v['saldo']; T['risk']+=v['amount_at_risk']
    T['real']+=v['realizable']; T['open']+=v['claims_opened']
print(f"Saldo total:        ${T['saldo']:>13,.2f}")
print(f"Claims opened:       {T['open']}")
print(f"Total en riesgo:    ${T['risk']:>13,.2f}")
print(f"NETO realizable:    ${T['real']:>13,.2f}")

print("\n=== JSON ===")
print(json.dumps({"results":results,"totals":T},ensure_ascii=False))
