import os,requests,json
from datetime import datetime,timedelta
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me.get("id")
print(f"User: {me.get('nickname')} id={uid}")

# Todos los paid orders con release date
from datetime import datetime, timezone
now=datetime.now(timezone.utc)

total_pagado=0
retenido=0
disponible=0
count=0
offset=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=paid&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=20).json()
    results=r.get("results",[])
    if not results: break
    for o in results:
        for p in o.get("payments",[]):
            if p.get("status") != "approved": continue
            amt = p.get("transaction_amount",0) - p.get("fee_details",[{}])[0].get("amount",0) if p.get("fee_details") else p.get("transaction_amount",0)
            total_pagado += p.get("transaction_amount",0)
            # Release date
            rel=p.get("money_release_date")
            if rel:
                try:
                    rel_dt=datetime.fromisoformat(rel.replace("Z","+00:00"))
                    if rel_dt <= now:
                        disponible += p.get("transaction_amount",0)
                    else:
                        retenido += p.get("transaction_amount",0)
                except: pass
            count+=1
    offset+=50
    if offset>=r.get("paging",{}).get("total",0): break
    if offset>=500: break  # cap

print(f"\nOrdenes paid approved: {count}")
print(f"Total pagado histórico: ${total_pagado:,.2f}")
print(f"Ya disponible (release_date pasó): ${disponible:,.2f}")
print(f"Retenido (release_date futura): ${retenido:,.2f}")

# Revisar saldo en billing
r=requests.get("https://api.mercadolibre.com/billing/integration/MLM/group/MARKETPLACE/summary?date_start=2026-04-01&date_end=2026-04-22",headers=H,timeout=20)
print(f"\nbilling summary abril: {r.status_code} {r.text[:500]}")
