"""One-off: Jorge Luis + Asva, todas las accionables (ready_to_ship excepto picked_up)."""
import os, sys, time, requests
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_run as d

TZ = d.TZ; TODAY = d.TODAY; DRIVE_FOLDER_ID = d.DRIVE_FOLDER_ID
# Substatus accionables: incluir todas menos las ya recogidas
INCL = {"ready_to_print","printing_error","printed","invoice_pending"}

ACCS = [a for a in d.ACCOUNTS if a["name"] in ("Asva","JorgeLuis")]
print(f"[cfg] cuentas: {[a['name'] for a in ACCS]}  TODAY={TODAY}")

all_ships = []
per_account = {}
for a in ACCS:
    print(f"\n========== {a['name']} ==========")
    at, err = d.validate_account(a)
    if err:
        print(f"  ❌ {err}"); per_account[a['name']] = 0; continue
    # Override sub_filter temporalmente para Jorge Luis (aquí queremos todas, no solo ready_to_print)
    prev_sf = a.get("sub_filter")
    a["sub_filter"] = INCL
    try:
        ships = d.collect_shipments(at, a)
    finally:
        # Restaurar
        if prev_sf is None: a.pop("sub_filter", None)
        else: a["sub_filter"] = prev_sf
    per_account[a['name']] = len(ships)
    all_ships.extend(ships)
    print(f"  incluidos: {len(ships)}")

total = len(all_ships)
print(f"\n========== TOTAL: {total} envíos ({' + '.join(f'{k}:{v}' for k,v in per_account.items())}) ==========")

if total == 0:
    print("Sin envíos. No genero PDF."); sys.exit(0)

all_ships.sort(key=lambda s:(0 if s["has_used"] else 1, s["account"], "/".join(s["comp_lines"]), s["sid"]))
out_local = f"ETIQUETAS_JORGE_ASVA_{TODAY}.pdf"
pages, fails = d.build_pdf(all_ships, out_local)
print(f"[pdf] pages={pages} fallidas={len(fails)}")
if pages == 0: sys.exit(1)

import ssl as _ssl
def fresh_svc():
    for att in range(1,4):
        try: return d.drive_service()
        except Exception as e:
            print(f"[drive] rebuild {att}: {type(e).__name__}"); time.sleep(3*att)
    return d.drive_service()

svc = fresh_svc()
day_folder = None
for att in range(1,5):
    try:
        day_folder = d.drive_find_or_create_day_folder(svc, DRIVE_FOLDER_ID, TODAY); break
    except (_ssl.SSLEOFError, _ssl.SSLError, ConnectionError, OSError) as e:
        print(f"[drive] folder {att}: {type(e).__name__}"); time.sleep(2*att); svc = fresh_svc()
if not day_folder: sys.exit(1)

up = d.drive_upload_pdf(svc, out_local, out_local, day_folder)
link = up.get("webViewLink","")
print(f"\n✅ SUBIDO: {out_local}")
print(f"   file_id: {up.get('id')}")
print(f"   link: {link}")
print(f"   páginas: {pages}  ·  envíos: {total}  ·  fallidas: {len(fails)}")

try:
    msg = (f"📦 <b>Etiquetas Jorge + Asva · {TODAY}</b>\n"
           f"✅ {pages} págs · {total} envíos · {len(fails)} fallidas\n"
           + "\n".join(f"   • {k}: {v}" for k,v in per_account.items())
           + f"\n\n📄 <a href=\"{link}\">Abrir PDF</a>")
    d.tg_send(msg)
except Exception as e:
    print(f"[tg] err: {e}")
