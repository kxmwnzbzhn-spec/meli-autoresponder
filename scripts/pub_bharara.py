import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CAT="MLM194118"
IID="MLM3025719815"

# 1) Dump all attrs for category with values (to pick valid IDs)
ats=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=15).json()
print(f"cat attrs available: {len(ats)}")

attr_map={}
for a in ats:
  aid=a["id"]
  attr_map[aid]=a

# Get current item state
g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
current_ids=set(a["id"] for a in g.get("attributes",[]) if a.get("value_name") or a.get("value_id"))
print(f"current filled: {len(current_ids)}")

# Build value mapping per attribute id
# For list types use value_id when needed
def get_value_id(aid, name):
  a=attr_map.get(aid,{})
  vs=a.get("values") or []
  for v in vs:
    if (v.get("name") or "").lower()==name.lower():
      return v.get("id")
  return None

# Mapping per attribute id with desired value
desired = {
  "BRAND": ("Tommy Hilfiger", None),
  "MODEL": ("Pack 3 Pares", None),
  "LINE": ("Classic", None),
  "ALPHANUMERIC_MODEL": ("TH-3PK", None),
  "MAIN_COLOR": ("Negro", get_value_id("MAIN_COLOR","Negro")),
  "COLOR": ("Negro", None),
  "GENDER": ("Hombre", get_value_id("GENDER","Hombre")),
  "AGE_GROUP": ("Adultos", get_value_id("AGE_GROUP","Adultos")),
  "ITEM_CONDITION": ("Nuevo", get_value_id("ITEM_CONDITION","Nuevo")),
  "SIZE": ("Único", None),
  "SOCKS_TYPE": ("Pantorrillero", get_value_id("SOCKS_TYPE","Pantorrillero")),
  "LENGTH_TYPE": ("3/4", get_value_id("LENGTH_TYPE","3/4")),
  "MAIN_MATERIAL": ("Algodón", None),
  "FABRIC_DESIGN": ("Liso", None),
  "DESIGN": ("Liso", None),
  "PRINT": ("Liso", None),
  "PATTERN": ("Liso", None),
  "UNITS_PER_PACK": ("3", None),
  "PACK_SIZE": ("3", None),
  "FOOT_LENGTH": ("Estándar", None),
  "SOCKS_USE": ("Casual", None),
  "RECOMMENDED_USE": ("Diario", None),
  "RECOMMENDED_FOR": ("Casual", None),
  "SPORTS_AND_FITNESS_ACTIVITY": ("Casual", None),
  "WAIST_TYPE": ("Media", None),
  "WITH_ELASTIC_BAND": ("Sí", None),
  "WITH_REINFORCEMENT": ("Sí", None),
  "WITH_PLAIN_SEAM": ("Sí", None),
  "WITH_LOGO": ("Sí", None),
  "WITH_BRAND_LOGO": ("Sí", None),
  "WASHING_TYPE": ("Lavado a máquina", None),
  "CARE_INSTRUCTIONS": ("Lavar a máquina con agua fría", None),
  "MATERIAL_COMPOSITION": ("80% Algodón, 17% Poliéster, 3% Elastano", None),
  "COMPOSITION": ("80% Algodón, 17% Poliéster, 3% Elastano", None),
  "SOCK_HEIGHT": ("Media pantorrilla", None),
  "PACKAGING_TYPE": ("Caja", None),
  "INCLUDES_PACKAGING": ("Sí", None),
  "STYLE": ("Casual", None),
  "SEASON": ("Todo el año", None),
  "WEIGHT": ("90 g", None),
  "SELLER_PACKAGE_LENGTH": ("16 cm", None),
  "SELLER_PACKAGE_WIDTH": ("12 cm", None),
  "SELLER_PACKAGE_HEIGHT": ("4 cm", None),
  "SELLER_PACKAGE_WEIGHT": ("120 g", None),
  "HAZMAT_TRANSPORTABILITY": ("No es peligroso", None),
  "GTIN": ("0088541002493", None),  # placeholder Tommy socks UPC
  "SHAFT_TYPE": ("Pantorrillera", None),
  "WITH_NON_SLIP_SOLE": ("No", None),
  "IS_TRANSPARENT": ("No", None),
  "IS_THERMAL": ("No", None),
  "IS_COMPRESSION": ("No", None),
  "TOE_SHAPE": ("Reforzada", None),
  "MATERIAL_DETAIL": ("Algodón premium con elastano", None),
}

# Build payload only with attrs that exist in category
to_set=[]
for aid,(name,vid) in desired.items():
  if aid not in attr_map: continue
  a={"id":aid,"value_name":name}
  if vid: a["value_id"]=vid
  to_set.append(a)

print(f"sending {len(to_set)} attrs")

# Try in batches in case some are invalid (errors stop whole PUT)
# First try all at once
p=requests.put(f"{API}/items/{IID}",headers=HJ,json={"attributes":to_set},timeout=30)
print(f"PUT all: {p.status_code}")
if p.status_code>=400:
  try:
    err=p.json()
    bad=set()
    for c in err.get("cause",[]):
      msg=c.get("message","")
      print(f"  {c.get('code','')}: {msg[:200]}")
      # Try to extract attribute id from message
      import re
      m=re.search(r"Attribute \[([A-Z_]+)\]", msg)
      if m: bad.add(m.group(1))
    # Retry without bad ones
    if bad:
      retry=[a for a in to_set if a["id"] not in bad]
      print(f"\nretry without {len(bad)} bad: {bad}")
      p2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"attributes":retry},timeout=30)
      print(f"PUT retry: {p2.status_code}")
      if p2.status_code>=400:
        print(p2.text[:800])
        # individual fallback
        print("\nindividual mode...")
        for a in retry:
          pp=requests.put(f"{API}/items/{IID}",headers=HJ,json={"attributes":[a]},timeout=20)
          if pp.status_code<400: print(f"  ✓ {a['id']}")
          else: print(f"  ✗ {a['id']}: {pp.text[:200]}")
  except Exception as e: print("parse err:",e)

# Verify
g2=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
filled=sum(1 for a in g2.get("attributes",[]) if a.get("value_name") or a.get("value_id"))
total=len(g2.get("attributes",[]))
print(f"\n✅ AFTER: {filled}/{total} attrs filled")
