#!/usr/bin/env python3
"""Resumen de ventas hoy en las 6 cuentas (desde 00:00 CDMX)."""
import os, requests, json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
]

now_utc = datetime.now(timezone.utc)
cdmx = now_utc - timedelta(hours=6)
midnight_cdmx = cdmx.replace(hour=0, minute=0, second=0, microsecond=0)
midnight_utc = midnight_cdmx + timedelta(hours=6)
date_from = midnight_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
today_label = cdmx.strftime("%d/%m/%Y")
hours_so_far = cdmx.hour + cdmx.minute/60

print(f"📊 RESUMEN DE VENTAS — {today_label} CDMX")
print(f"   Hora CDMX actual: {cdmx.strftime('%H:%M')} ({hours_so_far:.1f}h transcurridas)")
print(f"   Buscando desde: {date_from} UTC\n")

grand_total_qty = 0
grand_total_revenue = 0
grand_total_orders = 0
account_summaries = []

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var, "")
    if not RT:
        print(f"[{label}] sin token, skip"); continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
        USER_ID = me.get("id")
    except Exception as e:
        print(f"[{label}] auth err: {e}"); continue
    
    total_qty = 0
    total_revenue = 0
    n_orders = 0
    products_count = defaultdict(int)
    products_revenue = defaultdict(float)
    statuses = defaultdict(int)
    
    offset = 0
    while True:
        rr = requests.get(
            f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&limit=50&offset={offset}",
            headers=H, timeout=20
        ).json()
        results = rr.get("results", [])
        if not results: break
        for o in results:
            st = o.get("status","")
            statuses[st] += 1
            if st in ("paid","shipped","delivered"):
                amt = o.get("total_amount", 0) or 0
                total_revenue += amt
                n_orders += 1
                for oi in o.get("order_items",[]):
                    qty = oi.get("quantity",0)
                    total_qty += qty
                    title = (oi.get("item",{}).get("title","")[:50]) or "?"
                    products_count[title] += qty
                    unit_price = oi.get("unit_price",0) or 0
                    products_revenue[title] += qty * unit_price
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    grand_total_qty += total_qty
    grand_total_revenue += total_revenue
    grand_total_orders += n_orders
    
    nick = me.get("nickname","?")
    print(f"=== {label} ({nick}) ===")
    print(f"   Órdenes pagadas/enviadas: {n_orders}")
    print(f"   Unidades vendidas: {total_qty}")
    print(f"   Revenue: ${total_revenue:,.2f}")
    if statuses:
        st_str = " | ".join(f"{k}:{v}" for k,v in statuses.items())
        print(f"   Status breakdown: {st_str}")
    if products_count:
        # Top 5 products
        sorted_p = sorted(products_count.items(), key=lambda x: -x[1])[:5]
        print(f"   Top productos:")
        for title, qty in sorted_p:
            rev = products_revenue.get(title,0)
            print(f"     • {title[:48]:<48} | {qty}u | ${rev:,.0f}")
    print()
    account_summaries.append({"label":label, "orders":n_orders, "qty":total_qty, "revenue":total_revenue})

# Grand total
print("="*70)
print(f"💰 GRAND TOTAL HOY ({today_label}):")
print(f"   Órdenes: {grand_total_orders}")
print(f"   Unidades: {grand_total_qty}")
print(f"   Revenue: ${grand_total_revenue:,.2f}")
if hours_so_far > 0:
    rate_hour = grand_total_revenue / hours_so_far
    proj_24h = rate_hour * 24
    print(f"   Tasa actual: ${rate_hour:,.0f}/hora")
    print(f"   Proyección 24h: ${proj_24h:,.0f}")
print("="*70)
print("\n📊 Top cuentas hoy (por revenue):")
for a in sorted(account_summaries, key=lambda x: -x["revenue"]):
    if a["revenue"] > 0:
        print(f"   {a['label']:<10} ${a['revenue']:>10,.0f}  ({a['orders']} órdenes / {a['qty']} unidades)")
