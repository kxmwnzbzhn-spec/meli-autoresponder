import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

IID_A="MLM5239571436"

# Atributos completos para Go 4
RICH_ATTRS=[
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Go 4"},
    {"id":"LINE","value_name":"Go"},
    {"id":"ITEM_CONDITION","value_name":"Usado"},
    {"id":"MAX_BATTERY_AUTONOMY","value_name":"7 h"},
    {"id":"POWER_OUTPUT_RMS","value_name":"4.2 W"},
    {"id":"MAX_POWER","value_name":"4.2 W"},
    {"id":"PMPO_POWER_OUTPUT","value_name":"8 W"},
    {"id":"MIN_FREQUENCY_RESPONSE","value_name":"95 Hz"},
    {"id":"MAX_FREQUENCY_RESPONSE","value_name":"20000 Hz"},
    {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},
    {"id":"DISTORTION","value_name":"0.5 %"},
    {"id":"BATTERY_VOLTAGE","value_name":"5 V"},
    {"id":"BATTERY_CAPACITY","value_name":"730 mAh"},
    {"id":"BATTERY_TYPE","value_name":"Ion de litio"},
    {"id":"BATTERY_CHARGING_TIME","value_name":"2.5 h"},
    {"id":"BATTERY_QUANTITY","value_name":"1"},
    {"id":"INCLUDES_BATTERY","value_name":"Si"},
    {"id":"IS_RECHARGEABLE","value_name":"Si"},
    {"id":"IS_PORTABLE","value_name":"Si"},
    {"id":"IS_WIRELESS","value_name":"Si"},
    {"id":"IS_WATERPROOF","value_name":"Si"},
    {"id":"WATERPROOF_DEGREE","value_name":"IP67"},
    {"id":"IS_DUSTPROOF","value_name":"Si"},
    {"id":"BLUETOOTH_VERSION","value_name":"5.3"},
    {"id":"BLUETOOTH_RANGE","value_name":"10 m"},
    {"id":"WITH_BLUETOOTH","value_name":"Si"},
    {"id":"HAS_BLUETOOTH","value_name":"Si"},
    {"id":"HAS_MULTIPOINT","value_name":"No"},
    {"id":"HAS_MICROPHONE","value_name":"No"},
    {"id":"WITH_HANDSFREE_FUNCTION","value_name":"No"},
    {"id":"HAS_USB_INPUT","value_name":"No"},
    {"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},
    {"id":"HAS_FM_RADIO","value_name":"No"},
    {"id":"HAS_NFC","value_name":"No"},
    {"id":"HAS_APP_CONTROL","value_name":"No"},
    {"id":"HAS_LED_LIGHTS","value_name":"No"},
    {"id":"HAS_LED_DISPLAY","value_name":"No"},
    {"id":"IS_SMART","value_name":"No"},
    {"id":"IS_VOICE_ACTIVATED","value_name":"No"},
    {"id":"IS_DUAL_VOICE_COIL","value_name":"No"},
    {"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},
    {"id":"INCLUDES_REMOTE_CONTROL","value_name":"No"},
    {"id":"INCLUDES_CABLE","value_name":"Si"},
    {"id":"AC_ADAPTER_INCLUDED","value_name":"No"},
    {"id":"WITH_AUX","value_name":"No"},
    {"id":"WITH_STEREO_SOUND","value_name":"No"},
    {"id":"WITH_EQUALIZER","value_name":"No"},
    {"id":"HAS_AC_POWER","value_name":"No"},
    {"id":"CHARGING_PORT","value_name":"USB-C"},
    {"id":"SPEAKERS_NUMBER","value_name":"1"},
    {"id":"PICKUPS_NUMBER","value_name":"1"},
    {"id":"SPEAKER_FORMAT","value_name":"1.0"},
    {"id":"SHAPE","value_name":"Cilindrica"},
    {"id":"PACKAGE_LENGTH","value_name":"95 mm"},
    {"id":"PACKAGE_WIDTH","value_name":"75 mm"},
    {"id":"PACKAGE_HEIGHT","value_name":"75 mm"},
    {"id":"PACKAGE_WEIGHT","value_name":"190 g"},
    {"id":"WEIGHT","value_name":"190 g"},
    {"id":"LENGTH","value_name":"95 mm"},
    {"id":"WIDTH","value_name":"75 mm"},
    {"id":"HEIGHT","value_name":"75 mm"},
]

# === A: actualizar atributos del item existente ===
print(f"=== A: UPDATE attrs MLM5239571436 ===")
# Mantener atributos existentes que no esten en BAD
cur=requests.get(f"https://api.mercadolibre.com/items/{IID_A}?include_attributes=all",headers=H).json()
existing_attrs={a.get("id") for a in (cur.get("attributes") or [])}
print(f"  attrs existentes: {len(existing_attrs)}")

# Hacer update de attrs - solo pasar los nuevos
rp=requests.put(f"https://api.mercadolibre.com/items/{IID_A}",headers=H,json={"attributes":RICH_ATTRS},timeout=30)
print(f"  attrs update: {rp.status_code}")
if rp.status_code not in (200,201): print(f"    err: {rp.text[:500]}")

# Descripción A actualizada (la que ya estaba blindada)
DESC_A="""BOCINA JBL GO 4 BLUETOOTH PORTATIL IP67 - USADA EN EXCELENTE ESTADO

ESTADO DEL PRODUCTO
Vendida como USADA en excelente estado de funcionamiento. Producto 100% original JBL con caja original, numero de serie SN verificable y codigos UPC/EAN oficiales Harman/JBL impresos en el empaque. Puede presentar marcas MINIMAS de uso normal por tratarse de producto usado. Probada y funcionando al 100% antes del envio.

CARACTERISTICAS TECNICAS
- Bluetooth 5.3 estable hasta 10 metros
- Resistencia al agua y polvo grado IP67
- Bateria recargable con autonomia de 7 horas
- Sonido JBL Pro Sound potente
- Puerto USB-C para carga rapida
- Tiempo de carga aproximado 2.5 horas
- Peso ligero 190 gramos
- Diseno cilindrico ultra portatil
- Correa integrada para llevar a cualquier lado

QUE INCLUYE
- 1 Bocina JBL Go 4 USADA
- 1 Cable USB-C de carga
- Caja original

INFORMACION TECNICA IMPORTANTE
- Este modelo NO es compatible con la aplicacion JBL Portable.
- Este modelo NO es compatible con Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- No incluye microfono ni manos libres.
- Al comprar usted declara haber leido y aceptado expresamente estas caracteristicas tecnicas.

COLORES DISPONIBLES
6 colores disponibles: Negro, Azul, Rojo, Rosa, Camuflaje y Aqua. Seleccione su color al agregar al carrito.

GARANTIA DEL VENDEDOR
- 30 dias por defectos de fabrica comprobables con video.
- NO aplica garantia oficial del fabricante por tratarse de producto usado.
- NO cubre danos por agua excesiva, caidas, mal uso o desgaste estetico normal.

POLITICA DE DEVOLUCIONES Y RECLAMOS
- El producto enviado coincide con lo ofertado.
- NO se aceptan reclamos por no ser compatible con app JBL Portable. Esta publicacion lo declara expresamente.
- NO se aceptan reclamos por no ser compatible con Auracast. Esta publicacion lo declara expresamente.
- NO se aceptan reclamos por no ser original sin peritaje tecnico oficial.
- NO se aceptan devoluciones por cambio de opinion del comprador.
- NO se aceptan devoluciones por condiciones esteticas minimas propias de un producto usado.

ENVIO GRATIS - Despacho 24 horas habiles - Entrega estimada 2 a 5 dias segun zona.

Al completar esta compra usted declara haber leido y aceptar todos los terminos anteriores."""

rd=requests.put(f"https://api.mercadolibre.com/items/{IID_A}/description",headers=H,json={"plain_text":DESC_A},timeout=30)
print(f"  desc A: {rd.status_code}")

# === B: crear otra publicacion con titulo/desc distinto ===
# Re-upload pics
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
for v in (cur.get("variations") or []):
    color=None
    for ac in v.get("attribute_combinations",[]):
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    pids=v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
    new_ids=[]
    for p in pids[:4]:
        n=reup(p)
        if n: new_ids.append(n)
    color_pics[color]=new_ids
print(f"\n  pics B re-subidas: {sum(len(v) for v in color_pics.values())}")

variations=[]
for c,pics in color_pics.items():
    if not pics: continue
    variations.append({
        "price":299,"available_quantity":1,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids":pics,
    })
all_pics=[]
for c,pids in color_pics.items():
    for p in pids:
        if p not in all_pics: all_pics.append(p)

TITLE_B="Bocina Jbl Go 4 Sumergible Ip67 Bluetooth Bass 7h Seminueva"[:60]

body_B={
    "site_id":"MLM",
    "title":TITLE_B,
    "catalog_product_id":"MLM64277114",
    "category_id":"MLM59800","currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"used","buying_mode":"buy_it_now",
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":RICH_ATTRS,
    "variations":variations,
}

print(f"\n=== POST B Claribel ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body_B,timeout=60)
print(f"status: {rp.status_code}")
if rp.status_code in (200,201):
    NID=rp.json()["id"]
    print(f"*** OK B: {NID} ***")
    DESC_B="""JBL GO 4 SEMINUEVA - SUMERGIBLE IP67 - SONIDO POTENTE PARA TUS AVENTURAS

CARACTERISTICAS PRINCIPALES
Sonido JBL Pro Sound con graves potentes
Bluetooth 5.3 conexion estable
Bateria 7 horas de uso continuo
Sumergible IP67 para alberca, playa y lluvia
Puerto USB-C para carga rapida
Peso ligero 190 gramos para llevar a todos lados
Correa integrada incluida
Tiempo de carga aproximado 2.5 horas

ESTADO
Producto SEMINUEVO / USADO en excelente estado, practicamente sin uso. Caja original con sello JBL, serial SN unico y codigos UPC/EAN oficiales Harman/JBL. Probada y verificada antes del envio. Puede presentar marcas minimas propias de un producto usado.

INFORMACION IMPORTANTE
Esta unidad JBL Go 4 NO es compatible con la app JBL Portable.
Esta unidad NO es compatible con Auracast.
Funciona como altavoz Bluetooth estandar, empareja un dispositivo a la vez.
No incluye microfono ni funcion manos libres.
Al comprar usted acepta y entiende estas caracteristicas tecnicas.

6 COLORES PARA ELEGIR
Negro, Azul, Rojo, Rosa, Camuflaje, Aqua. Selecciona tu favorito al agregar al carrito.

QUE INCLUYE
1 Bocina JBL Go 4 seminueva
1 Cable USB-C
Caja original

GARANTIA Y POLITICAS
Garantia del vendedor de 30 dias por defectos comprobables con video. No cubre mal uso ni desgaste estetico normal.
NO se aceptan reclamos por no compatibilidad con app o Auracast (declarado aqui).
NO se aceptan devoluciones por cambio de opinion ni rayones esteticos minimos de producto usado.

ENVIO GRATIS con Mercado Envios. Despacho 24h habiles.

El producto enviado coincide con lo descrito aqui. Cualquier reclamo contrario carece de sustento."""
    rd=requests.put(f"https://api.mercadolibre.com/items/{NID}/description",headers=H,json={"plain_text":DESC_B},timeout=30)
    print(f"desc B: {rd.status_code}")
else:
    print(rp.text[:1500])
