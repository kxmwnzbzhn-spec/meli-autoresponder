"""
Crear catalog_suggestion ASVA: Bocina Bluetooth Portátil Flipi7 35W IP67 Roja (MLM-SPEAKERS).
Reusa las fotos de un listing activo de ASVA (sus picture ids).
Formato atributos: {"id":ATTR,"values":[{"name":"Valor"}]} (recipe).
"""
import os, json, hashlib, requests, meli_token

API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json(); UID=me["id"]
print("ASVA uid:",UID,me.get("nickname"))

# 1) Buscar item activo de la bocina roja
queries=["bocina bluetooth portatil impermeable ip67 bass 35w rojo",
         "bocina bluetooth ip67 35w rojo","flipi7 35w rojo","bocina 35w ip67 roja"]
pics=[]; chosen=None
for q in queries:
    r=requests.get(f"{API}/users/{UID}/items/search",params={"status":"active","q":q,"limit":20},headers=H,timeout=15)
    ids=r.json().get("results") or []
    print(f"q='{q}' -> {len(ids)} items")
    for iid in ids:
        it=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        tl=(it.get("title") or "").lower()
        if "35w" in tl and ("roj" in tl) and ("ip67" in tl or "impermeable" in tl):
            chosen=it
            pics=[{"id":p["id"]} for p in (it.get("pictures") or []) if p.get("id")][:8]
            print(f"  MATCH {iid} | {it.get('title')[:80]} | {len(pics)} fotos")
            break
    if chosen: break

if not pics:
    print("⚠ No encontré item rojo con fotos. Abortando para no crear sin fotos.")
    raise SystemExit(1)

# 2) EAN-13 interno
seed="asvaelectronics::flipi7::rojo"
h=hashlib.md5(seed.encode()).hexdigest(); nine="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
b="290"+nine; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b)); EAN=b+str((10-(s%10))%10)
print("EAN13:",EAN)

TITLE="Bocina Bluetooth Portátil Asvaelectronics Flipi7 35W IP67 Resistente al Agua Bajos Potentes Inalámbrica Roja"
ATTRS=[
 {"id":"BRAND","values":[{"name":"Asvaelectronics"}]},
 {"id":"MODEL","values":[{"name":"Flipi7"}]},
 {"id":"ALPHANUMERIC_MODEL","values":[{"name":"Flipi7"}]},
 {"id":"COLOR","values":[{"name":"Rojo"}]},
 {"id":"POWER_OUTPUT_RMS","values":[{"name":"35 W"}]},
 {"id":"WITH_BLUETOOTH","values":[{"name":"Sí"}]},
 {"id":"IS_PORTABLE","values":[{"name":"Sí"}]},
 {"id":"IS_WIRELESS","values":[{"name":"Sí"}]},
 {"id":"IS_WATERPROOF","values":[{"name":"Sí"}]},
 {"id":"IP_RATING","values":[{"name":"IP67"}]},
 {"id":"GTIN","values":[{"name":EAN}]},
]
body={"site_id":"MLM","domain_id":"MLM-SPEAKERS","type":"EDIT","title":TITLE,"attributes":ATTRS,"pictures":pics}
print("\n=== BODY ==="); print(json.dumps(body,ensure_ascii=False,indent=2)[:1500])

r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
print("\nhttp",r.status_code)
try:
    rb=r.json(); print(json.dumps(rb,ensure_ascii=False,indent=2)[:2500])
    sid=rb.get("id") or rb.get("suggestion_id")
    if sid: print(f"\n>>> SUGGESTION_ID = {sid}")
except Exception:
    print("raw:",r.text[:1000])
