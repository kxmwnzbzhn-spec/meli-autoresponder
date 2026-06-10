import os, requests, json, sys, base64, time
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for attempt in range(5):
  r=requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(8)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; NEW_RT=tok["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM34280293"
cp=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
print(f"[CPID] name={cp.get('name')}")
pictures=[{"source":p["url"]} for p in (cp.get("pictures") or [])]
print(f"[CPID] pics={len(pictures)}")

# Find category via domain_discovery
TITLE="Kerastase Aceite Capilar Elixir Ultime L Huile Originale 100ml"
qs=requests.utils.quote(TITLE)
dd=requests.get(f"https://api.mercadolibre.com/sites/MLM/domain_discovery/search?limit=5&q={qs}",
  headers={"Authorization":f"Bearer {AT}"},timeout=15)
print(f"[domain_discovery] HTTP {dd.status_code} body={dd.text[:400]}")
CAT_ID=None
try:
  arr=dd.json()
  if isinstance(arr,list) and arr:
    CAT_ID=arr[0].get("category_id")
    print(f"[CAT-discovery] {CAT_ID} domain={arr[0].get('domain_id')}")
except Exception: pass
if not CAT_ID:
  # Fallback to HAIR_OILS direct category
  CAT_ID="MLM174181"  # Aceites para el cabello
print(f"[CAT] {CAT_ID}")

PRICE=1199
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
    {"id":"BRAND","value_name":"Kérastase"},
    {"id":"LINE","value_name":"Elixir Ultime"},
    {"id":"MODEL","value_name":"Elixir Ultime L'Huile Originale"},
    {"id":"CONSISTENCY","value_name":"Aceite"},
    {"id":"NET_VOLUME","value_name":"100 mL"},
    {"id":"NET_WEIGHT","value_name":"100 g"},
    {"id":"UNITS_PER_PACK","value_name":"1"},
    {"id":"FUNCTIONS","value_name":"Acabado"},
    {"id":"MAJOR_INGREDIENTS","value_name":"Aceite de Marula, Aceite de camelia, Argán"},
    {"id":"PACKAGING_TYPE","value_name":"Dosificador"},
    {"id":"SALE_FORMAT","value_name":"Unidad"},
    {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
    {"id":"GTIN","value_name":"3474636397495"},
    {"id":"IS_DERMATOLOGICALLY_TESTED","value_name":"Sí"},
    {"id":"IS_VEGAN","value_name":"No"},
    {"id":"IS_GLUTEN_FREE","value_name":"Sí"},
    {"id":"IS_ALCOHOL_FREE","value_name":"No"},
    {"id":"IS_CRUELTY_FREE","value_name":"Sí"},
    {"id":"WITH_EXPIRATION_DATE","value_name":"Sí"},
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
        print("ERR:",json.dumps(err)[:1200])
        return None
      print("warnings only, proceeding")
    except Exception:
      print(v.text[:1500]); return None
  p=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=25)
  print(f"POST HTTP {p.status_code}")
  if p.status_code>=300:
    print(p.text[:1500]); return None
  return p.json()

out=try_publish(body)
if not out:
  # retry with EMPTY_GTIN_REASON if GTIN is asked
  body["attributes"].append({"id":"EMPTY_GTIN_REASON","value_name":"El producto no tiene código registrado"})
  print("[RETRY] adding EMPTY_GTIN_REASON")
  out=try_publish(body)

if not out:
  sys.exit(1)

NEW_ID=out["id"]
print(f"✅ {NEW_ID} ${PRICE} | http://articulo.mercadolibre.com.mx/{NEW_ID.replace('MLM','MLM-')}-_JM")

desc=("Kérastase Elixir Ultime L'Huile Originale — Aceite capilar nutritivo 100 ml.\n\n"
      "Producto 100% original, importado.\n"
      "Aceite embellecedor multiusos formulado con la mezcla exclusiva de 4 aceites preciosos: "
      "Argán, Marula, Camelia y Pracaxi. Aporta brillo extremo, nutrición profunda y protege "
      "del calor hasta 230°C.\n\n"
      "MODO DE USO\n"
      "- Cabello húmedo: 1-2 dosis antes del peinado.\n"
      "- Cabello seco: 1 dosis para retoques de brillo durante el día.\n\n"
      "GARANTÍA DEL VENDEDOR — Envío inmediato.")
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
