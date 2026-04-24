import os,requests,json,time

ACCOUNTS={
    "JUAN":os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL":os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO":os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
}

REPORT={}
for label,rt in ACCOUNTS.items():
    if not rt: 
        REPORT[label]={"error":"sin token"}; continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" not in r:
        REPORT[label]={"error":"refresh failed"}; continue
    TOKEN=r["access_token"]
    H={"Authorization":f"Bearer {TOKEN}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    USER_ID=me["id"]
    nick=me.get("nickname")
    
    # Reputation
    rep=me.get("seller_reputation") or {}
    rep_level=rep.get("level_id","sin data")
    power_seller=rep.get("power_seller_status")
    
    # Items por status
    active=paused=closed=0
    for st in ("active","paused","closed"):
        s=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=1",headers=H,timeout=15).json()
        t=s.get("paging",{}).get("total",0)
        if st=="active": active=t
        elif st=="paused": paused=t
        elif st=="closed": closed=t
    
    # Preguntas pendientes
    q=requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={USER_ID}&status=UNANSWERED&limit=1",headers=H,timeout=15).json()
    q_pending=q.get("total",0) if isinstance(q.get("total"),int) else len(q.get("questions") or [])
    
    # Claims abiertos
    c=requests.get("https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&limit=50",headers=H,timeout=15).json()
    claims_open=len(c.get("data") or [])
    claims_details=[]
    for cl in (c.get("data") or [])[:10]:
        claims_details.append(f"{cl.get('id')} ({cl.get('reason_id')})")
    
    # Ordenes pendientes (sin enviar)
    o=requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.status=paid&limit=50",headers=H,timeout=15).json()
    orders_paid=o.get("paging",{}).get("total",0) or len(o.get("results") or [])
    
    # Mensajes pendientes por responder
    # (skip, no es muy fiable via api publica)
    
    REPORT[label]={
        "nickname":nick,"user_id":USER_ID,
        "reputation":rep_level,"power_seller":power_seller,
        "items":{"active":active,"paused":paused,"closed":closed},
        "questions_pending":q_pending,
        "claims_open":claims_open,"claims_detail":claims_details,
        "orders_paid":orders_paid,
    }

print(json.dumps(REPORT,ensure_ascii=False,indent=2))
