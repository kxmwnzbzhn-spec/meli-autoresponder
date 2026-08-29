"""One-off: cuenta Jorge Luis, solo shipments substatus=ready_to_print
(estas son las "Etiquetas por imprimir" en la UI de MELI)."""
import os, sys, time, json, requests
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_run as d

TZ = d.TZ
TODAY = d.TODAY
DRIVE_FOLDER_ID = d.DRIVE_FOLDER_ID

RT = os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"]
APP_ID = os.environ.get("MELI_APP_ID_NEW") or os.environ["MELI_APP_ID"]
APP_SECRET = os.environ.get("MELI_APP_SECRET_NEW") or os.environ["MELI_APP_SECRET"]

# Refresh token → access token (probando app NEW primero, fallback OLD)
def refresh(app_id, app_sec):
    return requests.post("https://api.mercadolibre.com/oauth/token",
        data={"grant_type":"refresh_token","client_id":app_id,
              "client_secret":app_sec,"refresh_token":RT},timeout=25).json()

j = refresh(APP_ID, APP_SECRET)
if not j.get("access_token"):
    print(f"[NEW app fail] {j.get('error')}: {j.get('message')}. Trying OLD.")
    j = refresh(os.environ["MELI_APP_ID"], os.environ["MELI_APP_SECRET"])
if not j.get("access_token"):
    print(f"❌ auth fail: {j}"); sys.exit(1)
AT = j["access_token"]
H = {"Authorization": f"Bearer {AT}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
UID = me.get("id"); NICK = me.get("nickname")
print(f"[auth] Jorge Luis: {NICK} uid={UID}")

# Traer orders paid últimos 90 días
NOW = datetime.now(timezone.utc); START = NOW - timedelta(days=90)
orders=[]; off=0
while True:
    r = requests.get("https://api.mercadolibre.com/orders/search", headers=H, timeout=20,
        params={"seller":UID,"order.status":"paid",
                "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "order.date_created.to":NOW.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "limit":50,"offset":off}).json()
    res = r.get("results",[])
    if not res: break
    orders.extend(res); off += len(res)
    if off >= r.get("paging",{}).get("total",0): break
print(f"[scan] paid orders últimos 90d: {len(orders)}")

# Agrupar por shipping_id
obs = {}
for o in orders:
    sid = (o.get("shipping") or {}).get("id")
    if sid: obs.setdefault(sid, []).append(o)
print(f"[scan] shipping_ids únicos: {len(obs)}")

# Filtrar: ready_to_ship + ready_to_print
ships=[]; skipped_status=0; substat_counter={}
for sid, ord_list in obs.items():
    try:
        sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}", headers=H, timeout=10).json()
        st = sh.get("status"); sub = sh.get("substatus")
        substat_counter[f"{st}/{sub}"] = substat_counter.get(f"{st}/{sub}",0)+1
        if st != "ready_to_ship" or sub != "ready_to_print":
            skipped_status += 1; continue
        comp=[]; used=False
        for ord_o in ord_list:
            for it in ord_o.get("order_items", []):
                io_obj = it.get("item") or {}
                tcln, model = d.clean_title(io_obj, H)
                qty = it.get("quantity", 1)
                cond = d.get_condition(io_obj, H)
                if cond == "used":
                    used=True; comp.append(f"USADO {qty} {tcln}")
                else:
                    comp.append(f"{qty} {tcln}")
        if not comp: continue
        buyer = (ord_list[0].get("buyer") or {}).get("nickname","?")
        ships.append({"sid":sid,"account":"JorgeLuis","buyer":buyer,
                      "comp_lines":comp,"has_used":used,"n_prods":len(comp),
                      "at":AT})
        time.sleep(0.04)
    except Exception as e:
        print(f"  err shipment {sid}: {str(e)[:80]}")
print(f"[filter] substatus breakdown: {substat_counter}")
print(f"[filter] ready_to_print incluidas: {len(ships)}")

if not ships:
    print("Sin shipments en 'Etiquetas por imprimir'. No genero PDF.")
    sys.exit(0)

ships.sort(key=lambda s:(0 if s["has_used"] else 1,"/".join(s["comp_lines"]),s["sid"]))
out_local = f"ETIQUETAS_JORGELUIS_{TODAY}.pdf"
pages, fails = d.build_pdf(ships, out_local)
print(f"[pdf] pages={pages} fallidas={len(fails)}")
if pages == 0: sys.exit(1)

# Drive: rebuild + retry SSL
import ssl as _ssl
def fresh_svc():
    for a in range(1,4):
        try: return d.drive_service()
        except Exception as e:
            print(f"[drive] rebuild {a}: {type(e).__name__}"); time.sleep(3*a)
    return d.drive_service()

svc = fresh_svc()
day_folder = None
for a in range(1,5):
    try:
        day_folder = d.drive_find_or_create_day_folder(svc, DRIVE_FOLDER_ID, TODAY); break
    except (_ssl.SSLEOFError, _ssl.SSLError, ConnectionError, OSError) as e:
        print(f"[drive] folder {a}: {type(e).__name__}"); time.sleep(2*a); svc = fresh_svc()
if not day_folder: sys.exit(1)

up = d.drive_upload_pdf(svc, out_local, out_local, day_folder)
link = up.get("webViewLink","")
print(f"\n✅ SUBIDO: {out_local}")
print(f"   file_id: {up.get('id')}")
print(f"   link: {link}")
print(f"   páginas: {pages}  ·  envíos: {len(ships)}  ·  fallidas: {len(fails)}")

try:
    d.tg_send(f"📦 <b>Etiquetas Jorge Luis · {TODAY}</b>\n✅ {pages} etiquetas por imprimir\n📄 <a href=\"{link}\">Abrir PDF</a>")
except Exception as e:
    print(f"[tg] err: {e}")
