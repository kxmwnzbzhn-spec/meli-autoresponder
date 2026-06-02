"""Publish Calvin Klein 3-pack boxers in Adrián, tradicional, S/M/L (no XL), $799, qty=1 each."""
import os, requests, json
API="https://api.mercadolibre.com"

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

TITLE = "Calvin Klein Pack 3 Boxers Microfibra Hombre Premium"  # 52 chars
DESC = """Pack de 3 boxers Calvin Klein de microfibra premium, importados de USA. Diseñados para máxima comodidad y ajuste perfecto durante todo el día.

🔹 CARACTERÍSTICAS
• Marca: Calvin Klein
• Modelo: Brief
• Material: Microfibra sedosa de alta calidad
• Colores: Mixto (negro, gris oxford, gris cemento)
• Cantidad por pack: 3 boxers
• Cintura con elástico ancho y logo Calvin Klein

🔹 GUÍA DE TALLAS (CK Hombre)
┌────────┬──────────────┬──────────────┬────────────────┐
│ Talla  │ Cintura (cm) │ Cadera (cm)  │ Peso aprox     │
├────────┼──────────────┼──────────────┼────────────────┤
│   S    │   71 – 76    │   86 – 91    │  55 – 65 kg    │
│   M    │   81 – 86    │   94 – 99    │  65 – 75 kg    │
│   L    │   91 – 97    │  102 – 107   │  75 – 85 kg    │
└────────┴──────────────┴──────────────┴────────────────┘

🔹 IMPORTADOS DE USA — Producto 100% original.

🔹 ENVÍO Y GARANTÍA
• Envío inmediato.
• Atención por mensajes a través de MercadoLibre."""

# Item-level attributes (required by category MLM194115)
ITEM_ATTRS=[
    {"id":"BRAND","value_name":"Calvin Klein"},
    {"id":"MODEL","value_name":"Brief"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"COLOR","value_name":"Mixto"},
    {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
]

# Variations: S, M, L — each qty=1
SIZES=["S","M","L"]
VARIATIONS=[]
for s in SIZES:
    VARIATIONS.append({
        "attribute_combinations":[{"id":"SIZE","value_name":s}],
        "available_quantity":1,
        "price":799,
        "picture_ids":[PICS[0],PICS[1],PICS[2]],  # share pics across variations
    })

PAYLOAD={
    "title":TITLE,
    "category_id":"MLM194115",
    "price":799,
    "currency_id":"MXN",
    "available_quantity":3,  # sum across variations
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "description":{"plain_text":DESC},
    "pictures":[{"source":u} for u in PICS],
    "attributes":ITEM_ATTRS,
    "variations":VARIATIONS,
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== PAYLOAD ===")
print(json.dumps(PAYLOAD, ensure_ascii=False, indent=2)[:3000])

# 1) Validate
print("\n=== POST /items/validate ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=PAYLOAD,timeout=20)
print(f"HTTP {rv.status_code}: {rv.text[:2000]}")

# 2) If validation OK or only warnings, do real POST
if rv.status_code in (200, 204):
    print("\n=== POST /items (real) ===")
    # description must go separately on items create
    pl=PAYLOAD.copy()
    desc=pl.pop("description")
    rp=requests.post(f"{API}/items",headers=HJ,json=pl,timeout=30)
    print(f"HTTP {rp.status_code}: {rp.text[:2000]}")
    if rp.status_code in (200,201):
        item=rp.json()
        iid=item.get("id")
        print(f"\n✅ PUBLISHED {iid}")
        # set description
        rd=requests.put(f"{API}/items/{iid}/description",headers=HJ,
                        json={"plain_text":DESC},timeout=20)
        print(f"[DESC] HTTP {rd.status_code}: {rd.text[:300]}")
        print(f"\nPermalink: {item.get('permalink')}")
else:
    print("\n[STOP] Validation failed — no publico hasta arreglar errores.")
