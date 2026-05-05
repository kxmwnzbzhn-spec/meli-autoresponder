"""
Probe eligibility ASVA en MLM-PORTABLE_SPEAKERS + lookup catalog product de referencia.

Inputs (env):
  MELI_APP_SECRET            (GH secret)
  MELI_REFRESH_TOKEN_ASVA    (GH secret)
  REF_CPID                   catalog product id de referencia (ej. MLMU3924356098)
  PROBE_DOMAIN               domain_id a probar (default MLM-PORTABLE_SPEAKERS)

Salidas: stdout estructurado + outputs/probe_asva_speakers_result.json
"""
import os, json, requests, sys, pathlib

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
REF_CPID = os.environ.get("REF_CPID", "MLMU3924356098").strip()
PROBE_DOMAIN = os.environ.get("PROBE_DOMAIN", "MLM-PORTABLE_SPEAKERS").strip()

result = {
    "ref_cpid": REF_CPID,
    "probe_domain": PROBE_DOMAIN,
}

def section(title):
    print(f"\n{'='*72}\n=== {title}\n{'='*72}")

# ---- 1) Token ----
section("1) OAuth token ASVA")
r = requests.post(
    "https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":APP_ID,
          "client_secret":APP_SECRET,"refresh_token":RT},
    timeout=15,
)
print(f"status={r.status_code}")
if r.status_code != 200:
    print(r.text); sys.exit(1)
AT = r.json()["access_token"]
H = {"Authorization": f"Bearer {AT}"}
HJ = {**H, "Content-Type": "application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
UID = me.get("id")
result["asva"] = {"uid": UID, "nickname": me.get("nickname")}
print(f"  asva uid={UID} nickname={me.get('nickname')}")

# ---- 2) Lookup del catalog product de referencia ----
section(f"2) GET /products/{REF_CPID}")
candidates = [REF_CPID]
# Try sin la U si tiene U embebida después de MLM
if REF_CPID.startswith("MLMU"):
    candidates.append("MLM" + REF_CPID[4:])
ref_data = None
for cpid in candidates:
    rr = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=15)
    print(f"  /products/{cpid} -> {rr.status_code}")
    if rr.status_code == 200:
        ref_data = rr.json()
        result["ref_cpid_resolved"] = cpid
        break
    else:
        print(f"    body: {rr.text[:300]}")

if ref_data:
    # Extraer lo crítico
    summary = {
        "id": ref_data.get("id"),
        "name": ref_data.get("name"),
        "domain_id": ref_data.get("domain_id"),
        "category_id": ref_data.get("category_id"),
        "status": ref_data.get("status"),
        "main_features": [mf.get("text","")[:120] for mf in (ref_data.get("main_features") or [])],
        "pictures_count": len(ref_data.get("pictures") or []),
        "pictures_first3": [p.get("url") for p in (ref_data.get("pictures") or [])[:3]],
        "n_attributes": len(ref_data.get("attributes") or []),
    }
    if ref_data.get("buy_box_winner"):
        summary["buy_box_price"] = ref_data["buy_box_winner"].get("price")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    # Imprimir todos los attributes
    print("\n  --- attributes completos ---")
    for a in (ref_data.get("attributes") or []):
        print(f"    {a.get('id'):30} = {a.get('value_name')}")
    result["ref_product"] = {
        **summary,
        "attributes": [{"id": a.get("id"), "name": a.get("name"), "value_name": a.get("value_name")} for a in (ref_data.get("attributes") or [])],
    }
else:
    result["ref_product"] = None

# ---- 3) Eligibility (quota) ASVA ----
section(f"3) GET /catalog_suggestions/users/{UID}")
rr = requests.get(f"https://api.mercadolibre.com/catalog_suggestions/users/{UID}", headers=H, timeout=10)
print(f"status={rr.status_code}")
print(f"body: {rr.text[:1500]}")
result["quota_endpoint"] = {"status": rr.status_code, "body": rr.text[:2000]}

# ---- 4) Domains disponibles ----
section("4) GET /catalog_suggestions/sites/MLM/domains")
rr = requests.get("https://api.mercadolibre.com/catalog_suggestions/sites/MLM/domains", headers=H, timeout=10)
print(f"status={rr.status_code}")
domains_text = rr.text[:2000]
print(f"body[:2000]: {domains_text}")
# Buscar referencias a speakers/audio
try:
    domains_json = rr.json()
    matched = []
    if isinstance(domains_json, list):
        for d in domains_json:
            did = (d.get("domain_id") or d.get("id") or "")
            name = d.get("name") or ""
            if "SPEAKER" in did.upper() or "AUDIO" in did.upper() or "speaker" in name.lower() or "audio" in name.lower() or "boci" in name.lower():
                matched.append({"domain_id": did, "name": name})
    print(f"\n  matched audio/speaker domains: {json.dumps(matched, indent=2, ensure_ascii=False)}")
    result["domains_matched_audio"] = matched
except Exception as e:
    print(f"  parse err: {e}")

# ---- 5) POST sondeo (mínimo) en PROBE_DOMAIN ----
section(f"5) POST /catalog_suggestions sondeo en {PROBE_DOMAIN}")
probe_body = {
    "site_id": "MLM",
    "domain_id": PROBE_DOMAIN,
    "attributes": [
        {"id": "BRAND", "value_name": "ProbeBrand"},
        {"id": "MODEL", "value_name": "ProbeModel"},
    ],
}
rr = requests.post("https://api.mercadolibre.com/catalog_suggestions",
                   headers=HJ, json=probe_body, timeout=15)
print(f"status={rr.status_code}")
try:
    body = rr.json()
    print(json.dumps(body, indent=2, ensure_ascii=False)[:2500])
    result["probe_post"] = {"status": rr.status_code, "body": body}
except Exception:
    print(rr.text[:1500])
    result["probe_post"] = {"status": rr.status_code, "text": rr.text[:2000]}

# ---- 6) Listar suggestions ya creadas por ASVA ----
section(f"6) GET /catalog_suggestions/search?seller_id={UID}")
rr = requests.get(f"https://api.mercadolibre.com/catalog_suggestions/search?seller_id={UID}", headers=H, timeout=10)
print(f"status={rr.status_code}")
print(rr.text[:1500])
result["search_endpoint"] = {"status": rr.status_code, "body": rr.text[:2500]}

# ---- 7) Technical specs del dominio (atributos requeridos) ----
section(f"7) GET /domains/{PROBE_DOMAIN}/technical_specs")
rr = requests.get(f"https://api.mercadolibre.com/domains/{PROBE_DOMAIN}/technical_specs?site_id=MLM", headers=H, timeout=10)
print(f"status={rr.status_code}")
try:
    j = rr.json()
    # Extraer required attributes
    req = []
    if isinstance(j, dict):
        for group in (j.get("input",{}) or {}).values() if isinstance(j.get("input"), dict) else []:
            pass
        # estructura típica
        for grp in j.get("groups") or []:
            for c in grp.get("components") or []:
                aid = c.get("id")
                tags = c.get("tags") or []
                if aid:
                    req.append({"id": aid, "required": "required" in tags or c.get("required", False), "tags": tags})
    print(json.dumps(req, indent=2, ensure_ascii=False)[:3000])
    result["tech_specs_summary"] = req
except Exception as e:
    print(f"  err parsing: {e}; raw: {rr.text[:1200]}")

# ---- DUMP ----
out_path = pathlib.Path("probe_asva_speakers_result.json")
out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"\n[OK] wrote {out_path} size={out_path.stat().st_size}")
