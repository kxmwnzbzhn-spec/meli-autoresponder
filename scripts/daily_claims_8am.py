#!/usr/bin/env python3
"""
Reporte diario de reclamos abiertos en las 6 cuentas.
Corre 8:00 AM CDMX = 14:00 UTC.
Telegram con detalle completo: claim_id, cuenta, producto, orden, comprador, motivo, monto, días abierto.
"""
import os, requests, json, time
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
]

REASON_LABELS = {
    "PDD9943": "no es original",
    "PDD9944": "producto defectuoso/dañado",
    "PNR9501": "no llegó el producto",
    "PDD8975": "producto incompleto",
    "PDD9945": "producto distinto al publicado",
    "PDD8974": "diferente al pedido",
    "PDD8973": "no le gustó",
    "PDR9526": "no recibió el producto",
    "PDD9939": "diferente al publicado",
}

def days_since(iso_date):
    if not iso_date: return "?"
    try:
        d = datetime.fromisoformat(iso_date.replace("Z","+00:00"))
        return (datetime.now(timezone.utc) - d).days
    except: return "?"

all_claims = []  # [(account, claim_dict, order_dict)]

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var, "")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
    except Exception as e:
        print(f"[{label}] auth err: {e}"); continue

    rc = requests.get(
        "https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&limit=20",
        headers=H, timeout=15
    ).json()
    claims = rc.get("data") or []
    print(f"{label}: {len(claims)} reclamos abiertos")
    
    for c in claims:
        order_id = c.get("resource_id")
        order_data = {}
        try:
            order_data = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=H, timeout=10).json()
        except: pass
        all_claims.append((label, me.get("nickname"), c, order_data))

# Build Telegram message
today = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime("%d/%m/%Y")
if not all_claims:
    msg = f"☀️ *Reporte reclamos {today}*\n\n✅ *0 reclamos abiertos* en las 6 cuentas\n\nQue tengas un buen día 🙌"
else:
    lines = [f"☀️ *Reporte reclamos {today}* — {len(all_claims)} abiertos\n"]
    
    # Group by account
    by_account = {}
    for label, nick, c, ord_data in all_claims:
        by_account.setdefault(label, []).append((nick, c, ord_data))
    
    for label, items in by_account.items():
        nick = items[0][0]
        lines.append(f"\n*━━━ {label}* ({nick}) ━━━ *{len(items)}*")
        for _, c, ord_data in items:
            cid = c.get("id")
            stage = c.get("stage","?")
            ctype = c.get("type","?")
            reason_id = c.get("reason_id","")
            reason = REASON_LABELS.get(reason_id, reason_id)
            opened = c.get("date_created","")
            days_open = days_since(opened)
            
            order_id = c.get("resource_id")
            buyer = ord_data.get("buyer",{}).get("nickname","?")
            amount = ord_data.get("total_amount","?")
            items_o = ord_data.get("order_items",[])
            product = items_o[0].get("item",{}).get("title","?")[:50] if items_o else "?"
            
            lines.append(f"\n🚨 Claim `{cid}` — *{days_open}d abierto*")
            lines.append(f"  📦 {product}")
            lines.append(f"  🛒 Orden `{order_id}` | 💰 ${amount}")
            lines.append(f"  👤 Comprador: `{buyer}`")
            lines.append(f"  ⚠️  Motivo: *{reason}* ({reason_id})")
            lines.append(f"  🏷️  {ctype} — {stage}")
    
    lines.append(f"\n_Próximo reporte: mañana 8:00 AM_")
    msg = "\n".join(lines)

# Send Telegram (split if too long)
if TG_TOKEN and TG_CHAT:
    # Telegram max 4096 chars
    if len(msg) <= 4000:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                          json={"chat_id":TG_CHAT,"text":msg,"parse_mode":"Markdown"})
        print(f"telegram: {r.status_code}")
    else:
        # Send in chunks
        chunks = [msg[i:i+3800] for i in range(0, len(msg), 3800)]
        for i, ch in enumerate(chunks):
            r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                              json={"chat_id":TG_CHAT,"text":ch,"parse_mode":"Markdown"})
            print(f"telegram chunk {i+1}/{len(chunks)}: {r.status_code}")
            time.sleep(1)

print(f"\nTotal claims: {len(all_claims)}")
