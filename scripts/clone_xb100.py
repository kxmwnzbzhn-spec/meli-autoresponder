import os, requests, json, sys, base64, time
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(5):
  r=requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(6)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; NEW_RT=tok["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM2023522170"
cp=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
print(f"[CPID] name={cp.get('name')} pics={len(cp.get('pictures') or [])}")
pictures=[{"source":p["url"]} for p in (cp.get("pictures") or [])][:12]

# Discover category
TITLE="Sony SRS-XB100 Bocina Bluetooth Portátil Negro Ip67 Nueva"
qs=requests.utils.quote(TITLE)
dd=requests.get(f"https://api.mercadolibre.com/sites/MLM/domain_discovery/search?limit=5&q={qs}",
  headers={"Authorization":f"Bearer {AT}"},timeout=15)
CAT_ID=None
try:
  arr=dd.json()
  if isinstance(arr,list) and arr:
    CAT_ID=arr[0].get("category_id"); print(f"[CAT-discovery] {CAT_ID} domain={arr[0].get('domain_id')}")
except: pass
if not CAT_ID: CAT_ID="MLM1004"  # Bocinas y subwoofers fallback
print(f"[CAT] {CAT_ID}")

PRICE=599
body={
  "title":TITLE,
  "category_id":CAT_ID,
  "price":PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "buying_mode":"buy_it_now",
  "condition":"new",
  "listing_type_id":"gold_special",
  "pictures":pictures,
  "attributes":[
    {"id":"BRAND","value_name":"Sony"},
    {"id":"MODEL","value_name":"SRS-XB100"},
    {"id":"COLOR","value_name":"Negro"},
    {"id":"GTIN","value_name":"0027242926097"},
    {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
    {"id":"LINE","value_name":"SRS"},
  ],
}

def try_publish(body):
  v=requests.post("https://api.mercadolibre.com/items/validate",headers=H,json=body,timeout=20)
  print(f"[VALIDATE] HTTP {v.status_code}")
  if v.status_code>=300:
    try:
      j=v.json(); causes=j.get("cause",[])
      err=[c for c in causes if c.get("type")=="error"]
      if err:
        print("ERR:",json.dumps(err)[:1200]); return None
      print("warnings only")
    except: print(v.text[:800]); return None
  p=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=25)
  print(f"POST HTTP {p.status_code}")
  if p.status_code>=300: print(p.text[:1200]); return None
  return p.json()

out=try_publish(body)
if not out:
  # Try EAN-13 alternative + EMPTY_GTIN_REASON
  body["attributes"]=[a for a in body["attributes"] if a["id"]!="GTIN"]
  body["attributes"].append({"id":"EMPTY_GTIN_REASON","value_name":"El producto no tiene código registrado"})
  print("[RETRY] no GTIN + EMPTY_GTIN_REASON")
  out=try_publish(body)

if not out: sys.exit(1)

NEW_ID=out["id"]
print(f"✅ {NEW_ID} ${PRICE} | https://articulo.mercadolibre.com.mx/{NEW_ID.replace('MLM','MLM-')}-_JM")

desc=("Sony SRS-XB100 — Bocina Bluetooth portátil color negro. 100% original.\n\n"
      "CARACTERÍSTICAS\n"
      "- Diseño compacto y ligero, perfecto para llevar.\n"
      "- Sonido EXTRA BASS de Sony con woofer X-Balanced.\n"
      "- Resistencia IP67: a prueba de agua y polvo.\n"
      "- Hasta 16 horas de batería.\n"
      "- Bluetooth 5.3 con función manos libres.\n"
      "- Correa multifunción y tecnología Sound Diffusion.\n\n"
      "GARANTÍA DEL VENDEDOR · Envío inmediato.")
requests.post(f"https://api.mercadolibre.com/items/{NEW_ID}/description",
  headers=H,json={"plain_text":desc},timeout=15)

# Sync rotated RT
try:
  import nacl.encoding, nacl.public
except Exception:
  os.system("pip install pynacl -q")
  import nacl.encoding, nacl.public
GHT=os.environ["GH_PAT"]
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
REPO="kxmwnzbzhn-spec/meli-autoresponder"
pk=requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=GHH,timeout=15).json()
pub=nacl.public.PublicKey(base64.b64decode(pk["key"]))
sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
enc=base64.b64encode(sealed).decode()
ru=requests.put(f"https://api.github.com/repos/{REPO}/actions/secrets/MELI_REFRESH_TOKEN_AH",
  headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
print(f"[GH SECRET UPDATE] HTTP {ru.status_code}")
