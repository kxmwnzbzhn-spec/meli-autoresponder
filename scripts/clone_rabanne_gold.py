import os, requests, json, sys, base64, time
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(5):
  r=requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(6)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; NEW_RT=tok["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM51198714"
cp=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
pictures=[{"source":p["url"]} for p in (cp.get("pictures") or [])][:10]
print(f"[pics] {len(pictures)}")

PRICE=2499
TITLE="Rabanne 1 Million Gold Elixir Parfum Intense 100ml Hombre"
body={
  "title":TITLE,
  "category_id":"MLM1271",
  "price":PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "buying_mode":"buy_it_now",
  "condition":"new",
  "listing_type_id":"gold_special",
  "pictures":pictures,
  "attributes":[
    {"id":"BRAND","value_name":"Rabanne"},
    {"id":"GTIN","value_name":"3349668644483"},
    {"id":"PERFUME_NAME","value_name":"1 Million Gold Elixir"},
    {"id":"PERFUME_TYPE","value_name":"Parfum"},
    {"id":"UNIT_VOLUME","value_name":"100 mL"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
    {"id":"MODEL","value_name":"1 Million Gold Elixir Parfum Intense"},
  ],
}

# Validate (warnings OK)
v=requests.post("https://api.mercadolibre.com/items/validate",headers=H,json=body,timeout=20)
print(f"[VALIDATE] HTTP {v.status_code}")
if v.status_code>=300:
  try:
    j=v.json(); causes=j.get("cause",[])
    err=[c for c in causes if c.get("type")=="error"]
    if err: print("ERR:",json.dumps(err)[:1200]); sys.exit(1)
    print("warnings only, proceeding")
  except: print(v.text[:600]); sys.exit(1)

p=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=25)
print(f"POST HTTP {p.status_code}")
if p.status_code>=300: print(p.text[:1200]); sys.exit(1)
out=p.json(); NEW_ID=out["id"]
print(f"✅ {NEW_ID} ${PRICE} | https://articulo.mercadolibre.com.mx/{NEW_ID.replace('MLM','MLM-')}-_JM")

desc=("Rabanne 1 Million Gold Elixir Parfum Intense 100 ml — Hombre.\n\n"
      "Producto 100% original importado.\n\n"
      "FAMILIA OLFATIVA: Oriental Amaderada con un acorde dorado intenso.\n"
      "NOTAS DE SALIDA: Bergamota, Cardamomo.\n"
      "NOTAS DE CORAZÓN: Canela, Cuero.\n"
      "NOTAS DE FONDO: Ámbar, Maderas preciosas, Vainilla.\n\n"
      "PRESENTACIÓN: Spray 100 ml.\nDURACIÓN: 10-12 horas en piel.\n\n"
      "GARANTÍA DEL VENDEDOR · Envío inmediato.")
requests.post(f"https://api.mercadolibre.com/items/{NEW_ID}/description",
  headers=H,json={"plain_text":desc},timeout=15)

# Setup priority replenish: stock=1, repone 30s
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json",
     "Prefer":"return=representation,resolution=merge-duplicates"}
rp=requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
  json={"item_id":NEW_ID,"account":"AH","default_qty":1,"product_name":TITLE},timeout=12)
print(f"[priority_replenish] HTTP {rp.status_code}")
rd=requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
  json={"account":"AH","scope":"item","scope_value":NEW_ID,
        "directive_type":"priority_replenish","value_numeric":1,
        "raw_user_message":"1 unidad a la vista + replenish c/venta"},timeout=12)
print(f"[directive] HTTP {rd.status_code}")

# Sync RT
try: import nacl.encoding, nacl.public
except Exception: os.system("pip install pynacl -q"); import nacl.encoding, nacl.public
GHT=os.environ["GH_PAT"]
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
R="kxmwnzbzhn-spec/meli-autoresponder"
pk=requests.get(f"https://api.github.com/repos/{R}/actions/secrets/public-key",headers=GHH,timeout=15).json()
pub=nacl.public.PublicKey(base64.b64decode(pk["key"]))
sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
enc=base64.b64encode(sealed).decode()
ru=requests.put(f"https://api.github.com/repos/{R}/actions/secrets/MELI_REFRESH_TOKEN_AH",
  headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
print(f"[GH SECRET] HTTP {ru.status_code}")
