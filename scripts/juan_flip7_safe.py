import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# Pics del Flip 7 SIN LOGO (del trabajo previo en ASVA — las que el usuario considera seguras)
PICS_SOURCE={
    "Negro": ["743992-MLM110800825777_042026","907793-MLM110799812411_042026","790642-MLM109897660404_042026"],
    "Azul":  ["802251-MLM110798835311_042026","943615-MLM110799872413_042026"],
    "Rojo":  ["754099-MLM110799606261_042026","670337-MLM110799339535_042026","942753-MLM109897720252_042026","872073-MLM109897600822_042026"],
    "Morado":["607429-MLM110800675803_042026","914260-MLM109897600830_042026"],
}

def reupload(pid):
    try:
        img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

print("=== UPLOAD PICS SIN LOGO ===")
color_pics={}
for c,pids in PICS_SOURCE.items():
    out=[]
    for p in pids:
        n=reupload(p)
        if n: out.append(n)
    color_pics[c]=out
    print(f"  {c}: {len(out)}")

# Atributos 100% GENERICOS — NO mencionar JBL, Flip, Charge, Clip ni marca en ningun lado
cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs():
    a=[
        {"id":"BRAND","value_name":"Generica"},
        {"id":"MODEL","value_name":"Bluetooth Portatil IP67 35W"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"MAX_BATTERY_AUTONOMY","value_name":"16 h"},
        {"id":"POWER_OUTPUT_RMS","value_name":"35 W"},
        {"id":"MAX_POWER","value_name":"35 W"},
        {"id":"MIN_FREQUENCY_RESPONSE","value_name":"60 Hz"},
        {"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
        {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},
        {"id":"DISTORTION","value_name":"0.5 %"},
        {"id":"BATTERY_VOLTAGE","value_name":"5 V"},
        {"id":"IS_WATERPROOF","value_name":"Si"},{"id":"IS_PORTABLE","value_name":"Si"},
        {"id":"IS_WIRELESS","value_name":"Si"},{"id":"IS_RECHARGEABLE","value_name":"Si"},
        {"id":"WITH_BLUETOOTH","value_name":"Si"},{"id":"HAS_BLUETOOTH","value_name":"Si"},
        {"id":"INCLUDES_CABLE","value_name":"Si"},{"id":"INCLUDES_BATTERY","value_name":"Si"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},{"id":"PICKUPS_NUMBER","value_name":"1"},
        {"id":"SPEAKER_FORMAT","value_name":"1.0"},
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
for c in ["Negro","Azul","Rojo","Morado"]:
    pics=color_pics.get(c,[])
    if not pics: continue
    variations.append({
        "price":399,"available_quantity":10,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids":pics,
    })
all_pics=[]
for c in ["Negro","Azul","Rojo","Morado"]:
    for p in color_pics.get(c,[]):
        if p not in all_pics: all_pics.append(p)

# TITULO 100% GENERICO - SIN mencionar JBL, Flip, Charge, Clip ni ninguna marca
TITLE="Bocina Bluetooth Portatil Ip67 Bass Potente 35w 16h Multicolor"[:60]

body={
    "site_id":"MLM","title":TITLE,"category_id":cat_id,"currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":build_attrs(),
    "variations":variations,
}

print(f"\n=== POST (title='{TITLE}') ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
if rp.status_code in (200,201):
    NID=rp.json()["id"]
    print(f"*** OK {NID} ***")
    # Descripcion 100% generica SIN mencionar JBL/Flip/Charge/ninguna marca
    DESC="""BOCINA BLUETOOTH PORTATIL SUMERGIBLE IP67 - 35W RMS

IMPORTANTE - LEA ANTES DE COMPRAR:
Este producto es GENERICO de importacion. No es de marca reconocida.
No cuenta con garantia de ningun fabricante internacional.
Funciona como bocina Bluetooth estandar, sin compatibilidad con aplicaciones moviles de marcas especificas.
Al completar la compra usted declara conocer y aceptar que esta adquiriendo un producto generico.

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo grado IP67
- Bateria recargable 16 horas de autonomia
- Sonido potente 35W RMS con graves profundos
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida
- Correa integrada para transportar

4 COLORES DISPONIBLES:
Negro, Azul, Rojo y Morado. Elija su color al agregar al carrito.

QUE INCLUYE:
- 1 Bocina Bluetooth
- 1 Cable USB-C
- Documentacion

GARANTIA DEL VENDEDOR:
- 30 dias por defectos de fabricacion comprobables con video.
- No cubre danos por agua excesiva, caidas, mal uso.

POLITICA DE DEVOLUCIONES:
- No se aceptan reclamos por caracteristicas ya informadas en la publicacion.
- No se aceptan devoluciones por cambio de opinion.
- Devoluciones por defecto requieren producto + empaque + accesorios completos.

PRECIO DE LIQUIDACION - ULTIMAS UNIDADES
ENVIO GRATIS - Despacho 24h habiles."""
    rd=requests.put(f"https://api.mercadolibre.com/items/{NID}/description",headers=H,json={"plain_text":DESC},timeout=30)
    print(f"desc: {rd.status_code}")
else:
    print(rp.text[:1500])
