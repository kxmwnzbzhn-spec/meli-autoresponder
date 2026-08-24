"""One-off: solo Edilberto + LuisEd, solo shipments ready_to_ship con
date_handling.estimated_handling_limit.date == HOY CDMX. Sin dedupe global.
Sube consolidado a la subcarpeta del día en Drive."""
import os, sys, io, time, json, re, requests
from datetime import datetime, timedelta, timezone

# Import de daily_run
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_run as d

TZ = d.TZ
TODAY = d.TODAY  # YYYY-MM-DD CDMX
DRIVE_FOLDER_ID = d.DRIVE_FOLDER_ID

ONLY = {"Edilberto", "LuisEd"}
accounts = [a for a in d.ACCOUNTS if a["name"] in ONLY]

print(f"[hoy] TODAY (CDMX)={TODAY}")
print(f"[hoy] cuentas: {[a['name'] for a in accounts]}")

def is_today_limit(sh):
    """True si el shipment tiene estimated_handling_limit.date == HOY CDMX."""
    dh = sh.get("date_handling") or {}
    ehl = dh.get("estimated_handling_limit") or {}
    dstr = ehl.get("date") or ""
    # dstr formato ISO con offset (ej 2026-08-24T22:59:59.000-06:00). Convertir a CDMX date.
    if not dstr: return False
    try:
        # Parse
        # strip fractional seconds
        s = re.sub(r"\.\d+", "", dstr)
        # dateutil not installed by default; usar fromisoformat con soporte offset
        dt = datetime.fromisoformat(s)
        local = dt.astimezone(TZ)
        return local.strftime("%Y-%m-%d") == TODAY
    except Exception as e:
        return False

def collect_only_today(at, account):
    """Copia de collect_shipments pero con filtro estricto por fecha límite = HOY."""
    H = {"Authorization": f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    uid = me["id"]
    NOW = datetime.now(timezone.utc); START = NOW - timedelta(days=90)
    orders = []; off = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search", headers=H, timeout=20,
            params={"seller": uid, "order.status": "paid",
                    "order.date_created.from": START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "order.date_created.to": NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit": 50, "offset": off}).json()
        res = r.get("results", [])
        if not res: break
        orders.extend(res); off += len(res)
        if off >= r.get("paging", {}).get("total", 0): break
    obs = {}
    for o in orders:
        sid = (o.get("shipping") or {}).get("id")
        if sid: obs.setdefault(sid, []).append(o)
    ships = []; skipped_notoday = 0; skipped_status = 0
    excl_models = account["exclude_models"]; excl_titles = account["exclude_titles"]
    for sid, ord_list in obs.items():
        try:
            sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}", headers=H, timeout=10).json()
            st = sh.get("status"); sub = sh.get("substatus")
            if st != "ready_to_ship" or sub in d.EXCLUDED_SUBS:
                skipped_status += 1; continue
            if not is_today_limit(sh):
                skipped_notoday += 1; continue
            comp = []; used = False; skip = False
            for ord_o in ord_list:
                for it in ord_o.get("order_items", []):
                    io_obj = it.get("item") or {}
                    tcln, model = d.clean_title(io_obj, H)
                    if model in excl_models: skip = True
                    rt_ = (io_obj.get("title") or "").lower(); rcln = tcln.lower()
                    if any(kw in rt_ or kw in rcln for kw in excl_titles): skip = True
                    qty = it.get("quantity", 1)
                    cond = d.get_condition(io_obj, H)
                    if cond == "used":
                        used = True; comp.append(f"USADO {qty} {tcln}")
                    else:
                        comp.append(f"{qty} {tcln}")
            if skip: continue
            if not comp: continue
            buyer = (ord_list[0].get("buyer") or {}).get("nickname", "?")
            ships.append({"sid": sid, "account": account["name"], "buyer": buyer,
                          "comp_lines": comp, "has_used": used, "n_prods": len(comp),
                          "at": at})
            time.sleep(0.04)
        except Exception as e:
            print(f"  err shipment {sid}: {str(e)[:80]}")
    print(f"  [{account['name']}] scaneados={len(obs)} status_off={skipped_status} no_hoy={skipped_notoday} incluidos={len(ships)}")
    ships.sort(key=lambda s: (0 if s["has_used"] else 1, "/".join(s["comp_lines"]), s["sid"]))
    return ships

all_ships = []
per_account = {}
for a in accounts:
    print(f"\n========== {a['name']} ==========")
    at, err = d.validate_account(a)
    if err:
        print(f"  ❌ {err}"); per_account[a['name']] = 0; continue
    ships = collect_only_today(at, a)
    per_account[a['name']] = len(ships)
    all_ships.extend(ships)

total = len(all_ships)
print(f"\n========== TOTAL con fecha límite HOY ({TODAY}): {total} envíos ({' + '.join(f'{k}:{v}' for k,v in per_account.items())}) ==========")

if total == 0:
    print("Sin envíos con fecha límite HOY. No genero PDF.")
    sys.exit(0)

out_local = f"ETIQUETAS_HOY_EDIL_LUIS_{TODAY}.pdf"
pages, fails = d.build_pdf(all_ships, out_local)
print(f"[pdf] pages={pages} fallidas={len(fails)} ids_fail={fails[:20]}")

if pages == 0:
    print("❌ PDF vacío"); sys.exit(1)

# Drive upload — rebuild svc + retry SSL
def fresh_svc():
    for att in range(1, 4):
        try: return d.drive_service()
        except Exception as e:
            print(f"[drive] rebuild {att} fail: {type(e).__name__}: {str(e)[:120]}")
            time.sleep(3*att)
    return d.drive_service()

import ssl as _ssl
svc = fresh_svc()
day_folder_id = None
for att in range(1, 5):
    try:
        day_folder_id = d.drive_find_or_create_day_folder(svc, DRIVE_FOLDER_ID, TODAY); break
    except (_ssl.SSLEOFError, _ssl.SSLError, ConnectionError, OSError) as e:
        print(f"[drive] day_folder att {att} err: {type(e).__name__}: {str(e)[:120]}")
        time.sleep(2*att); svc = fresh_svc()
if not day_folder_id:
    print("❌ no pude crear/obtener subcarpeta"); sys.exit(1)

up = d.drive_upload_pdf(svc, out_local, out_local, day_folder_id)
link = up.get("webViewLink", "")
print(f"\n✅ SUBIDO: {out_local}")
print(f"   file_id: {up.get('id')}")
print(f"   link: {link}")
print(f"   páginas: {pages}  ·  envíos: {total}  ·  fallidas: {len(fails)}")
if fails:
    print(f"   ids fallidos: {list(fails)}")

# Telegram
try:
    tg_msg = (f"📦 <b>Etiquetas HOY (fecha límite {TODAY})</b>\n"
              f"Cuentas: Edilberto + LuisEd\n"
              f"✅ {pages} págs · {total} envíos · {len(fails)} fallidas\n"
              + "\n".join(f"   • {k}: {v}" for k,v in per_account.items())
              + f"\n\n📄 <a href=\"{link}\">Abrir PDF</a>")
    d.tg_send(tg_msg)
except Exception as e:
    print(f"[tg] err: {e}")
