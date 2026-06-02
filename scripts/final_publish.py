"""Final: publish 1 listing in MLM194115 with SIZE_GRID_ID=5915675 + variations S/M/L."""
import os, requests, json, time
API="https://api.mercadolibre.com"
CHART="5915675"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

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

# Variations: each combines SIZE_GRID_ROW_ID + SIZE
variations=[]
for s in ["S","M","L"]:
    variations.append({
        "attribute_combinations":[
            {"id":"SIZE_GRID_ROW_ID","value_name":s},
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
    "available_quantity":3,
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
print(f"HTTP {rp.status_code}: {rp.text[:2000]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ PUBLISHED {iid}")
    print(f"Permalink: {link}")
    vars=it.get("variations") or []
    print(f"Variations: {len(vars)}")
    for v in vars:
        ac={a.get('id'):a.get('value_name') for a in (v.get('attribute_combinations') or [])}
        print(f"  variation_id={v.get('id')} {ac} qty={v.get('available_quantity')}")
    # Description
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
