"""Publish in MLM431078 with clean attrs + free shipping me2."""
import os, requests, json, time
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
DESC=("Pack de 3 boxers Calvin Klein de microfibra premium, importados de USA.\n\n"
      "🔹 CARACTERÍSTICAS\n"
      "• Marca: Calvin Klein • Modelo: Brief • Material: Microfibra\n"
      "• Colores incluidos: Negro, gris oxford y gris cemento (mixto)\n"
      "• Cantidad por pack: 3 boxers\n"
      "• Cintura con elástico ancho y logo Calvin Klein\n\n"
      "🔹 GUÍA DE TALLAS (CK Hombre)\n"
      "• S — Cintura 71-76 cm | Cadera 86-91 cm | Peso 55-65 kg\n"
      "• M — Cintura 81-86 cm | Cadera 94-99 cm | Peso 65-75 kg\n"
      "• L — Cintura 91-97 cm | Cadera 102-107 cm | Peso 75-85 kg\n\n"
      "🔹 IMPORTADOS DE USA — 100% original.\n"
      "🔹 Envío inmediato. Garantía 30 días por defectos.")

SIZES=[("S","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla S"),
       ("M","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla M"),
       ("L","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla L")]
published=[]
errors=[]
for size,title in SIZES:
    print(f"\n========== TALLA {size} ==========")
    payload={
        "title":title,
        "category_id":"MLM431078",
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
            {"id":"COLOR","value_name":"Mixto"},
            {"id":"CLOTHING_LOT_SIZE","value_name":size},
        ],
        "shipping":{
            "mode":"me2",
            "local_pick_up":False,
            "free_shipping":False,
        },
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"},
        ],
    }
    rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"  POST HTTP {rp.status_code}: {rp.text[:900]}")
    if rp.status_code in (200,201):
        it=rp.json(); iid=it.get("id"); link=it.get("permalink")
        print(f"  ✅ {iid} | {link}")
        rd=requests.put(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
        print(f"  [DESC] HTTP {rd.status_code}")
        published.append({"size":size,"item_id":iid,"link":link})
    else:
        errors.append((size, rp.status_code, rp.text[:600]))
    time.sleep(1)

print(f"\n=== FINAL ===")
for p in published:
    print(f"  Talla {p['size']}: {p['item_id']} → {p['link']}")
print(f"TOTAL: {len(published)}/3")
if errors:
    print("\n=== ERRORS ===")
    for e in errors:
        print(f"  Talla {e[0]}: HTTP {e[1]}: {e[2]}")
