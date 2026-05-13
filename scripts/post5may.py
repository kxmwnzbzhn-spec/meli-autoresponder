import os, requests
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
ACCOUNTS=[("JUAN","MELI_REFRESH_TOKEN"),("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO")]

ANCHOR=datetime(2026,5,5,0,0,0,tzinfo=timezone(timedelta(hours=-6)))

for label,env in ACCOUNTS:
    RT=os.environ[env]
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me["id"]
    
    print(f"\n━━━━━━ {label} ({me.get('nickname')}) — REFUNDS POST 5-MAY ━━━━━━")
    
    # Pull all orders since 1-abril
    all_orders=[]; offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from=2026-04-01T00:00:00.000Z&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
        res=rr.get("results",[])
        if not res: break
        all_orders.extend(res)
        if len(res)<50: break
        offset+=50
        if offset>10000: break
    
    # Filtrar refunds donde la cancelación fue DESPUÉS del 5-may
    # Para saber cuándo se procesó el refund necesitamos last_updated o date_closed
    
    # En MELI, una orden puede haber sido creada antes pero cancelada/reembolsada después
    # Por lo que usamos date_closed o last_updated de la orden si existe
    
    refunds_post=[]
    refunds_pre=[]
    refunds_unknown=[]
    
    for o in all_orders:
        for p in (o.get("payments") or []):
            ra=p.get("transaction_amount_refunded",0) or 0
            if ra<=0: continue
            
            # Fecha del refund: date_last_updated del payment o de la orden
            refund_date_str=p.get("date_last_modified") or p.get("money_release_date") or o.get("last_updated") or o.get("date_created","")
            
            try:
                if refund_date_str:
                    refund_dt=datetime.fromisoformat(refund_date_str.replace("Z","+00:00")).astimezone(timezone(timedelta(hours=-6)))
                    if refund_dt > ANCHOR:
                        refunds_post.append({
                            "order":o.get("id"),"date":refund_date_str[:10],"amount":ra,
                            "reason":(o.get("cancel_detail") or {}).get("description","")[:50]
                        })
                    else:
                        refunds_pre.append(ra)
                else:
                    refunds_unknown.append(ra)
            except:
                refunds_unknown.append(ra)
    
    total_post=sum(r["amount"] for r in refunds_post)
    total_pre=sum(refunds_pre)
    total_unk=sum(refunds_unknown)
    
    print(f"  Refunds POST 5-may (afectaron saldo): ${total_post:,.2f}  ({len(refunds_post)} órdenes)")
    print(f"  Refunds PRE 5-may  (ya en ancla):     ${total_pre:,.2f}  ({len(refunds_pre)} órdenes)")
    print(f"  Refunds sin fecha clara:              ${total_unk:,.2f}  ({len(refunds_unknown)} órdenes)")
    
    print(f"\n  TOP 15 refunds POST 5-may:")
    for rd in sorted(refunds_post,key=lambda x:-x["amount"])[:15]:
        print(f"    {rd['date']} ${rd['amount']:>8,.2f}  order={rd['order']} reason={rd['reason']}")
    
    print(f"\n  Sumarizado por motivo (post 5-may):")
    by_reason={}
    for rd in refunds_post:
        r=rd["reason"] or "(sin motivo)"
        by_reason.setdefault(r,{"n":0,"t":0})
        by_reason[r]["n"]+=1
        by_reason[r]["t"]+=rd["amount"]
    for r,d in sorted(by_reason.items(),key=lambda x:-x[1]["t"]):
        print(f"    ${d['t']:>9,.2f}  {d['n']:>3}x  {r}")
