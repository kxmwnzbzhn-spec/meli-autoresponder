import os, requests
from datetime import datetime, timezone, timedelta

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
ACCOUNTS=[
    ("Raymundo May Chi", "MELI_REFRESH_TOKEN_RAYMUNDO_MAY"),
    ("Ángel Damián",     "MELI_REFRESH_TOKEN_ANGEL_DAMIAN"),
    ("Asgari",           "MELI_REFRESH_TOKEN_ASGARI"),
]

for label, env in ACCOUNTS:
    RT=os.environ.get(env,"")
    if not RT: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=15).json()
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me["id"]; nick=me.get("nickname")
    
    # Pull last 10 orders ordered by date desc (any status)
    o=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&limit=10&sort=date_desc",headers=H,timeout=20).json()
    
    print(f"\n=== {label} ({nick} / UID {uid}) ===")
    
    # Last paid order
    last_paid=None; last_any=None
    for ord in o.get("results",[]):
        if not last_any:
            last_any=ord
        if ord.get("status") in ("paid","shipped","delivered"):
            last_paid=ord
            break
    
    # If last paid not in first 10, search more
    if not last_paid:
        offset=0
        while offset<5000 and not last_paid:
            r2=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=20).json()
            for ord in r2.get("results",[]):
                if ord.get("status") in ("paid","shipped","delivered"):
                    last_paid=ord; break
            if last_paid: break
            if not r2.get("results"): break
            offset+=50
    
    if last_paid:
        dt=last_paid.get("date_created","")
        title=""
        items=last_paid.get("order_items",[])
        if items:
            title=items[0].get("item",{}).get("title","")
        amt=last_paid.get("total_amount",0)
        # Compute days since
        try:
            ord_dt=datetime.fromisoformat(dt.replace("Z","+00:00"))
            now=datetime.now(timezone.utc)
            days=(now - ord_dt).days
            hours=int((now - ord_dt).total_seconds() // 3600)
        except:
            days=None
        print(f"  Última venta paid:")
        print(f"    Fecha: {dt}")
        print(f"    Hace: {days} días ({hours} horas)" if days is not None else "")
        print(f"    Producto: {title}")
        print(f"    Monto: ${amt:,.2f}")
    else:
        print(f"  Sin ventas paid encontradas")
    
    # También última orden de cualquier tipo (incluyendo cancelaciones)
    if last_any and last_any!=last_paid:
        dt=last_any.get("date_created","")
        st=last_any.get("status","")
        print(f"  Última orden (cualquier estado):")
        print(f"    Fecha: {dt}  Status: {st}")
