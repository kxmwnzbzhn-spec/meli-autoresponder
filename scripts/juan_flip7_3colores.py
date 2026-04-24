import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# Pics de Flip 7 en ASVA -> re-subir a Juan
PICS_SOURCE={
    "Azul":["802251-MLM110798835311_042026","943615-MLM110799872413_042026"],  # pic_10, pic_06
    "Rojo":["754099-MLM110799606261_042026","670337-MLM110799339535_042026","942753-MLM109897720252_042026","872073-MLM109897600822_042026"],  # 2,3,5,7
    "Morado":["607429-MLM110800675803_042026","914260-MLM109897600830_042026"],  # 4, 9
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

color_pics={}
for c,pids in PICS_SOURCE.items():
    out=[]
    for p in pids:
        n=reupload(p)
        if n: out.append(n)
    color_pics[c]=out
    print(f"{c}: {len(out)} pics")

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs():
    a=[
        {"id":"BRAND","value_name":"Generica"},
        {"id":"MODEL","value_name":"BT Flip Bass 40W"},
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
        {"id":"HAS_MICROPHONE","value_name":"Si"},{"id":"IS_DUAL_VOICE_COIL","value_name":"No"},
        {"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},{"id":"HAS_FM_RADIO","value_name":"No"},
        {"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},{"id":"HAS_LED_LIGHTS","value_name":"No"},
        {"id":"HAS_APP_CONTROL","value_name":"No"},{"id":"HAS_USB_INPUT","value_name":"No"},
        {"id":"WITH_AUX","value_name":"No"},{"id":"WITH_HANDSFREE_FUNCTION","value_name":"Si"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},{"id":"PICKUPS_NUMBER","value_name":"1"},
        {"id":"SPEAKER_FORMAT","value_name":"1.0"},
    ]
    seen={x["id"] for x in a}
    BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","LINE","ALPHANUMERIC_MODEL","GTIN"}
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

DESC="""BOCINA BLUETOOTH PORTATIL SUMERGIBLE IP67 - DISPONIBLE EN 3 COLORES

IMPORTANTE - LEA ANTES DE COMPRAR:
Este producto NO es original de la marca JBL ni de ninguna otra marca reconocida.
Es un producto generico de importacion, similar en diseno y funciones a modelos comerciales.
No cuenta con garantia de fabricante internacional.
Funciona como bocina Bluetooth estandar, no requiere aplicacion movil.
Al finalizar la compra usted declara conocer y aceptar que NO esta comprando un producto de marca original.

COLORES DISPONIBLES:
Azul, Rojo, Morado. Elija su color al agregar al carrito.

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo grado IP67
- Bateria recargable 16 horas de uso continuo
- Sonido potente 35W RMS con graves profundos
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida
- Ligera y portatil para uso exterior

QUE INCLUYE:
- 1 Bocina Bluetooth
- 1 Cable USB-C de carga
- Manual de usuario

GARANTIA (del vendedor):
- 30 dias contra defectos de fabricacion comprobables con video
- NO cubre: danos por agua en exceso, caidas, mal uso
- No aplica garantia oficial de ninguna marca

POLITICA DE DEVOLUCIONES:
- Se aceptan por defecto de fabrica comprobado en 30 dias
- NO se aceptan reclamos por "no es original" - esta publicacion lo declara expresamente
- NO se aceptan reclamos por caracteristicas tecnicas ya informadas
- NO se aceptan devoluciones por cambio de opinion

ENVIO GRATIS - Despacho 24h habiles."""

TITLE="Bocina Bluetooth Portatil Ip67 Bass 35w 16h Multicolor"[:60]

# === INTENTO UNIFICADO: title + variations (sin family_name) ===
variations=[]
for c,pics in color_pics.items():
    if not pics: continue
    variations.append({
        "price":399,"available_quantity":10,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids":pics,
    })
all_pics=[]
for pids in color_pics.values():
    for p in pids:
        if p not in all_pics: all_pics.append(p)

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

print("=== INTENTO UNIFICADA (title+variations) ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
d=rp.json()
if rp.status_code in (200,201):
    new_id=d["id"]
    print(f"OK unificada: {new_id}")
    rd=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":DESC},timeout=30)
    print(f"desc: {rd.status_code}")
else:
    print(json.dumps(d,ensure_ascii=False)[:1500])
    # FALLBACK: 3 separadas
    print("\n=== FALLBACK: 3 SEPARADAS ===")
    RESULTS={}
    for color,pics in color_pics.items():
        if not pics: continue
        t=f"Bocina Bluetooth Portatil Ip67 Bass 35w 16h {color} Generica"[:60]
        attrs=build_attrs(); attrs.append({"id":"COLOR","value_name":color})
        b={
            "site_id":"MLM","title":t,"category_id":cat_id,"currency_id":"MXN",
            "price":399,"available_quantity":10,
            "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
            "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
            "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
            "pictures":[{"id":p} for p in pics],
            "attributes":attrs,
        }
        rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=b,timeout=45)
        if rp.status_code in (200,201):
            iid=rp.json()["id"]
            print(f"  {color} OK: {iid}")
            desc_color=DESC.replace("DISPONIBLE EN 3 COLORES",f"COLOR {color.upper()}").replace("Azul, Rojo, Morado. Elija su color al agregar al carrito.",f"Color: {color}")
            requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":desc_color},timeout=20)
            RESULTS[color]=iid
        else:
            print(f"  {color} FAIL: {rp.status_code} {rp.text[:300]}")
        time.sleep(2)
    print(f"\n=== RESUMEN ===")
    for c,iid in RESULTS.items(): print(f"  {c}: {iid}")
