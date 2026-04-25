import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

SRC="MLM2883448187"
src=requests.get(f"https://api.mercadolibre.com/items/{SRC}?include_attributes=all",headers=H).json()
print(f"Source: {src.get('title')[:60]} | catalog={src.get('catalog_product_id')}")

# Re-subir pics por color (re-upload para garantizar que estan en cuenta Juan)
def reup(pid):
    try:
        img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

color_pics={}
for v in (src.get("variations") or []):
    color=None
    for ac in v.get("attribute_combinations",[]):
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    pids=v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
    new_ids=[]
    for p in pids[:4]:
        n=reup(p)
        if n: new_ids.append(n)
    color_pics[color]=new_ids
    print(f"  {color}: {len(new_ids)} pics")

# Construir variations remanufacturadas
variations=[]
for c,pics in color_pics.items():
    if not pics: continue
    variations.append({
        "price":399,"available_quantity":1,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids":pics,
    })
all_pics=[]
for c,pids in color_pics.items():
    for p in pids:
        if p not in all_pics: all_pics.append(p)

# Atributos
cat_id=src.get("category_id","MLM59800")
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H).json()

attrs=[
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Go 4"},
    {"id":"ITEM_CONDITION","value_name":"Reacondicionado"},
    {"id":"WARRANTY","value_name":"30 dias del vendedor"},
]
seen={x["id"] for x in attrs}
BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","GTIN","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","LINE","GRADING","HAS_MICROPHONE","IS_DUAL_VOICE_COIL","WITH_HANDSFREE_FUNCTION","HAS_LED_LIGHTS","IS_DUAL_VOICE_ASSISTANTS","HAS_FM_RADIO","HAS_SD_MEMORY_INPUT","HAS_APP_CONTROL","WITH_AUX","HAS_USB_INPUT"}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    vals=ca.get("values") or []; vt=ca.get("value_type")
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

TITLE="Bocina Jbl Go 4 Bluetooth Ip67 Reacondicionada Excelente"[:60]

body={
    "site_id":"MLM","title":TITLE,
    "category_id":cat_id,"currency_id":"MXN",
    "listing_type_id":"gold_special",
    "condition":"refurbished",
    "buying_mode":"buy_it_now",
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":attrs,
    "variations":variations,
}

print("\n=== POST item REACONDICIONADO ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
if rp.status_code in (200,201):
    NID=rp.json()["id"]
    print(f"*** OK {NID} ***")
    DESC="""BOCINA JBL GO 4 BLUETOOTH PORTATIL IP67 - REACONDICIONADA EN EXCELENTE ESTADO

ESTADO DEL PRODUCTO:
- Producto REACONDICIONADO en excelente estado de funcionamiento.
- Probada, limpiada y verificada al 100% antes del envio.
- Puede presentar marcas MINIMAS de uso normal por tratarse de producto reacondicionado.
- Bateria, sonido, conectividad y resistencia al agua probados.

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 estable hasta 10 metros
- Resistencia al agua y polvo grado IP67
- Bateria recargable con autonomia de 7 horas
- Sonido JBL Pro Sound potente
- Manos libres con microfono integrado
- Puerto USB-C para carga rapida
- 6 colores disponibles: Negro, Azul, Rojo, Rosa, Camuflaje, Aqua

INFORMACION TECNICA IMPORTANTE - LEA ANTES DE COMPRAR:
- Este modelo NO es compatible con la aplicacion JBL Portable.
- Este modelo NO es compatible con Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- Al comprar usted declara aceptar estas caracteristicas tecnicas.

QUE INCLUYE:
- 1 Bocina JBL Go 4 reacondicionada
- 1 Cable USB-C de carga
- Caja (puede no ser la original)

VERIFICACION DE AUTENTICIDAD:
Producto JBL original con codigos UPC/EAN oficiales. Puede validar el numero de serie en jbl.com.mx o llamando a JBL Mexico 01-800-005-5252.

GARANTIA DEL VENDEDOR:
- 30 dias por defectos de fabrica comprobables con video.
- NO aplica garantia oficial del fabricante por tratarse de producto reacondicionado.
- NO cubre danos por agua excesiva, caidas, mal uso o desgaste estetico normal.

POLITICA DE DEVOLUCIONES:
- El producto se vende tal como se describe.
- NO se aceptan reclamos por compatibilidad con app o Auracast (declarado expresamente).
- NO se aceptan reclamos sin peritaje tecnico oficial.
- NO se aceptan devoluciones por cambio de opinion ni por marcas esteticas minimas propias del reacondicionamiento.

ENVIO GRATIS - Despacho 24 horas habiles.

Al completar la compra usted declara haber leido y aceptar todos los terminos."""
    rd=requests.put(f"https://api.mercadolibre.com/items/{NID}/description",headers=H,json={"plain_text":DESC},timeout=30)
    print(f"desc: {rd.status_code}")
else:
    print(json.dumps(rp.json(),ensure_ascii=False)[:1500])
