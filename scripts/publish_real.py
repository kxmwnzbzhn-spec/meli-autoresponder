"""FINAL: fetch chart rows, publish 1 listing in MLM194115 with variations S/M/L."""
import os, requests, json, time
API="https://api.mercadolibre.com"
CHART="5915675"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

# Get chart
print(f"\n=== Fetching chart {CHART} ===")
ch=requests.get(f"{API}/catalog/charts/{CHART}",headers=H,timeout=10).json()
print(f"Chart name: {ch.get('names',{}).get('MLM')}")
size_to_row={}
for row in (ch.get("rows") or []):
    row_id=row.get("id")
    size_val=None
    for a in (row.get("attributes") or []):
        if a.get("id")=="SIZE":
            vs=a.get("values") or []
            if vs: size_val=vs[0].get("name")
            break
    if size_val:
        size_to_row[size_val]=row_id
        print(f"  {size_val} → {row_id}")

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
DESIRED_SIZES=["S","M","L"]
variations=[]
for s in DESIRED_SIZES:
    rid=size_to_row.get(s)
    if not rid:
        print(f"  [WARN] talla {s} no encontrada en el chart")
        continue
    variations.append({
        "attribute_combinations":[
            {"id":"SIZE_GRID_ROW_ID","value_id":rid},
            {"id":"SIZE","value_name":s},
        ],
        "available_quantity":1,
        "price":799,
        "picture_ids":PICS,
    })

payload={
    "title":"Calvin Klein Pack 3 Boxers Microfibra Hombre Premium",
    "category_id":"MLM194115",
    "price":799,
    "currency_id":"MXN",
    "available_quantity":len(variations),
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":[{"source":u} for u in PICS],
    "attributes":[
        {"id":"BRAND","value_name":"Calvin Klein"},
        {"id":"MODEL","value_name":"Brief"},
        {"id":"GENDER","value_name":"Hombre"},
        {"id":"COLOR","value_name":"Mixto"},
        {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
        {"id":"SIZE_GRID_ID","value_name":CHART},
    ],
    "variations":variations,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== POST /items/validate ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
print(f"HTTP {rv.status_code}: {rv.text[:1500]}")

print("\n=== POST /items (real) ===")
rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"HTTP {rp.status_code}")
print(rp.text[:2000])

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ PUBLISHED {iid}")
    print(f"Permalink: {link}")
    for v in (it.get("variations") or []):
        print(f"  variation_id={v.get('id')} attrs={v.get('attribute_combinations')} qty={v.get('available_quantity')} price={v.get('price')}")
    DESC=(
"Pack de 3 boxers Calvin Klein de microfibra premium, importados de USA. "
"Disenados para maxima comodidad y ajuste perfecto durante todo el dia.\n\n"
"CARACTERISTICAS\n"
"- Marca: Calvin Klein\n"
"- Modelo: Brief\n"
"- Material: Microfibra sedosa de alta calidad\n"
"- Colores incluidos: Negro, gris oxford y gris cemento (mixto)\n"
"- Cantidad por pack: 3 boxers\n"
"- Cintura con elastico ancho y logo Calvin Klein\n\n"
"GUIA DE TALLAS - Calvin Klein Hombre\n"
"- Talla S: Cintura 71-76 cm, Cadera 86-91 cm\n"
"- Talla M: Cintura 81-86 cm, Cadera 94-99 cm\n"
"- Talla L: Cintura 91-97 cm, Cadera 102-107 cm\n\n"
"IMPORTADOS DE USA. Producto 100 por ciento original Calvin Klein.\n"
"Envio inmediato. Garantia 30 dias por defectos de fabricacion."
)
    rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
    print(f"\n[DESC] HTTP {rd.status_code}: {rd.text[:300]}")
