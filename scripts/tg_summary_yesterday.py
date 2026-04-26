#!/usr/bin/env python3
"""Resumen de AYER a Telegram con bruto, neto, devoluciones, top productos por cuenta."""
import os, requests, json, sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]; TG_CHAT = os.environ["TELEGRAM_CHAT_ID"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
]

# Yesterday CDMX
date_str = os.environ.get("ACCOUNTING_DATE","")
if date_str:
    target = datetime.strptime(date_str,"%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=-6)))
else:
    target = (datetime.now(timezone.utc) - timedelta(hours=6)) - timedelta(days=1)

day_start_cdmx = target.replace(hour=0,minute=0,second=0,microsecond=0)
day_end_cdmx = day_start_cdmx + timedelta(days=1)
date_from = day_start_cdmx.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
date_to = day_end_cdmx.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
date_label = day_start_cdmx.strftime("%d/%m/%Y")

print(f"Resumen {date_label} CDMX")

per_acc = {}
all_returns_count = 0
all_returns_amt = 0
top_products = defaultdict(lambda: {"qty":0,"revenue":0})

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var,"")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
        USER_ID = me["id"]
    except Exception as e: continue
    
    a_orders = a_qty = 0; a_bruto = a_fees = a_ship = 0; a_ret_cnt = a_ret_amt = 0
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&order.date_created.to={date_to}&limit=50&offset={offset}",headers=H,timeout=20).json()
        results = rr.get("results",[])
        if not results: break
        for o in results:
            st = o.get("status","")
            had_paid = False; refund = 0
            for pay in o.get("payments",[]):
                if pay.get("status")=="approved": had_paid=True
                if pay.get("status") in ("refunded","charged_back"):
                    refund += pay.get("transaction_amount",0) or 0
            if st=="cancelled" and not had_paid: continue
            if refund > 0:
                a_ret_cnt += 1; a_ret_amt += refund
            if st not in ("paid","shipped","delivered"): continue
            amt = o.get("total_amount",0) or 0
            a_orders += 1; a_bruto += amt
            try:
                od = requests.get(f"https://api.mercadolibre.com/orders/{o.get('id')}",headers=H,timeout=10).json()
                for pay in od.get("payments",[]):
                    if pay.get("status")=="approved":
                        a_fees += pay.get("marketplace_fee",0) or 0
                sh_id = od.get("shipping",{}).get("id")
                if sh_id:
                    sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}",headers=H,timeout=10).json()
                    so = sd.get("shipping_option",{}) or {}
                    a_ship += max(0,(so.get("list_cost",0) or 0)-(so.get("cost",0) or 0))
            except: pass
            for oi in o.get("order_items",[]):
                qty = oi.get("quantity",0)
                a_qty += qty
                title = oi.get("item",{}).get("title","")[:50] or "?"
                top_products[title]["qty"] += qty
                top_products[title]["revenue"] += qty * (oi.get("unit_price",0) or 0)
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    iva = a_bruto - (a_bruto/1.16) if a_bruto > 0 else 0
    net = a_bruto - a_fees - a_ship
    net_after_iva = net - iva
    per_acc[label] = {
        "nick": me.get("nickname",""),
        "orders":a_orders,"qty":a_qty,"bruto":a_bruto,
        "fees":a_fees,"ship":a_ship,"iva":iva,
        "net":net,"net_iva":net_after_iva,
        "ret_cnt":a_ret_cnt,"ret_amt":a_ret_amt
    }
    all_returns_count += a_ret_cnt; all_returns_amt += a_ret_amt

t_o = sum(d["orders"] for d in per_acc.values())
t_q = sum(d["qty"] for d in per_acc.values())
t_b = sum(d["bruto"] for d in per_acc.values())
t_f = sum(d["fees"] for d in per_acc.values())
t_s = sum(d["ship"] for d in per_acc.values())
t_iva = sum(d["iva"] for d in per_acc.values())
t_net = t_b - t_f - t_s
t_net_iva = t_net - t_iva

# Build Telegram message
lines = [f"📊 *Resumen {date_label}*\n"]
lines.append(f"💰 *Bruto:* ${t_b:,.0f}")
lines.append(f"📦 Órdenes: {t_o} | Unidades: {t_q}\n")
lines.append(f"  − Comisión MELI: ${t_f:,.0f} ({t_f/t_b*100:.0f}%)" if t_b else "")
lines.append(f"  − Envío seller: ${t_s:,.0f} ({t_s/t_b*100:.0f}%)" if t_b else "")
lines.append(f"  − IVA (16%): ${t_iva:,.0f}\n")
lines.append(f"✅ *NET (sin IVA):* ${t_net:,.0f} ({t_net/t_b*100:.0f}%)" if t_b else "")
lines.append(f"🏦 *NET (post IVA):* ${t_net_iva:,.0f} ({t_net_iva/t_b*100:.0f}%)\n" if t_b else "")
lines.append(f"↩️ Devoluciones reales: *{all_returns_count}* / ${all_returns_amt:,.0f}\n")

# Por cuenta
lines.append("*━━━ Por cuenta ━━━*")
for label, d in sorted(per_acc.items(), key=lambda x: -x[1]["bruto"]):
    if d["orders"] == 0: continue
    lines.append(f"`{label:<10}` ${d['bruto']:>7,.0f} | {d['orders']} ord | NET ${d['net_iva']:,.0f}")

# Top 5 productos
lines.append(f"\n*🔥 Top 5 productos:*")
top_sorted = sorted(top_products.items(), key=lambda x: -x[1]["revenue"])[:5]
for title, info in top_sorted:
    lines.append(f"• {title[:40]} — {info['qty']}u/${info['revenue']:,.0f}")

msg = "\n".join(l for l in lines if l)
print(msg)

# Send
r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":msg[:4000],"parse_mode":"Markdown"})
print(f"\nTelegram: {r.status_code}")
