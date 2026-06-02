"""Plan B: publish 3 separate tradicional items (S, M, L) — avoids SIZE_GRID requirement."""
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
DESC="""Pack de 3 boxers Calvin Klein de microfibra premium, importados de USA. Diseñados para máxima comodidad y ajuste perfecto durante todo el día.

🔹 CARACTERÍSTICAS
• Marca: Calvin Klein
• Modelo: Brief
• Material: Microfibra sedosa de alta calidad
• Colores incluidos: Negro, gris oxford, gris cemento (mixto)
• Cantidad por pack: 3 boxers
• Cintura con elástico ancho y logo Calvin Klein
• Acabado premium, sin marcas en la piel

🔹 GUÍA DE TALLAS (Calvin Klein Hombre)
• Talla S — Cintura 71-76 cm | Cadera 86-91 cm | Peso aprox 55-65 kg
• Talla M — Cintura 81-86 cm | Cadera 94-99 cm | Peso aprox 65-75 kg
• Talla L — Cintura 91-97 cm | Cadera 102-107 cm | Peso aprox 75-85 kg

🔹 IMPORTADOS DE USA — Producto 100% original Calvin Klein.

🔹 ENVÍO Y GARANTÍA
• Envío inmediato.
• Garantía del vendedor: 30 días por defectos de fabricación.
• Atención por mensajes a través de MercadoLibre."""

SIZES=[
    ("S","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla S"),
    ("M","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla M"),
    ("L","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla L"),
]

published=[]
for size,title in SIZES:
    print(f"\n========== TALLA {size} ==========")
    print(f"title='{title}' ({len(title)} chars)")
    payload={
        "title":title,
        "category_id":"MLM194115",
        "price":799,
        "currency_id":"MXN",
        "available_quantity":1,
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
            {"id":"SIZE","value_name":size},
        ],
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"},
        ],
    }
    # Validate
    rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
    print(f"  validate HTTP {rv.status_code}: {rv.text[:600]}")
    if rv.status_code not in (200,204):
        # Try to remove COLOR or other optional? Print and skip
        print(f"  [SKIP {size}] validation failed")
        continue
    # Real POST
    rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"  POST HTTP {rp.status_code}")
    if rp.status_code in (200,201):
        it=rp.json(); iid=it.get("id"); link=it.get("permalink")
        print(f"  ✅ {iid} | {link}")
        # Description
        rd=requests.put(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
        print(f"  [DESC] HTTP {rd.status_code}")
        published.append({"size":size,"item_id":iid,"link":link,"title":title})
        # Supabase actions_log
        if SBH:
            requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
                json={"account":"ADRIAN","item_id":iid,"action_type":"publish_tradicional",
                      "from_value":"none","to_value":f"talla={size} qty=1 price=799",
                      "actor":"claude_cowork","details":f"CK Brief CPID base MLM65349937"},
                timeout=10)
    else:
        print(f"  [ERR] {rp.text[:800]}")
    time.sleep(1)

print("\n=== PUBLISHED ===")
for p in published:
    print(f"  Talla {p['size']}: {p['item_id']} → {p['link']}")
print(f"\nTOTAL: {len(published)}/3")
