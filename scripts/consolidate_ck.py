"""Close 3 published items, publish 1 with 3 variations (S, M, L), fix description."""
import os, requests, json, time
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation"} if SBK else None

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

# === STEP 1: close 3 previous items ===
print("\n=== CLOSE previous 3 items ===")
for iid in ["MLM5444637526","MLM5444848314","MLM5444797814"]:
    rp=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=15)
    print(f"  {iid} → HTTP {rp.status_code}")
    time.sleep(0.5)

# === STEP 2: publish 1 item with 3 variations ===
PICS=[
  "https://http2.mlstatic.com/D_NQ_NP_743804-MLA106119402584_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_958202-MLA106740502843_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_890097-MLA106741215883_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_909047-MLA106740740811_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_639680-MLA106741215897_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_977787-MLA106740622519_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_964357-MLA106119905012_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_886035-MLA106120083064_022026-F.jpg",
]
TITLE="Calvin Klein Pack 3 Boxers Microfibra Hombre Premium"  # 52 chars, no size

DESC = (
"Pack de 3 boxers Calvin Klein de microfibra premium, importados de USA. "
"Disenados para maxima comodidad y ajuste perfecto durante todo el dia.\n\n"
"CARACTERISTICAS\n"
"- Marca: Calvin Klein\n"
"- Modelo: Brief\n"
"- Material: Microfibra sedosa de alta calidad\n"
"- Colores incluidos: Negro, gris oxford y gris cemento (mixto)\n"
"- Cantidad por pack: 3 boxers\n"
"- Cintura con elastico ancho y logo Calvin Klein\n\n"
"GUIA DE TALLAS Calvin Klein Hombre\n"
"- Talla S: Cintura 71-76 cm, Cadera 86-91 cm, Peso aprox 55-65 kg\n"
"- Talla M: Cintura 81-86 cm, Cadera 94-99 cm, Peso aprox 65-75 kg\n"
"- Talla L: Cintura 91-97 cm, Cadera 102-107 cm, Peso aprox 75-85 kg\n\n"
"IMPORTADOS DE USA. Producto 100 por ciento original Calvin Klein.\n"
"Envio inmediato. Garantia 30 dias por defectos de fabricacion."
)

SIZES=["S","M","L"]
VARS=[]
for s in SIZES:
    VARS.append({
        "attribute_combinations":[{"id":"CLOTHING_LOT_SIZE","value_name":s}],
        "available_quantity":1,
        "price":799,
        "picture_ids":[u for u in PICS],
    })

payload={
    "title":TITLE,
    "category_id":"MLM431078",
    "price":799,
    "currency_id":"MXN",
    "available_quantity":3,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":[{"source":u} for u in PICS],
    "attributes":[
        {"id":"BRAND","value_name":"Calvin Klein"},
        {"id":"MODEL","value_name":"Brief"},
        {"id":"COLOR","value_name":"Mixto"},
    ],
    "variations":VARS,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== POST /items (1 listing, 3 variations) ===")
rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"HTTP {rp.status_code}: {rp.text[:1500]}")

if rp.status_code in (200,201):
    item=rp.json(); iid=item.get("id"); link=item.get("permalink")
    print(f"\n✅ NEW ITEM {iid}")
    print(f"  Permalink: {link}")
    print(f"  Variations: {len(item.get('variations') or [])}")
    
    # === STEP 3: description (sin emojis) ===
    print("\n=== Description ===")
    r1=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
    print(f"  POST: HTTP {r1.status_code}: {r1.text[:300]}")
    if r1.status_code not in (200,201):
        r2=requests.put(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
        print(f"  PUT: HTTP {r2.status_code}: {r2.text[:300]}")
    
    if SBH:
        requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
            json={"account":"ADRIAN","item_id":iid,"action_type":"publish_tradicional_variations",
                  "from_value":"MLM5444637526,MLM5444848314,MLM5444797814 (3 items)",
                  "to_value":f"{iid} con 3 variaciones S/M/L",
                  "actor":"claude_cowork","details":"CK Brief CPID base MLM65349937"},timeout=10)
else:
    print(f"\n[FAIL] no se pudo publicar con variations: {rp.text[:1500]}")
