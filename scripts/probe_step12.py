"""
Step 1 + Step 2 del protocolo: quota + technical_specs del endpoint catalog_suggestions.
NO HACE POST. Solo trae schema real.
"""
import os, json, requests, pathlib

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]

def section(t): print(f"\n{'='*72}\n=== {t}\n{'='*72}")

# OAuth
r = requests.post("https://api.mercadolibre.com/oauth/token",
                  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
                  timeout=15).json()
AT = r["access_token"]
H = {"Authorization": f"Bearer {AT}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
UID = me["id"]
print(f"asva uid={UID}")

result = {"uid": UID}

# STEP 1 — quota
section(f"STEP 1 — GET /catalog_suggestions/users/{UID}")
rr = requests.get(f"https://api.mercadolibre.com/catalog_suggestions/users/{UID}", headers=H, timeout=15)
print(f"  status={rr.status_code}")
ct = rr.headers.get("content-type","")
if rr.status_code == 200:
    try:
        body = rr.json()
        print(json.dumps(body, indent=2, ensure_ascii=False)[:2500])
        result["quota"] = body
    except Exception:
        print(f"  raw: {rr.text[:1000]}")
        result["quota_raw"] = rr.text[:1500]
else:
    print(f"  content-type={ct}")
    print(f"  body[:600]: {rr.text[:600]}")
    result["quota_status"] = rr.status_code
    result["quota_raw"] = rr.text[:800]

# STEP 2.1 — listar domains catalog_suggestions
section("STEP 2.1 — GET /catalog_suggestions/sites/MLM/domains")
rr = requests.get("https://api.mercadolibre.com/catalog_suggestions/sites/MLM/domains", headers=H, timeout=15)
print(f"  status={rr.status_code}")
ct = rr.headers.get("content-type","")
print(f"  content-type={ct}")
if rr.status_code == 200:
    try:
        domains = rr.json()
        # match audio/speakers
        speakers = []
        if isinstance(domains, list):
            print(f"  total domains: {len(domains)}")
            for d in domains:
                did = d.get("domain_id") or d.get("id") or ""
                name = d.get("domain_name") or d.get("name") or ""
                if "SPEAKER" in did.upper() or "AUDIO" in did.upper() or "speaker" in name.lower() or "boci" in name.lower() or "audio" in name.lower():
                    speakers.append({"domain_id": did, "name": name})
                    print(f"    audio match: id={did}  name={name}")
        result["domains_audio"] = speakers
    except Exception as e:
        print(f"  parse err: {e}; raw[:800]: {rr.text[:800]}")
        result["domains_raw"] = rr.text[:1500]
else:
    print(f"  body[:600]: {rr.text[:600]}")
    result["domains_status"] = rr.status_code
    result["domains_raw"] = rr.text[:800]

# STEP 2.2 — technical_specs en endpoint catalog_suggestions (DOS variantes)
for dom in ["MLM-PORTABLE_SPEAKERS", "MLM-SPEAKERS"]:
    section(f"STEP 2.2 — GET /catalog_suggestions/sites/MLM/domains/{dom}/technical_specs")
    rr = requests.get(f"https://api.mercadolibre.com/catalog_suggestions/sites/MLM/domains/{dom}/technical_specs",
                      headers=H, timeout=15)
    print(f"  status={rr.status_code}")
    print(f"  content-type={rr.headers.get('content-type','')}")
    if rr.status_code == 200:
        try:
            spec = rr.json()
            # Imprimir resumen estructurado
            print(f"\n  spec.keys: {list(spec.keys()) if isinstance(spec, dict) else 'list len='+str(len(spec))}")
            attrs = []
            if isinstance(spec, dict):
                # Posibles ubicaciones
                if "attributes" in spec:
                    attrs = spec["attributes"]
                elif "groups" in spec:
                    for g in spec["groups"]:
                        for c in g.get("components", []):
                            attrs.append(c)
                elif "input" in spec and isinstance(spec["input"], dict):
                    for k, v in spec["input"].items():
                        if isinstance(v, list): attrs.extend(v)
            print(f"  total attributes: {len(attrs)}")
            print(f"\n  --- REQUIRED attributes ---")
            for a in attrs:
                aid = a.get("id")
                tags = a.get("tags") or {}
                req = (isinstance(tags, dict) and tags.get("required")) or (isinstance(tags, list) and "required" in tags) or a.get("required")
                if not req: continue
                vt = a.get("value_type")
                vals = a.get("values") or a.get("allowed_values") or []
                print(f"\n    id={aid}")
                print(f"      value_type={vt}")
                print(f"      tags={tags}")
                if vt in ("list","boolean"):
                    print(f"      values_count={len(vals)}")
                    for v in (vals[:8] if isinstance(vals, list) else []):
                        print(f"        value_id={v.get('id')}  name={v.get('name')}")
                if vt == "number_unit":
                    units = a.get("allowed_units") or a.get("units") or []
                    print(f"      units={units}")
            print(f"\n  --- ALL attribute IDs ---")
            print("  " + ", ".join((a.get("id") or "") for a in attrs))
            result[f"techspecs_{dom}"] = {
                "attribute_ids": [a.get("id") for a in attrs],
                "required_attrs": [a for a in attrs if (isinstance(a.get("tags"), dict) and a.get("tags",{}).get("required")) or (isinstance(a.get("tags"), list) and "required" in a.get("tags",[])) or a.get("required")],
                "raw_first_5": attrs[:5],
            }
        except Exception as e:
            print(f"  parse err: {e}; raw[:1000]: {rr.text[:1000]}")
            result[f"techspecs_{dom}_raw"] = rr.text[:2000]
    else:
        print(f"  body[:500]: {rr.text[:500]}")
        result[f"techspecs_{dom}_status"] = rr.status_code

pathlib.Path("step12_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"\n[OK] wrote step12_result.json")
