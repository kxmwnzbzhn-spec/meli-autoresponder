#!/usr/bin/env python3
"""ETIQUETAS LUNES: filtra shipments cuyo handling_limit (deadline MELI para
despachar) cae en lunes 4 mayo 2026 o antes (overdue). Genera CSV + manifest
y opcionalmente regenera el PDF unificado solo con esos.

Lógica:
- Recorre todas las cuentas
- Lista órdenes paid recientes (7 dias)
- Para cada shipment: GET shipment detail
- Toma estimated_handling_limit.date (CDMX)
- Filtra <= LIMIT_DAY (lunes 4 mayo)
"""
import os, requests, time, json
from datetime import datetime, timedelta, timezone
from collections import defaultdict

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID = os.environ.get("TELEGRAM_CHAT_ID","")

ACCS = {
    "Juan":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "Claribel": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "Asva":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "Raymundo": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "Dilcie":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "Mildred":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "Bren":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
}

# Día límite: lunes 4 mayo 2026 (incluye overdue)
TZ_CDMX = timezone(timedelta(hours=-6))
LIMIT_DAY_STR = os.environ.get("LIMIT_DAY", "2026-05-04")
LIMIT_DAY = datetime.fromisoformat(LIMIT_DAY_STR).date()
print(f"Límite handling: {LIMIT_DAY} (incluye overdue anteriores)")

def tok(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")


WINDOW_DAYS = 7
NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=WINDOW_DAYS)

results = defaultdict(list)
errors = []

for acc, rt in ACCS.items():
    if not rt:
        print(f"\n{acc}: sin token, skip")
        continue
    print(f"\n=== {acc} ===")
    at = tok(rt)
    if not at:
        print(f"  {acc}: token refresh fallo")
        continue
    H = {"Authorization": f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    uid = me.get("id")
    if not uid: continue

    # Listar orders paid de ultima semana
    orders = []
    offset = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search",
            headers=H, timeout=20,
            params={"seller":uid,
                    "order.status":"paid",
                    "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit":50,"offset":offset}).json()
        res = r.get("results",[])
        if not res: break
        orders.extend(res)
        offset += len(res)
        if offset >= r.get("paging",{}).get("total",0): break

    # Extraer shipment ids
    ship_ids = set()
    order_by_ship = {}
    for o in orders:
        sh = (o.get("shipping") or {}).get("id")
        if sh:
            ship_ids.add(sh)
            order_by_ship[sh] = o

    print(f"  orders paid 7d: {len(orders)} | shipments: {len(ship_ids)}")

    # Para cada shipment ver handling_limit y status
    matches = 0
    for sid in ship_ids:
        try:
            sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}",
                              headers=H, timeout=10).json()
            status = sh.get("status")
            substatus = sh.get("substatus")
            # ignorar shipments ya enviados
            if status in ("delivered","shipped","not_delivered","cancelled"):
                continue
            # ignorar handling_unit ya cerrado
            if substatus in ("delivered","shipped"):
                continue

            # estimated_handling_limit
            ehl = (sh.get("lead_time") or {}).get("estimated_handling_limit") or {}
            limit_date_str = ehl.get("date") or sh.get("estimated_handling_limit") or ""
            if not limit_date_str:
                # intentar otro path
                limit_date_str = (sh.get("shipping_option") or {}).get("estimated_handling_limit",{}).get("date","")
            limit_date = None
            if limit_date_str:
                try:
                    # ISO format with TZ
                    dt = datetime.fromisoformat(limit_date_str.replace("Z","+00:00"))
                    limit_date = dt.astimezone(TZ_CDMX).date()
                except Exception:
                    pass

            if limit_date and limit_date <= LIMIT_DAY:
                # Match
                ord_o = order_by_ship.get(sid, {})
                items = ord_o.get("order_items",[])
                comp = "+".join(f"{(it.get('item') or {}).get('title','')[:30]} x{it.get('quantity',1)}" for it in items)
                buyer = (ord_o.get("buyer") or {}).get("nickname","?")
                results[acc].append({
                    "shipment_id": sid,
                    "order_id": ord_o.get("id"),
                    "buyer": buyer,
                    "composition": comp,
                    "handling_limit": str(limit_date),
                    "status": status,
                    "substatus": substatus,
                })
                matches += 1
            time.sleep(0.05)
        except Exception as e:
            errors.append({"acc":acc,"sid":sid,"err":str(e)[:80]})

    print(f"  ✅ {acc}: {matches} shipments con limit <= {LIMIT_DAY}")

# Reporte
print(f"\n{'='*60}\n=== TOTAL ===")
total = sum(len(v) for v in results.values())
print(f"Total shipments para despachar lunes (limit <= {LIMIT_DAY}): {total}")
for acc, lst in results.items():
    print(f"  {acc}: {len(lst)}")

# Guardar CSV
import csv
out = "lunes_shipments.csv"
with open(out,"w",newline="",encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["account","shipment_id","order_id","buyer","composition","handling_limit","status","substatus"])
    for acc, lst in results.items():
        for s in lst:
            w.writerow([acc, s["shipment_id"], s["order_id"], s["buyer"],
                        s["composition"], s["handling_limit"], s["status"], s["substatus"]])
print(f"\nCSV: {out}")

# Telegram
if TG and TGCID:
    msg = f"📅 *Despacho lunes {LIMIT_DAY_STR}*\n\n"
    msg += f"Total shipments con handling_limit ≤ {LIMIT_DAY_STR}: *{total}*\n\n"
    for acc, lst in sorted(results.items(), key=lambda x: -len(x[1])):
        if lst: msg += f"• {acc}: *{len(lst)}*\n"
    # Group by handling_limit date
    by_date = defaultdict(int)
    for lst in results.values():
        for s in lst:
            by_date[s["handling_limit"]] += 1
    msg += f"\n*Por fecha límite:*\n"
    for d in sorted(by_date.keys()):
        marker = "⚠️ OVERDUE" if d < LIMIT_DAY_STR else "📅"
        msg += f"  {marker} {d}: {by_date[d]}\n"
    if errors: msg += f"\n❌ Errores: {len(errors)}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
