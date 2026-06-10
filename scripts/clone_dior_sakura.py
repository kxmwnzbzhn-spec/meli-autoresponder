import os, requests, json, sys, base64
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; NEW_RT=tok["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

SRC="MLM2969851475"
src=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
pictures=[{"source":p["url"]} for p in (src.get("pictures") or [])]
print(f"[src] pics={len(pictures)} title={src.get('title')}")

PRICE=1999
TITLE="Christian Dior Sakura Eau De Parfum 125ml Unisex Maison"
body={
  "title":TITLE,
  "category_id":"MLM1271",
  "price":PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "buying_mode":"buy_it_now",
  "condition":"new",
  "listing_type_id":"gold_special",
  "pictures":pictures or [{"source":"https://http2.mlstatic.com/D_NQ_NP_2X_650129-MLA84252437094_052025-F.webp"}],
  "attributes":[
    {"id":"BRAND","value_name":"Dior"},
    {"id":"GTIN","value_name":"3348901630184"},
    {"id":"PERFUME_NAME","value_name":"Dior Sakura"},
    {"id":"PERFUME_TYPE","value_name":"Eau de parfum"},
    {"id":"UNIT_VOLUME","value_name":"125 mL"},
    {"id":"GENDER","value_name":"Sin género"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"MODEL","value_name":"Sakura"},
  ],
}

# Validate (warnings OK)
v=requests.post("https://api.mercadolibre.com/items/validate",
  headers=H,json=body,timeout=20)
print(f"[VALIDATE] HTTP {v.status_code}")
if v.status_code>=300:
  try:
    j=v.json(); causes=j.get("cause",[])
    err=[c for c in causes if c.get("type")=="error"]
    if err:
      print("ERR:",json.dumps(err)[:1000]); sys.exit(1)
    print("warnings only, proceeding")
  except Exception:
    print(v.text[:1500]); sys.exit(1)

p=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=25)
print(f"POST HTTP {p.status_code}")
if p.status_code>=300:
  print(p.text[:1500]); sys.exit(1)
out=p.json(); NEW_ID=out["id"]
print(f"✅ {NEW_ID} ${PRICE} | http://articulo.mercadolibre.com.mx/{NEW_ID.replace('MLM','MLM-')}-_JM")

desc=("Christian Dior Sakura Eau de Parfum 125 ml. Unisex. "
      "Maison Christian Dior - Edición exclusiva. Producto 100% original importado. "
      "Envío inmediato y garantía del vendedor.\n\n"
      "FAMILIA OLFATIVA: Floral frutal limpia y luminosa, inspirada en los cerezos en flor de Japón.\n"
      "PRESENTACIÓN: spray 125 ml.\nOCASIÓN: Versátil, ideal para diario.")
requests.post(f"https://api.mercadolibre.com/items/{NEW_ID}/description",
  headers=H,json={"plain_text":desc},timeout=15)

# Sync new RT
try:
  import nacl.encoding, nacl.public
except Exception:
  os.system("pip install pynacl -q")
  import nacl.encoding, nacl.public
GHT=os.environ["GH_PAT"]
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
REPO="kxmwnzbzhn-spec/meli-autoresponder"
pk=requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=GHH,timeout=15).json()
pkb=base64.b64decode(pk["key"]); pub=nacl.public.PublicKey(pkb)
sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
enc=base64.b64encode(sealed).decode()
ru=requests.put(f"https://api.github.com/repos/{REPO}/actions/secrets/MELI_REFRESH_TOKEN_AH",
  headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
print(f"[GH SECRET UPDATE] HTTP {ru.status_code}")
