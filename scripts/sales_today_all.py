import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN","MELI_REFRESH_TOKEN"),
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
    ("BREN","MELI_REFRESH_TOKEN_BREN"),
    ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
    ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
    ("OFICIAL","MELI_REFRESH_TOKEN_OFICIAL"),
]

cdmx = datetime.now(timezone.utc) - timedelta(hours=6)
midnight_cdmx = cdmx.replace(hour=0, minute=0, second=0, microsecond=0)
midnight_utc = midnight_cdmx + timedelta(hours=6)
date_from = midnight_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
today = cdmx.strftime("%d/%m/%Y")
print(f"=== VENTAS HOY {today} ({cdmx.strftime('%H:%M')} CDMX) ===")
print(f"Desde {date_from}")
print()

g_gross=g_fees=g_net=g_qty=0; g_orders=0; g_cancelled=0
table=[]
top_models={}

for label, env in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT:
        table.append((label, "NO TOKEN", 0, 0, 0, 0, 0))
        continue
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
        if "access_token" not in r:
            table.append((label, f"REFRESH FAIL: {r.get('message','?')}", 0,0,0,0,0)); continue
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        uid=me["id"]; nick=me.get("nickname","")
    except Exception as e:
        table.append((label, f"AUTH ERR: {e}",0,0,0,0,0)); continue
    
    a_gross=a_fees=a_qty=0; a_orders=0
    offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={offset}",headers=H,timeout=20).json()
        res=rr.get("results",[])
        if not res: break
        for o in res:
            st=o.get("status","")
            if st in ("paid","shipped","delivered"):
                a_orders+=1
                for it in o.get("order_items",[]):
                    q=it.get("quantity",0) or 0
                    up=it.get("unit_price",0) or 0
                    sf=it.get("sale_fee",0) or 0
                    a_gross+= up*q
                    a_fees += sf*q
                    a_qty  += q
                    title=it.get("item",{}).get("title","")[:50]
                    if title:
                        e=top_models.setdefault(title,{"u":0,"r":0})
                        e["u"]+=q; e["r"]+=up*q
        if len(res)<50: break
        offset+=50
    
    # Cancelled today
    c_count=0
    cr=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=cancelled&order.date_created.from={date_from}&limit=50",headers=H,timeout=20).json()
    c_count=cr.get("paging",{}).get("total",0) or len(cr.get("results",[]))
    
    a_net = a_gross - a_fees
    table.append((label, nick, a_orders, a_qty, a_gross, a_fees, a_net))
    g_gross+=a_gross; g_fees+=a_fees; g_qty+=a_qty; g_orders+=a_orders; g_cancelled+=c_count

g_net=g_gross-g_fees
print(f"{'Cuenta':<10} {'Nick':<28} {'Órd':>4} {'U':>4} {'Bruto':>12} {'Comis':>10} {'NETO':>12}")
print("-"*84)
for row in table:
    label,nick,o,q,gr,fe,nt = row
    if isinstance(nick,str) and ("ERR" in nick or "FAIL" in nick or "NO TOKEN" in nick):
        print(f"{label:<10} {nick}")
        continue
    print(f"{label:<10} {nick[:28]:<28} {o:>4} {q:>4} ${gr:>11,.2f} ${fe:>9,.2f} ${nt:>11,.2f}")
print("-"*84)
print(f"{'TOTAL':<10} {'':<28} {g_orders:>4} {g_qty:>4} ${g_gross:>11,.2f} ${g_fees:>9,.2f} ${g_net:>11,.2f}")
print(f"\nCanceladas hoy: {g_cancelled}")
print(f"\n=== TOP MODELOS HOY ===")
for t,e in sorted(top_models.items(),key=lambda x:-x[1]["r"])[:10]:
    print(f"  {e['u']:>3}u  ${e['r']:>10,.0f}  {t}")
