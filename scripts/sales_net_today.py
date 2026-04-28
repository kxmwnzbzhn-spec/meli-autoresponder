#!/usr/bin/env python3
"""Resumen NET hoy: revenue - marketplace_fee - shipping_cost por cuenta."""
import os, requests, json
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
    ("BREN", "MELI_REFRESH_TOKEN_BREN"),
]

cdmx = datetime.now(timezone.utc) - timedelta(hours=6)
midnight_cdmx = cdmx.replace(hour=0, minute=0, second=0, microsecond=0)
midnight_utc = midnight_cdmx + timedelta(hours=6)
date_from = midnight_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
today = cdmx.strftime("%d/%m/%Y")
hours = cdmx.hour + cdmx.minute/60

print(f"📊 RESUMEN NET HOY — {today} ({cdmx.strftime('%H:%M')} CDMX)\n")

g_gross = g_fees = g_ship = g_qty = g_net = 0
g_orders = 0
account_sums = []

for label, env in ACCOUNTS:
    RT = os.environ.get(env,"")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
        USER_ID = me["id"]
    except Exception as e:
        print(f"[{label}] err: {e}"); continue
    
    a_gross = a_fees = a_ship = a_qty = 0
    a_orders = 0
    
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
            if st not in ("paid","shipped","delivered"): continue
            a_orders += 1
            amt = o.get("total_amount", 0) or 0
            a_gross += amt
            
            # Sum quantities
            for oi in o.get("order_items", []):
                a_qty += oi.get("quantity", 0)
            
            # Query order detail (search doesn't return fees)
            order_id = o.get("id")
            try:
                od = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=H, timeout=10).json()
                for pay in od.get("payments",[]):
                    if pay.get("status") in ("approved",):
                        fee = pay.get("marketplace_fee", 0) or 0
                        a_fees += fee
                # Shipping cost from shipment - usar list_cost que es lo que paga el seller en envío gratis
                sh_id = od.get("shipping",{}).get("id")
                if sh_id:
                    sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}", headers=H, timeout=10).json()
                    so = sd.get("shipping_option",{}) or {}
                    list_cost = so.get("list_cost", 0) or 0
                    cost_seller = so.get("cost", 0) or 0
                    # In MELI, list_cost is seller's price; cost is buyer's price
                    # If free_shipping, seller pays list_cost - cost
                    seller_pays = max(0, list_cost - cost_seller)
                    a_ship += seller_pays
            except Exception as e:
                pass
            
            # Sometimes shipping cost is in shipping not payments
            sh = o.get("shipping",{}) or {}
            # If empty payments shipping_cost, query shipment cost
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    a_net = a_gross - a_fees - a_ship
    g_gross += a_gross; g_fees += a_fees; g_ship += a_ship
    g_qty += a_qty; g_net += a_net; g_orders += a_orders
    
    if a_orders > 0:
        print(f"=== {label} ({me.get('nickname')}) ===")
        print(f"   Órdenes: {a_orders} | Unidades: {a_qty}")
        print(f"   Bruto: ${a_gross:,.2f}")
        print(f"   - Comisión MELI: ${a_fees:,.2f}")
        print(f"   - Envío seller: ${a_ship:,.2f}")
        print(f"   = NET: ${a_net:,.2f}\n")
        account_sums.append((label,a_orders,a_qty,a_gross,a_fees,a_ship,a_net))
    else:
        print(f"=== {label}: sin ventas ===\n")

# IVA (Mexico 16%): seller remite 16% del precio sin IVA
# bruto_con_iva / 1.16 = bruto_sin_iva → IVA = 16% × bruto_sin_iva
g_subtotal_sin_iva = g_gross / 1.16
g_iva_remite = g_gross - g_subtotal_sin_iva

print("="*70)
print(f"💰 TOTAL HOY ({today}):")
print(f"   Órdenes:  {g_orders}")
print(f"   Unidades: {g_qty}")
print(f"   Bruto:    ${g_gross:>10,.2f}")
print(f"   - Comisión MELI:  ${g_fees:>10,.2f}  ({g_fees/g_gross*100:.1f}% del bruto)" if g_gross > 0 else "")
print(f"   - Envío seller:   ${g_ship:>10,.2f}  ({g_ship/g_gross*100:.1f}% del bruto)" if g_gross > 0 else "")
print(f"   - IVA (16%):      ${g_iva_remite:>10,.2f}  ({g_iva_remite/g_gross*100:.1f}% del bruto)")
g_net_after_iva = g_net - g_iva_remite
print(f"   = NET:                ${g_net:>10,.2f}  ({g_net/g_gross*100:.1f}%)")
print(f"   = NET DESPUÉS IVA:    ${g_net_after_iva:>10,.2f}  ({g_net_after_iva/g_gross*100:.1f}%)")
print("="*70)

if hours > 0 and g_net > 0:
    rate_h = g_net / hours
    proj = rate_h * 24
    print(f"\n📈 Proyección 24h NET: ${proj:,.0f}  (tasa ${rate_h:,.0f}/h)")

print(f"\n📊 NET por cuenta:")
for label,o,q,gr,f,sh,n in sorted(account_sums, key=lambda x: -x[6]):
    margin_pct = (n/gr*100) if gr else 0
    print(f"  {label:<10} ${n:>9,.0f} NET  ({margin_pct:.0f}% margen)  | bruto ${gr:>9,.0f}")
print()
print("⚠️ NOTA: Este NET descuenta solo comisión MELI + envío seller.")
print("   NO incluye COGS (costo del producto) ni gastos operativos.")
