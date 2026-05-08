"""Cierra TODAS las publicaciones que tengan 'Mandarin Sky' en el título, en cada cuenta."""
import os, requests, time

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

ACCS = {
    "JUAN":         os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL":     os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASGARI":       os.environ.get("MELI_REFRESH_TOKEN_ASGARI"),
    "MILDRED":      os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "WILBERT":      os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "RAYMUNDO":     os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "ANGEL_DAMIAN": os.environ.get("MELI_REFRESH_TOKEN_ANGEL_DAMIAN"),
    "RAYMUNDO_MAY": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO_MAY"),
    "DILCIE":       os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
}

closed_total = 0
errors = []
report_lines = []

for acc, rt in ACCS.items():
    if not rt:
        continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,
            "client_secret":APP_SECRET,"refresh_token":rt}, timeout=15).json()
        at = r.get("access_token")
        if not at:
            print(f"{acc}: AUTH FAIL")
            continue
        H = {"Authorization": f"Bearer {at}", "Content-Type":"application/json"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
        uid = me.get("id")
        if not uid: continue

        iids = []
        for st in ["active","paused","under_review"]:
            offset = 0
            while True:
                rr = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=50&offset={offset}", headers=H, timeout=20).json()
                b = rr.get("results",[])
                if not b: break
                iids.extend(b)
                offset += len(b)
                if offset >= rr.get("paging",{}).get("total",0): break

        # Filtrar Mandarin
        mandarin_items = []
        for i in range(0, len(iids), 20):
            chunk = iids[i:i+20]
            rr = requests.get("https://api.mercadolibre.com/items", headers=H,
                params={"ids":",".join(chunk),"attributes":"id,title,status"}, timeout=20).json()
            for resp in rr:
                if resp.get("code") != 200: continue
                it = resp["body"]
                if "mandarin" in (it.get("title","") or "").lower():
                    if it.get("status") != "closed":
                        mandarin_items.append(it)
            time.sleep(0.2)

        if not mandarin_items:
            continue

        print(f"\n=== {acc} — {len(mandarin_items)} mandarin a cerrar ===")
        for it in mandarin_items:
            iid = it["id"]
            title = it["title"][:60]
            # PUT status=closed
            r2 = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                              headers=H, json={"status":"closed"}, timeout=20)
            if r2.status_code == 200:
                print(f"  ✓ closed {iid}  {title}")
                closed_total += 1
                report_lines.append(f"✓ {acc} {iid} {title}")
            else:
                err = r2.text[:200]
                print(f"  ✗ FAIL {iid}: HTTP {r2.status_code} {err}")
                errors.append(f"{acc}/{iid}: {err}")
                report_lines.append(f"✗ {acc} {iid} {err[:80]}")
            time.sleep(0.5)
    except Exception as e:
        print(f"{acc}: ERR {e}")
        errors.append(f"{acc}: {e}")

print(f"\n=== TOTAL: {closed_total} publicaciones Mandarin Sky CERRADAS ===")
if errors:
    print(f"Errores: {len(errors)}")
    for e in errors[:10]:
        print(f"  {e}")

if TG and TGCID:
    msg = f"🚫 *Mandarin Sky — TODAS cerradas*\n\nCerradas: *{closed_total}* publicaciones\n"
    if errors:
        msg += f"Errores: {len(errors)}\n"
    msg += "\n_Stock master ya estaba en 0._"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=15)
