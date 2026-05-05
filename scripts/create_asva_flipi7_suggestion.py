"""
Crea catalog_suggestion en MLM-SPEAKERS para ASVA - Asvaelectronics Flipi7 35W IP67 Negro.

Pipeline:
 1) OAuth ASVA
 2) Busca items activos de ASVA que matcheen el slug del URL original para sacar pictures (>=3)
 3) Genera EAN-13 interno (290 + 9 hash MD5 + check)
 4) Construye body con attributes completos
 5) POST /catalog_suggestions
 6) Si UNDER_REVIEW captura suggestion_id, opcionalmente POST /description
 7) Dump resultado + intenta GET /catalog_suggestions/{id}

Outputs:
  asva_flipi7_result.json
"""
import os, sys, json, hashlib, time, pathlib, requests

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]

BRAND = "Asvaelectronics"
MODEL = "Flipi7"
COLOR = "Negro"
POWER_W = "35 W"

result = {"brand": BRAND, "model": MODEL, "stage": "init"}

def section(t):
    print(f"\n{'='*72}\n=== {t}\n{'='*72}")

# 1) Token
section("1) OAuth")
r = requests.post(
    "https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
    timeout=15,
).json()
AT = r.get("access_token")
if not AT:
    print("OAUTH FAIL", r); sys.exit(1)
H = {"Authorization": f"Bearer {AT}"}
HJ = {**H, "Content-Type": "application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
UID = me["id"]
result["uid"] = UID
print(f"  asva uid={UID} nick={me.get('nickname')}")

# 2) Buscar items activos de ASVA con keywords del URL para sacar pictures
section("2) Buscar items ASVA con slug del URL para extraer pictures")
slug_terms = ["bocina bluetooth portatil impermeable ip67 bass 35w negro",
              "bluetooth portatil ip67 35w",
              "bocina ip67 35w",
              "bocina bluetooth 35w negro"]
found_items = []
for q in slug_terms:
    rr = requests.get(f"https://api.mercadolibre.com/users/{UID}/items/search",
                      params={"status":"active","q":q,"limit":20},
                      headers=H, timeout=15)
    if rr.status_code != 200:
        print(f"  q='{q}' status={rr.status_code} body={rr.text[:200]}")
        continue
    ids = rr.json().get("results") or []
    print(f"  q='{q}' -> {len(ids)} items")
    for iid in ids[:10]:
        if iid in [f["id"] for f in found_items]:
            continue
        item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
        title = item.get("title","")
        pics = [p.get("secure_url") or p.get("url") for p in (item.get("pictures") or [])]
        cat_listing = item.get("catalog_listing")
        cat_pid = item.get("catalog_product_id")
        # ranking simple por keywords presentes
        score = 0
        tlow = title.lower()
        for kw in ["35w","ip67","bluetooth","bocina","portatil","negro","bass"]:
            if kw in tlow: score += 1
        found_items.append({
            "id": iid,
            "title": title[:120],
            "pictures": pics,
            "catalog_listing": cat_listing,
            "catalog_product_id": cat_pid,
            "score": score,
        })
    if found_items: break

found_items.sort(key=lambda x: -x["score"])
result["candidate_items"] = found_items[:5]

if not found_items:
    print("  ⚠ No items match en ASVA. Voy a crear sugerencia SIN pictures (riesgo alto WAITING_FOR_FIX o REJECTED)")
    pictures = []
else:
    best = found_items[0]
    print(f"\n  best match: {best['id']} score={best['score']} title={best['title']}")
    pictures = best["pictures"][:6]
    print(f"  pictures: {len(pictures)}")
    for u in pictures:
        print(f"    - {u}")
result["pictures_used"] = pictures

# 3) EAN-13 interno: 290 + 9 hash + check
section("3) EAN-13 interno")
seed = f"{BRAND}::{MODEL}".lower()
h = hashlib.md5(seed.encode()).hexdigest()
nine = "".join(c for c in h if c.isdigit())[:9]
while len(nine) < 9:
    nine += "0"
body12 = "290" + nine
s = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(body12))
check = (10 - (s % 10)) % 10
EAN13 = body12 + str(check)
print(f"  seed='{seed}'  ean13={EAN13}")
result["gtin"] = EAN13

# 4) Construir body
section("4) Build body catalog_suggestion")
attrs = [
    {"id":"BRAND","value_name":BRAND},
    {"id":"MODEL","value_name":MODEL},
    {"id":"ALPHANUMERIC_MODEL","value_name":MODEL},
    {"id":"COLOR","value_name":COLOR},
    {"id":"POWER_OUTPUT_RMS","value_name":POWER_W},
    {"id":"WITH_BLUETOOTH","value_name":"Sí"},
    {"id":"IS_PORTABLE","value_name":"Sí"},
    {"id":"IS_WIRELESS","value_name":"Sí"},
    {"id":"IS_WATERPROOF","value_name":"Sí"},
    {"id":"GTIN","value_name":EAN13},
]
sugg_body = {
    "site_id": "MLM",
    "domain_id": "MLM-SPEAKERS",
    "attributes": attrs,
}
if pictures:
    sugg_body["pictures"] = [{"url": u} for u in pictures[:6]]

print(json.dumps(sugg_body, indent=2, ensure_ascii=False)[:1500])

# 5) POST
section("5) POST /catalog_suggestions")
rr = requests.post("https://api.mercadolibre.com/catalog_suggestions",
                   headers=HJ, json=sugg_body, timeout=20)
print(f"  status={rr.status_code}")
try:
    rb = rr.json()
    print(json.dumps(rb, indent=2, ensure_ascii=False)[:2500])
    result["post_status"] = rr.status_code
    result["post_body"] = rb
except Exception:
    result["post_status"] = rr.status_code
    result["post_text"] = rr.text[:1500]
    print(f"  raw: {rr.text[:600]}")

# 6) Si éxito, capturar suggestion_id y traer detalle
sid = None
if isinstance(result.get("post_body"), dict):
    sid = result["post_body"].get("id") or result["post_body"].get("suggestion_id")
if sid:
    section(f"6) GET /catalog_suggestions/{sid}")
    rr = requests.get(f"https://api.mercadolibre.com/catalog_suggestions/{sid}", headers=H, timeout=15)
    print(f"  status={rr.status_code}")
    try:
        rb = rr.json()
        print(json.dumps(rb, indent=2, ensure_ascii=False)[:2000])
        result["detail_after_post"] = rb
    except Exception:
        result["detail_after_post_text"] = rr.text[:1500]

    # 7) POST description
    desc = (
        f"Bocina Bluetooth portátil {BRAND} {MODEL} de 35W RMS con resistencia al agua IP67. "
        f"Ideal para fiestas, alberca, exteriores. Bluetooth 5.0 de largo alcance, batería de larga duración, "
        f"manos libres integrado. Color {COLOR}. Garantía y respaldo del vendedor."
    )
    rr = requests.post(f"https://api.mercadolibre.com/catalog_suggestions/{sid}/description",
                       headers=HJ, json={"plain_text": desc}, timeout=15)
    print(f"\n  POST /description status={rr.status_code} body[:300]={rr.text[:300]}")
    result["description_post_status"] = rr.status_code

result["stage"] = "done"
out = pathlib.Path("asva_flipi7_result.json")
out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"\n[OK] wrote {out}")
