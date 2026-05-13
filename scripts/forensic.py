import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

ACCOUNTS=[
    ("JUAN",     "MELI_REFRESH_TOKEN"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
]

for label, env in ACCOUNTS:
    RT=os.environ[env]
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me["id"]
    
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"FORENSIC AUDIT: {label} / {me.get('nickname')} / UID {uid}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # 1) Pull ALL orders since 1-april para revisar TODO el flujo
    date_from="2026-04-01T00:00:00.000Z"
    
    all_orders=[]; offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=30).json()
        res=rr.get("results",[])
        if not res: break
        all_orders.extend(res)
        if len(res)<50: break
        offset+=50
        if offset>10000: break
    
    print(f"\n📋 Total órdenes desde 1-abr: {len(all_orders)}")
    
    # 2) Análisis exhaustivo de payments con cualquier amount refunded > 0
    print(f"\n💰 TODOS los payments con transaction_amount_refunded > 0:")
    total_refunded_all=0; refund_details=[]
    for o in all_orders:
        for p in (o.get("payments") or []):
            ra=p.get("transaction_amount_refunded",0) or 0
            if ra>0:
                total_refunded_all += ra
                refund_details.append({
                    "order":o.get("id"),"date":o.get("date_created","")[:10],
                    "status_order":o.get("status",""), "status_payment":p.get("status",""),
                    "refund":ra,
                    "cancel_reason":(o.get("cancel_detail") or {}).get("description","")
                })
    print(f"   Total reembolsado (cualquier estado): ${total_refunded_all:,.2f}  ({len(refund_details)} payments)")
    
    by_status={}
    for rd in refund_details:
        k=rd["status_order"]+"/"+rd["status_payment"]
        by_status.setdefault(k,{"count":0,"total":0})
        by_status[k]["count"]+=1
        by_status[k]["total"]+=rd["refund"]
    print(f"   Por estado (orden/payment):")
    for k,v in sorted(by_status.items(),key=lambda x:-x[1]["total"]):
        print(f"     {k:<40}  {v['count']:>3}x  ${v['total']:>10,.2f}")
    
    # 3) Claims abiertas (que pueden haber deducido)
    print(f"\n⚖️  CLAIMS:")
    for st in ["opened","closed","with_refund"]:
        c=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?status={st}&limit=50",headers=H,timeout=20).json()
        if isinstance(c,dict):
            total=c.get('paging',{}).get('total','?')
            print(f"   status={st}: {total} total")
    
    # 4) Probar endpoint de movements de cuenta (si existe)
    print(f"\n💸 MOVIMIENTOS DE CUENTA (probing):")
    for ep in [f"/users/{uid}/accounting/movement/search?limit=10",
               f"/users/{uid}/account/movements?limit=10",
               f"/sites/MLM/seller-accounting/{uid}/movements?limit=10"]:
        try:
            r=requests.get(f"https://api.mercadolibre.com{ep}",headers=H,timeout=10)
            print(f"   {ep[:60]}: {r.status_code}")
            if r.status_code==200:
                print(f"     {r.text[:400]}")
        except Exception as e:
            print(f"   {ep[:60]}: ERR {e}")
    
    # 5) Buscar status_detail con refund pendiente
    print(f"\n📝 ÓRDENES CON STATUS_DETAIL ESPECIAL:")
    sd_counts={}
    for o in all_orders:
        sd=o.get("status_detail") or "—"
        if sd!="—":
            sd_counts[sd]=sd_counts.get(sd,0)+1
    for sd,c in sd_counts.items():
        print(f"   {sd:<50}  {c}x")
    
    # 6) Si hay refund_details, listar los más grandes
    print(f"\n🔍 TOP 10 REFUNDS POR MONTO:")
    for rd in sorted(refund_details,key=lambda x:-x["refund"])[:10]:
        print(f"   {rd['date']}  ${rd['refund']:>8,.2f}  {rd['status_order']:<10}/{rd['status_payment']:<10}  reason={rd['cancel_reason'][:50]}")
