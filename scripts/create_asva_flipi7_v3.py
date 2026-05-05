"""
v3: probe attributes con value_ids correctos + fallbacks progresivos.
"""
import os, sys, json, hashlib, requests, pathlib

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]

BRAND = "Asvaelectronics"
MODEL = "Flipi7"
COLOR = "Negro"

def section(t):
    print(f"\n{'='*72}\n=== {t}\n{'='*72}")

# OAuth
r = requests.post("https://api.mercadolibre.com/oauth/token",
                  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
                  timeout=15).json()
AT = r["access_token"]
H = {"Authorization": f"Bearer {AT}"}
HJ = {**H, "Content-Type": "application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
UID = me["id"]
print(f"asva uid={UID}")

# Pictures de item ASVA matchee
section("Pictures from ASVA item")
items_resp = requests.get(f"https://api.mercadolibre.com/users/{UID}/items/search",
    params={"status":"active","q":"bocina bluetooth portatil impermeable ip67 bass 35w negro","limit":3},
    headers=H, timeout=15).json()
PICS = []
ITEM_REF = None
for iid in (items_resp.get("results") or [])[:1]:
    it = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
    PICS = [p.get("secure_url") or p.get("url") for p in (it.get("pictures") or [])][:6]
    ITEM_REF = it
    print(f"  item={iid} title='{it.get('title')[:80]}' pics={len(PICS)}")
    print(f"  category_id={it.get('category_id')}")
    # extraer attributes con value_id
    print("  attrs (con value_id):")
    item_attrs_map = {}
    for a in (it.get("attributes") or []):
        item_attrs_map[a.get("id")] = a
        if a.get("value_id"):
            print(f"    {a.get('id'):28} value_id={a.get('value_id'):12} value_name={a.get('value_name')}")

# 1) Traer attributes de la category del item para conseguir allowed values con value_id
section("Categoría attributes (allowed values)")
CAT = ITEM_REF.get("category_id") if ITEM_REF else None
print(f"  category={CAT}")
allowed = {}
if CAT:
    rr = requests.get(f"https://api.mercadolibre.com/categories/{CAT}/attributes", headers=H, timeout=15)
    if rr.status_code == 200:
        for a in rr.json():
            aid = a.get("id")
            vt = a.get("value_type")
            vals = a.get("values") or []
            tags = a.get("tags") or {}
            allowed[aid] = {"value_type": vt, "tags": tags, "values_count": len(vals), "values_sample": vals[:8]}
        # imprimir solo los que nos interesan
        for k in ["BRAND","MODEL","ALPHANUMERIC_MODEL","COLOR","POWER_OUTPUT_RMS",
                  "WITH_BLUETOOTH","IS_PORTABLE","IS_WIRELESS","IS_WATERPROOF","GTIN",
                  "MAX_BATTERY_AUTONOMY","SPEAKERS_NUMBER"]:
            a = allowed.get(k)
            if not a: continue
            print(f"\n    {k}: type={a['value_type']} tags={a['tags']}")
            for v in a["values_sample"][:4]:
                print(f"      val: id={v.get('id')} name={v.get('name')}")

# Helper
def value_id_for(attr_id, name):
    a = allowed.get(attr_id)
    if not a: return None
    for v in a.get("values_sample") or []:
        if (v.get("name") or "").strip().lower() == name.strip().lower():
            return v.get("id")
    return None

# EAN
seed = f"{BRAND}::{MODEL}".lower()
nine = "".join(c for c in hashlib.md5(seed.encode()).hexdigest() if c.isdigit())[:9].ljust(9,"0")
body12 = "290" + nine
EAN = body12 + str((10 - sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(body12))%10)%10)
print(f"\n  ean13={EAN}")

# 2) Build body MÍNIMO ABSOLUTO (sin booleanos)
section("ATTEMPT A: body mínimo (solo BRAND+MODEL+COLOR+GTIN)")
attrs_min = [
    {"id":"BRAND","value_name":BRAND},
    {"id":"MODEL","value_name":MODEL},
    {"id":"COLOR","value_name":COLOR},
    {"id":"GTIN","value_name":EAN},
]
body_min = {"site_id":"MLM","domain_id":"MLM-SPEAKERS","attributes":attrs_min}
if PICS: body_min["pictures"] = [{"url":u} for u in PICS[:5]]

rr = requests.post("https://api.mercadolibre.com/catalog_suggestions", headers=HJ, json=body_min, timeout=20)
print(f"  status={rr.status_code}")
print(json.dumps(rr.json() if rr.status_code in (200,201,400) else {"raw": rr.text[:500]}, indent=2, ensure_ascii=False)[:2000])
attempt_a = {"status":rr.status_code,"body":rr.json() if rr.headers.get("content-type","").startswith("application/json") else rr.text[:500]}

# 3) Build body CON value_ids
section("ATTEMPT B: body con value_ids correctos para booleanos")
attrs_full = [
    {"id":"BRAND","value_name":BRAND},
    {"id":"MODEL","value_name":MODEL},
    {"id":"ALPHANUMERIC_MODEL","value_name":MODEL},
    {"id":"COLOR","value_name":COLOR},
    {"id":"POWER_OUTPUT_RMS","value_name":"35 W"},
    {"id":"GTIN","value_name":EAN},
]
# Agregar booleanos con value_id
for bool_aid, want in [("WITH_BLUETOOTH","Sí"),("IS_PORTABLE","Sí"),("IS_WIRELESS","Sí"),("IS_WATERPROOF","Sí")]:
    vid = value_id_for(bool_aid, want)
    if vid:
        attrs_full.append({"id":bool_aid, "value_id":vid, "value_name":want})
        print(f"  {bool_aid}: value_id={vid} value_name={want}")
    else:
        # Fallback: usar value_id estándar 242085 que MELI usa para "Sí" en booleanos
        attrs_full.append({"id":bool_aid, "value_id":"242085", "value_name":"Sí"})
        print(f"  {bool_aid}: NO allowed, fallback value_id=242085")

body_full = {"site_id":"MLM","domain_id":"MLM-SPEAKERS","attributes":attrs_full}
if PICS: body_full["pictures"] = [{"url":u} for u in PICS[:5]]

rr = requests.post("https://api.mercadolibre.com/catalog_suggestions", headers=HJ, json=body_full, timeout=20)
print(f"\n  status={rr.status_code}")
try:
    rb = rr.json()
    print(json.dumps(rb, indent=2, ensure_ascii=False)[:2500])
except Exception:
    print(f"  raw: {rr.text[:600]}")
    rb = rr.text[:600]
attempt_b = {"status":rr.status_code, "body":rb if isinstance(rb,(dict,list)) else str(rb)}

# Si A o B funcionó, GET detail
sid = None
for at in (attempt_a, attempt_b):
    b = at.get("body")
    if isinstance(b, dict) and (b.get("id") or b.get("suggestion_id")):
        sid = b.get("id") or b.get("suggestion_id")
        break

result = {
    "uid": UID,
    "category_used_for_lookup": CAT,
    "ean13": EAN,
    "pictures_count": len(PICS),
    "attempt_a_min": attempt_a,
    "attempt_b_full": attempt_b,
    "suggestion_id": sid,
}

if sid:
    section(f"GET /catalog_suggestions/{sid}")
    rr = requests.get(f"https://api.mercadolibre.com/catalog_suggestions/{sid}", headers=H, timeout=15)
    print(f"  status={rr.status_code} body[:1000]={rr.text[:1000]}")
    try:
        result["detail"] = rr.json()
    except Exception:
        result["detail_raw"] = rr.text[:1000]

pathlib.Path("asva_flipi7_v3_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"\n[OK] wrote asva_flipi7_v3_result.json")
