import os,requests,json
from datetime import datetime,timezone,timedelta
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me.get("id")
print(f"Cuenta: {me.get('nickname')} id={uid}")

now=datetime.now(timezone.utc)

# Traer todas las ordenes paid (hasta 1000)
orders=[]
offset=0
while offset<1000:
    r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=paid&limit=50&offset={offset}&sort=date_desc",headers=H,timeout=20).json()
    res=r.get("results",[])
    if not res: break
    orders+=res
    total_paging=r.get("paging",{}).get("total",0)
    offset+=50
    if offset>=total_paging: break

print(f"\nOrdenes paid totales: {len(orders)}\n")

# Clasificar por status de shipping
buckets={
    "delivered": {"count":0,"bruto":0,"fees":0,"neto":0},
    "shipped": {"count":0,"bruto":0,"fees":0,"neto":0},
    "handling": {"count":0,"bruto":0,"fees":0,"neto":0},
    "ready_to_ship": {"count":0,"bruto":0,"fees":0,"neto":0},
    "pending": {"count":0,"bruto":0,"fees":0,"neto":0},
    "other": {"count":0,"bruto":0,"fees":0,"neto":0},
}

# Obtener status envío de cada orden
last_30d = now - timedelta(days=30)
for o in orders:
    # Obtener total y fee
    total_paid = 0
    total_fee = 0
    for p in o.get("payments",[]):
        if p.get("status")=="approved":
            total_paid += p.get("transaction_amount",0) or 0
            # fee_details suma todos los fees (comision meli, envio si aplica)
            for fd in p.get("fee_details",[]) or []:
                total_fee += fd.get("amount",0) or 0
    if total_paid==0: continue
    neto = total_paid - total_fee
    
    # Shipping status
    shp = o.get("shipping") or {}
    shp_status = shp.get("status","unknown")
    
    # Si no tiene shipping info, traer detalle
    if shp_status=="unknown" and shp.get("id"):
        sr=requests.get(f"https://api.mercadolibre.com/shipments/{shp['id']}",headers=H,timeout=15).json()
        shp_status=sr.get("status","unknown")
    
    bkey = {
        "delivered":"delivered",
        "shipped":"shipped",
        "ready_to_ship":"ready_to_ship",
        "handling":"handling",
        "pending":"pending",
    }.get(shp_status,"other")
    buckets[bkey]["count"] += 1
    buckets[bkey]["bruto"] += total_paid
    buckets[bkey]["fees"] += total_fee
    buckets[bkey]["neto"] += neto

print(f"{'Estado':<18} {'#':>4} {'Bruto':>12} {'Fees MELI':>12} {'Neto $':>12}")
print("-"*66)
total_b=total_f=total_n=total_c=0
for k in ["delivered","shipped","ready_to_ship","handling","pending","other"]:
    b=buckets[k]
    if b["count"]==0: continue
    print(f"{k:<18} {b['count']:>4} ${b['bruto']:>10,.2f} ${b['fees']:>10,.2f} ${b['neto']:>10,.2f}")
    total_b+=b["bruto"]; total_f+=b["fees"]; total_n+=b["neto"]; total_c+=b["count"]
print("-"*66)
print(f"{'TOTAL':<18} {total_c:>4} ${total_b:>10,.2f} ${total_f:>10,.2f} ${total_n:>10,.2f}")

# Estimación: dinero que llega a MP
disponible = buckets["delivered"]["neto"]  # ya entregado (money released)
en_transito = buckets["shipped"]["neto"] + buckets["handling"]["neto"] + buckets["ready_to_ship"]["neto"]  # en camino (retenido)
pending_cat = buckets["pending"]["neto"]  # sin despachar aun

print(f"\n===== ESTIMACION MERCADO PAGO =====")
print(f"Dinero YA disponible (entregadas):         ${disponible:,.2f}")
print(f"Dinero RETENIDO (en camino):                ${en_transito:,.2f}")
print(f"Dinero PENDIENTE (por despachar):           ${pending_cat:,.2f}")
print(f"TOTAL NETO (disp + retenido + pendiente):   ${disponible+en_transito+pending_cat:,.2f}")
print(f"\nNota: MELI libera el dinero ~14 dias despues de confirmar entrega.")
