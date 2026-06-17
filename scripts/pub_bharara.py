import os, requests, json, re
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CAT="MLM194118"; IID="MLM3025719815"
ats=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=15).json()
attr_map={a["id"]:a for a in ats}

def vid(aid, name):
  for v in (attr_map.get(aid,{}).get("values") or []):
    if (v.get("name") or "").lower()==name.lower():
      return v.get("id")
  return None

# Big curated fill
desired={
  "AGE_GROUP":               ("Adultos", vid("AGE_GROUP","Adultos")),
  "PACKAGE_HEIGHT":          ("4 cm", None),
  "PACKAGE_WIDTH":           ("12 cm", None),
  "PACKAGE_LENGTH":          ("16 cm", None),
  "PACKAGE_WEIGHT":          ("120 g", None),
  "TOE_TYPE":                ("Reforzada", None),
  "WITH_RECYCLED_MATERIALS": ("No", vid("WITH_RECYCLED_MATERIALS","No")),
  "PAIRS_NUMBER":            ("3", None),
  "SOCKS_SIZE":              ("7-12 MX", None),
  "RELEASE_YEAR":            ("2025", None),
  "WITH_POSITIVE_IMPACT":    ("No", vid("WITH_POSITIVE_IMPACT","No")),
  "MPN":                     ("TH-CLASSIC-3PK-BLK", None),
  "HAZMAT_TRANSPORTABILITY": ("Exceptuado", vid("HAZMAT_TRANSPORTABILITY","Exceptuado")),
  "IS_KIT":                  ("Sí", vid("IS_KIT","Sí")),
  "SHIPMENT_PACKING":        ("Bolsa", vid("SHIPMENT_PACKING","Bolsa")),
  "IS_SUITABLE_FOR_SHIPMENT":("Sí", vid("IS_SUITABLE_FOR_SHIPMENT","Sí")),
  "IS_FLAMMABLE":            ("No", vid("IS_FLAMMABLE","No")),
  "HAS_COMPATIBILITIES":     ("No", vid("HAS_COMPATIBILITIES","No")),
  "IS_NEW_OFFER":            ("Sí", vid("IS_NEW_OFFER","Sí")),
  "SELLER_SKU":              ("TH-SOCK-3PK-BLK-OS", None),
  "VALUE_ADDED_TAX":         ("16 %", None),
  "DESCRIPTIVE_TAGS":        ("classic, ribbed, cotton, mens, gift", None),
  "CATALOG_TITLE":           ("Calcetines Tommy Hilfiger Hombre Pack 3 Pares Negro", None),
}

to_set=[]
for aid,(name,vval) in desired.items():
  if aid not in attr_map: continue
  a={"id":aid,"value_name":name}
  if vval: a["value_id"]=vval
  to_set.append(a)

print(f"trying {len(to_set)} attrs")

# Batch attempt with progressive removal of bad ones
attempt=list(to_set)
ok_set=set()
for round_n in range(5):
  if not attempt: break
  p=requests.put(f"{API}/items/{IID}",headers=HJ,json={"attributes":attempt},timeout=30)
  if p.status_code<400:
    print(f"  round {round_n}: ✅ all {len(attempt)} accepted")
    for a in attempt: ok_set.add(a["id"])
    break
  err=p.json() if p.headers.get("content-type","").startswith("application/json") else {}
  bad=set()
  for c in err.get("cause",[]):
    msg=c.get("message","")
    m=re.search(r"Attribute \[([A-Z_]+)\]", msg)
    if m: bad.add(m.group(1))
    print(f"  round {round_n}: {c.get('code','')}: {msg[:150]}")
  if not bad:
    print(f"  no parseable bad attr; stopping")
    break
  before=len(attempt)
  attempt=[a for a in attempt if a["id"] not in bad]
  print(f"  removed {before-len(attempt)} bad; retry with {len(attempt)}")

# Individual fallback for the difficult ones
remaining=[a for a in to_set if a["id"] not in ok_set]
if remaining:
  print(f"\nindividual fallback for {len(remaining)}:")
  for a in remaining:
    pp=requests.put(f"{API}/items/{IID}",headers=HJ,json={"attributes":[a]},timeout=20)
    if pp.status_code<400:
      ok_set.add(a["id"])
      print(f"  ✓ {a['id']}")
    else:
      print(f"  ✗ {a['id']}: {pp.text[:200]}")

# Final check
g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
filled=sum(1 for a in g.get("attributes",[]) if a.get("value_name") or a.get("value_id"))
total=len(g.get("attributes",[]))
print(f"\n✅ AFTER: {filled}/{total} attrs filled (added: {len(ok_set)})")
