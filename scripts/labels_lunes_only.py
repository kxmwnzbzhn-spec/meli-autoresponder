#!/usr/bin/env python3
"""ETIQUETAS LUNES — filtra shipments que MELI requiere despachar HOY/LUNES.

Lógica:
1. Lista órdenes paid (últimos 7 días)
2. Para cada shipment status=ready_to_ship (etiqueta lista pero no entregada al carrier):
   - Calcula handover_deadline = date_handling + handling_hours_default (48h)
   - O usa /shipments/{id}/sla → expected_date como deadline
3. Filtra los que tengan deadline <= LIMIT_DAY (lunes 4 mayo)
   = OVERDUE (ya pasó deadline) + due-on-Monday
4. Genera CSV agrupado por cuenta con shipment_id, comp, deadline, urgency
"""
import os, requests, time, csv, json
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

TZ_CDMX = timezone(timedelta(hours=-6))
LIMIT_DAY_STR = os.environ.get("LIMIT_DAY", "2026-05-04")
LIMIT_DAY = datetime.fromisoformat(LIMIT_DAY_STR).replace(hour=23, minute=59, tzinfo=TZ_CDMX)
print(f"Límite handover: {LIMIT_DAY.isoformat()}")

def tok(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

WINDOW_DAYS = 10
NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=WINDOW_DAYS)

results = defaultdict(list)
errors = []

for acc, rt in ACCS.items():
    if not rt:
        print(f"\n{acc}: skip"); continue
    print(f"\n=== {acc} ===")
    at = tok(rt)
    if not at: continue
    H = {"Authorization": f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    uid = me.get("id")
    if not uid: continue

    # Listar orders paid
    orders = []
    offset = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search",
            headers=H, timeout=20,
            params={"seller":uid, "order.status":"paid",
                    "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit":50,"offset":offset}).json()
        res = r.get("results",[])
        if not res: break
        orders.extend(res)
        offset += len(res)
        if offset >= r.get("paging",{}).get("total",0): break

    ship_ids = set()
    order_by_ship = {}
    for o in orders:
        sid = (o.get("shipping") or {}).get("id")
        if sid:
            ship_ids.add(sid)
            order_by_ship[sid] = o

    print(f"  orders paid: {len(orders)} | shipments: {len(ship_ids)}")

    matches = 0
    for sid in ship_ids:
        try:
            sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}",
                              headers=H, timeout=10).json()
            status = sh.get("status")
            substatus = sh.get("substatus")
            # Solo los que aun no se han despachado
            if status not in ("ready_to_ship", "handling"):
                continue
            # Si ya esta shipped substatus, skip
            if substatus in ("shipped","ready_to_pickup"):
                continue

            # Deadline: usar SLA endpoint (expected_date)
            deadline = None
            try:
                sla = requests.get(f"https://api.mercadolibre.com/shipments/{sid}/sla",
                                   headers=H, timeout=8).json()
                ed = sla.get("expected_date")
                if ed:
                    deadline = datetime.fromisoformat(ed.replace("Z","+00:00")).astimezone(TZ_CDMX)
            except Exception:
                pass

            # Fallback: date_handling + 48h
            if not deadline:
                hist = sh.get("status_history") or {}
                dh = hist.get("date_handling")
                if dh:
                    dh_dt = datetime.fromisoformat(dh.replace("Z","+00:00"))
                    deadline = (dh_dt + timedelta(hours=48)).astimezone(TZ_CDMX)

            if not deadline:
                continue

            if deadline <= LIMIT_DAY:
                ord_o = order_by_ship.get(sid, {})
                items = ord_o.get("order_items",[])
                comp = " + ".join(f"{(it.get('item') or {}).get('title','')[:40]} x{it.get('quantity',1)}"
                                  for it in items)
                buyer = (ord_o.get("buyer") or {}).get("nickname","?")
                # urgency
                today = datetime.now(TZ_CDMX)
                if deadline.date() < today.date():
                    urgency = "OVERDUE"
                elif deadline.date() == today.date():
                    urgency = "HOY"
                else:
                    urgency = "LUNES"

                results[acc].append({
                    "shipment_id": sid,
                    "order_id": ord_o.get("id"),
                    "buyer": buyer,
                    "composition": comp,
                    "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
                    "deadline_date": deadline.date().isoformat(),
                    "urgency": urgency,
                    "status": status,
                    "substatus": substatus,
                    "tracking": sh.get("tracking_number",""),
                    "logistic": sh.get("logistic_type",""),
                })
                matches += 1
            time.sleep(0.05)
        except Exception as e:
            errors.append({"acc":acc,"sid":sid,"err":str(e)[:80]})

    print(f"  ✅ {acc}: {matches} match")

# Reporte
total = sum(len(v) for v in results.values())
overdue = sum(1 for lst in results.values() for s in lst if s["urgency"]=="OVERDUE")
hoy = sum(1 for lst in results.values() for s in lst if s["urgency"]=="HOY")
lunes = sum(1 for lst in results.values() for s in lst if s["urgency"]=="LUNES")
print(f"\n{'='*60}\n=== TOTAL: {total} ===")
print(f"  OVERDUE (ya vencidos): {overdue}")
print(f"  HOY (deadline hoy): {hoy}")
print(f"  LUNES (deadline lunes): {lunes}")
for acc, lst in sorted(results.items(), key=lambda x: -len(x[1])):
    if lst: print(f"  {acc}: {len(lst)}")

# CSV
with open("lunes_shipments.csv","w",newline="",encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["urgency","account","shipment_id","order_id","buyer","composition",
                "deadline","status","substatus","tracking","logistic"])
    rows = []
    for acc, lst in results.items():
        for s in lst:
            rows.append([s["urgency"], acc, s["shipment_id"], s["order_id"], s["buyer"],
                         s["composition"], s["deadline"], s["status"], s["substatus"],
                         s["tracking"], s["logistic"]])
    # Sort: OVERDUE first, then HOY, then LUNES
    rank = {"OVERDUE":0,"HOY":1,"LUNES":2}
    rows.sort(key=lambda r: (rank.get(r[0],9), r[6]))
    for r in rows: w.writerow(r)
print(f"\nCSV: lunes_shipments.csv")

# Telegram
if TG and TGCID:
    msg = f"📅 *Despacho hasta {LIMIT_DAY_STR}*\n\n"
    msg += f"*Total: {total}*\n"
    msg += f"⚠️ OVERDUE: *{overdue}*\n"
    msg += f"⏰ HOY: *{hoy}*\n"
    msg += f"📦 LUNES: *{lunes}*\n\n*Por cuenta:*\n"
    for acc, lst in sorted(results.items(), key=lambda x: -len(x[1])):
        if lst: msg += f"• {acc}: *{len(lst)}*\n"
    if errors: msg += f"\n❌ Errores: {len(errors)}"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=20)
