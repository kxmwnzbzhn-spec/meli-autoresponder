import os, requests
import meli_token
SRC="MLM5346655686"; API="https://api.mercadolibre.com"
WT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
HW={"Authorization":f"Bearer {WT}"}; HWJ={**HW,"Content-Type":"application/json"}
s=requests.get(f"{API}/items/{SRC}",headers=HW,timeout=20).json()
# subir fotos a Wilbert (re-upload por url source)
sess=requests.Session(); allah=[]
for p in (s.get("pictures") or []):
    url=p.get("secure_url") or p.get("url")
    if not url: continue
    img=sess.get(url,timeout=60).content
    rp=requests.post(f"{API}/pictures/items/upload",headers=HW,files={"file":("p.jpg",img,"image/jpeg")},timeout=120)
    if rp.status_code<300: allah.append(rp.json().get("id"))
# colores y mapeo de pics por variante (segun la fuente, fallback compartido)
src_map={}
for ip,p in enumerate(s.get("pictures") or []):
    if p.get("id") and ip<len(allah): src_map[p["id"]]=allah[ip]
colors=[]
for v in (s.get("variations") or []):
    for c in (v.get("attribute_combinations") or []):
        if c.get("id")=="COLOR" or c.get("name")=="Color":
            if c.get("value_name") not in colors: colors.append(c.get("value_name"))
# 50 piezas distribuidas
n=len(colors); base=50//n; rem=50-base*n
dist=[base+(1 if i<rem else 0) for i in range(n)]
print("colors:",colors,"| dist:",dist,"| pics:",len(allah))
variations=[]
for i,col in enumerate(colors):
    # mapear picture_ids del variation original al nuevo upload
    vp=[]
    for v in (s.get("variations") or []):
        if any(c.get("value_name")==col and (c.get("id")=="COLOR" or c.get("name")=="Color") for c in (v.get("attribute_combinations") or [])):
            for pid in (v.get("picture_ids") or []):
                if pid in src_map: vp.append(src_map[pid])
            break
    if not vp: vp=allah[:3]
    variations.append({"attribute_combinations":[{"id":"COLOR","value_name":col}],
                       "picture_ids":vp[:10],"available_quantity":dist[i],"price":299})
payload={"site_id":"MLM","title":s.get("title"),"category_id":s.get("category_id"),
         "currency_id":"MXN","buying_mode":"buy_it_now","listing_type_id":s.get("listing_type_id") or "gold_special",
         "condition":s.get("condition") or "used",
         "pictures":[{"id":x} for x in allah],
         "attributes":[{"id":"BRAND","value_name":"Genérico"},{"id":"MODEL","value_name":"Genérico"}],
         "variations":variations}
r=requests.post(f"{API}/items",headers=HWJ,json=payload,timeout=60)
print("publish http:",r.status_code)
if r.status_code>=300:
    print("body:",r.text[:600]); raise SystemExit(0)
nid=r.json().get("id")
print("NEW:",nid,"status:",r.json().get("status"))
# descripcion reescrita: color aleatorio, no garantizado
desc=(
"⚠ IMPORTANTE - LEE ANTES DE COMPRAR ⚠\n\n"
"El COLOR seleccionado al momento de la compra NO SE GARANTIZA. "
"Este producto se envía con COLOR ALEATORIO según disponibilidad en almacén. "
"Si el color es decisivo para ti, por favor NO realices la compra; cualquier reclamo "
"por color recibido NO procederá.\n\n"
"---\n\n"
"BOCINA BLUETOOTH PORTÁTIL — Calidad Premium\n\n"
"• Diseño compacto y ultra portátil, ideal para llevar a cualquier lugar.\n"
"• Bluetooth 5.3 con conexión rápida y estable.\n"
"• Resistente al agua y polvo (IP67).\n"
"• Sonido potente con bajos profundos.\n"
"• Batería recargable de larga duración.\n"
"• Acabado y materiales premium.\n\n"
"Producto OEM/genérico — no se trata de marca original. Se incluye 1 cable de carga.\n\n"
"Envío inmediato. Cualquier duda, contáctanos antes de comprar."
)
rd=requests.post(f"{API}/items/{nid}/description",headers=HWJ,json={"plain_text":desc},timeout=30)
print("description http:",rd.status_code,"| PERMALINK:",r.json().get("permalink"))
print("DONE")
