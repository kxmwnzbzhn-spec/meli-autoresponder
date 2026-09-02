"""One-off: cuenta Alejandra (ALE), todo status ready_to_ship."""
import os, sys, time, requests
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_run as d

TZ = d.TZ; TODAY = d.TODAY; DRIVE_FOLDER_ID = d.DRIVE_FOLDER_ID

RT = os.environ["MELI_REFRESH_TOKEN_ALE"]
def refresh(a, s):
    return requests.post("https://api.mercadolibre.com/oauth/token",
        data={"grant_type":"refresh_token","client_id":a,"client_secret":s,"refresh_token":RT},
        timeout=25).json()

# Probar new pair primero
j = refresh(os.environ.get("MELI_APP_ID_NEW",""), os.environ.get("MELI_APP_SECRET_NEW",""))
if not j.get("access_token"):
    j = refresh(os.environ["MELI_APP_ID"], os.environ["MELI_APP_SECRET"])
if not j.get("access_token"):
    print(f"❌ auth fail: {j}"); sys.exit(1)
AT = j["access_token"]; H = {"Authorization": f"Bearer {AT}"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
UID = me.get("id")
print(f"[auth] Alejandra: {me.get('nickname')} uid={UID}")

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
print(f"[scan] orders={len(orders)}")

obs = {}
for o in orders:
    sid = (o.get("shipping") or {}).get("id")
    if sid: obs.setdefault(sid,[]).append(o)

ships = []; substat = {}
for sid, orlist in obs.items():
    try:
        sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}", headers=H, timeout=10).json()
        st = sh.get("status"); sub = sh.get("substatus")
        substat[f"{st}/{sub}"] = substat.get(f"{st}/{sub}",0)+1
        if st != "ready_to_ship" or sub == "picked_up": continue
        comp=[]; used=False
        for ord_o in orlist:
            for it in ord_o.get("order_items", []):
                io_obj = it.get("item") or {}
                tcln,_ = d.clean_title(io_obj, H)
                qty = it.get("quantity",1)
                cond = d.get_condition(io_obj, H)
                if cond == "used":
                    used=True; comp.append(f"USADO {qty} {tcln}")
                else:
                    comp.append(f"{qty} {tcln}")
        if not comp: continue
        buyer = (orlist[0].get("buyer") or {}).get("nickname","?")
        ships.append({"sid":sid,"account":"Alejandra","buyer":buyer,
                      "comp_lines":comp,"has_used":used,"n_prods":len(comp),
                      "at":AT})
        time.sleep(0.04)
    except Exception as e:
        print(f"  err shipment {sid}: {str(e)[:80]}")
print(f"[filter] substatus breakdown: {substat}")
print(f"[filter] incluidas ready_to_ship: {len(ships)}")

if not ships:
    print("Sin ready_to_ship. No genero PDF."); sys.exit(0)

ships.sort(key=lambda s:(0 if s["has_used"] else 1,"/".join(s["comp_lines"]),s["sid"]))
out_local = f"ETIQUETAS_ALEJANDRA_{TODAY}.pdf"
pages, fails = d.build_pdf(ships, out_local)
print(f"[pdf] pages={pages} fallidas={len(fails)}")
if pages == 0: sys.exit(1)

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
print(f"   link: {link}")
print(f"   páginas: {pages}  ·  envíos: {len(ships)}  ·  fallidas: {len(fails)}")

try:
    d.tg_send(f"📦 <b>Etiquetas Alejandra · {TODAY}</b>\n✅ {pages} etiquetas\n📄 <a href=\"{link}\">Abrir PDF</a>")
except: pass
