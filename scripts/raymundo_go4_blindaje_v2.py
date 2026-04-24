import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

IID_A="MLM5235542250"

# ===== DESCRIPCION BLINDADA A =====
DESC_A="""BOCINA JBL GO 4 BLUETOOTH PORTATIL IP67 - USADA EN EXCELENTE ESTADO

INFORMACION TECNICA IMPORTANTE - LEA ANTES DE COMPRAR

COMPATIBILIDAD DEL MODELO JBL GO 4:
- Este modelo NO es compatible con la aplicacion JBL Portable.
- Este modelo NO es compatible con Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- No requiere instalacion de aplicacion movil para su funcionamiento.
- Al comprar usted declara haber leido y aceptado expresamente estas caracteristicas tecnicas.

ESTADO DEL PRODUCTO:
- Vendido como USADO en excelente estado de funcionamiento.
- Producto 100% original JBL con caja original, numero de serie SN verificable y codigos UPC/EAN oficiales Harman/JBL impresos en el empaque.
- Puede presentar marcas MINIMAS de uso normal por tratarse de un producto usado.
- Probado y funcionando al 100% antes del envio.

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 estable hasta 10 metros
- Resistencia al agua y polvo grado IP67
- Bateria recargable con autonomia de 7 horas
- Sonido JBL Pro Sound potente
- Manos libres con microfono integrado
- Puerto USB-C para carga rapida
- 6 colores disponibles: Negro, Azul, Rojo, Rosa, Camuflaje, Aqua

QUE INCLUYE:
- 1 Bocina JBL Go 4 USADA
- 1 Cable USB-C de carga
- Caja original

VERIFICACION DE AUTENTICIDAD:
Puede validar la originalidad del producto por cualquiera de estas vias oficiales antes de emitir cualquier reclamo:
1. Portal oficial: jbl.com.mx seccion Verificar producto.
2. Servicio al cliente JBL Mexico: telefono 01-800-005-5252
3. Peritaje tecnico en centro autorizado Harman.

GARANTIA DEL VENDEDOR:
- 30 dias por defectos de fabrica comprobables con video del fallo.
- NO aplica garantia oficial del fabricante por tratarse de producto usado.
- NO cubre danos por agua excesiva, caidas, mal uso o desgaste estetico normal.

POLITICA DE DEVOLUCIONES Y RECLAMOS:
- El producto enviado NO difiere del ofertado: marca, modelo, condicion y caracteristicas coinciden con lo publicado.
- NO se aceptan reclamos por no ser compatible con app JBL Portable. Esta publicacion lo declara expresamente.
- NO se aceptan reclamos por no ser compatible con Auracast. Esta publicacion lo declara expresamente.
- NO se aceptan reclamos por no ser original sin peritaje tecnico oficial.
- NO se aceptan devoluciones por cambio de opinion del comprador.
- NO se aceptan devoluciones por condiciones esteticas minimas propias de un producto USADO.

ENVIO GRATIS - Despacho 24 horas habiles.

Al completar esta compra usted declara haber leido y aceptar todos los terminos anteriores."""

# Probar varios formatos para el update
def update_desc(iid,desc):
    # Try 1: POST create new
    rp=requests.post(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":desc},timeout=30)
    if rp.status_code in (200,201): return "POST_plain",rp.status_code
    # Try 2: PUT plain_text
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":desc},timeout=30)
    if rp.status_code in (200,201): return "PUT_plain",rp.status_code
    # Try 3: PUT text (HTML permite line breaks via <br>)
    html_desc=desc.replace("\n","<br>")
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"text":html_desc},timeout=30)
    if rp.status_code in (200,201): return "PUT_text_html",rp.status_code
    return f"FAIL {rp.status_code}: {rp.text[:300]}",rp.status_code

print("=== Desc A ya aplicada en run anterior, skip ===")

# ========== A/B TEST: Crear publicacion B con titulo/desc distinto ==========
# Leer el item A para clonar pics/variations
cur=requests.get(f"https://api.mercadolibre.com/items/{IID_A}?include_attributes=all",headers=H).json()

# Re-upload pics para nueva publicacion B
def reup(pid):
    try:
        img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

print("\n=== B: re-upload pics ===")
color_pics={}
for v in (cur.get("variations") or []):
    color=None
    for ac in v.get("attribute_combinations",[]):
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    pids=v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
    newids=[]
    for p in pids[:4]:
        n=reup(p)
        if n: newids.append(n)
    color_pics[color]=newids
    print(f"  {color}: {len(newids)}")

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H).json()

def build_attrs_B():
    a=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Go 4"},
        {"id":"ITEM_CONDITION","value_name":"Usado"},
    ]
    seen={x["id"] for x in a}
    BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","GTIN","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","LINE","GRADING","HAS_MICROPHONE","IS_DUAL_VOICE_COIL","WITH_HANDSFREE_FUNCTION","HAS_LED_LIGHTS","IS_DUAL_VOICE_ASSISTANTS","HAS_FM_RADIO","HAS_SD_MEMORY_INPUT","HAS_APP_CONTROL","WITH_AUX","HAS_USB_INPUT"}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD: continue
        vals=ca.get("values") or []; vt=ca.get("value_type")
        if vals: a.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): a.append({"id":aid,"value_name":"1"})
        else: a.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    return a

variations=[]
for c,pics in color_pics.items():
    if not pics: continue
    variations.append({
        "price":299,"available_quantity":1,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids":pics,
    })
all_pics=[]
for pids in color_pics.values():
    for p in pids:
        if p not in all_pics: all_pics.append(p)

# VARIANTE B: titulo distinto enfocado en keywords diferentes (waterproof, playa, 7h bateria, 24h liquidacion)
TITLE_B="Bocina Jbl Go 4 Sumergible Ip67 Bluetooth Bass 7h Seminueva"[:60]

DESC_B="""BOCINA JBL GO 4 SEMINUEVA - RESISTENCIA IP67 - PRECIO LIQUIDACION

═══ CARACTERISTICAS CLAVE ═══

Sonido JBL Pro Sound con graves potentes
Bluetooth 5.3 conexion estable
Bateria 7 horas para fiestas y dia de playa
Sumergible hasta 1 metro por 30 minutos - IP67
Puerto USB-C para carga rapida
Microfono manos libres para llamadas
Diseno compacto ideal para llevar

═══ IMPORTANTE - LEA ANTES DE COMPRAR ═══

COMPATIBILIDAD:
Esta unidad JBL Go 4 NO es compatible con la app JBL Portable.
Esta unidad NO es compatible con Auracast.
Funciona como altavoz Bluetooth estandar, empareja un dispositivo a la vez.
Al comprar usted acepta y entiende estas caracteristicas tecnicas.

CONDICION:
Producto SEMINUEVO / USADO, practicamente sin uso (abierto y probado una vez).
Caja original con sello JBL + serial SN + codigos UPC/EAN oficiales Harman.
Original JBL autentica, verificable en jbl.com.mx o linea 01-800-005-5252.

6 COLORES A ELEGIR:
Negro, Azul, Rojo, Rosa, Camuflaje, Aqua. Seleccione su favorito al agregar al carrito.

═══ POLITICAS CLARAS ═══

GARANTIA: 30 dias del vendedor por defectos comprobables con video. No cubre mal uso.
NO ACEPTAMOS: reclamos por no-compatibilidad con app/Auracast (declarado aqui), cambios de opinion, rayones esteticos normales de producto usado.
SI ACEPTAMOS: defectos de fabrica comprobables + devolucion con producto + empaque completos.

ENVIO GRATIS con Mercado Envios. Despacho 24h habiles.

El producto enviado coincide con lo descrito aqui. Cualquier reclamo contrario carece de sustento."""

body_B={
    "site_id":"MLM",
    "title":"Bocina Jbl Go 4 Sumergible Ip67 Bluetooth Bass 7h Seminueva","catalog_product_id":"MLM64277114",
    "category_id":cat_id,"currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"used","buying_mode":"buy_it_now",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":build_attrs_B(),
    "variations":variations,
}

print("\n=== POST B (A/B test) ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body_B,timeout=60)
print(f"status: {rp.status_code}")
if rp.status_code in (200,201):
    IID_B=rp.json()["id"]
    print(f"*** OK B: {IID_B} ***")
    m,s=update_desc(IID_B,DESC_B)
    print(f"  desc B: {m} -> {s}")
else:
    print(rp.text[:1500])
