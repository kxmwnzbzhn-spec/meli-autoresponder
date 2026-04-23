import os,requests,json,time,glob
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"ASVA user: {me.get('nickname')} ({me.get('id')})")

PICS_DIR="pics_go4_genericas"
# Subir fotos por color
def upload(path):
    with open(path,"rb") as f:
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":(os.path.basename(path),f,"image/jpeg")},timeout=60)
    if rp.status_code in (200,201):
        return rp.json()["id"]
    print(f"  upload fail {path}: {rp.status_code} {rp.text[:200]}")
    return None

COLOR_MAP={
    "Rosa":["rosa_1","rosa_2","rosa_3"],
    "Aqua":["aqua_1","aqua_2","aqua_3"],
    "Azul":["azul_1","azul_2","azul_3"],
    "Negro":["negro_1","negro_2","negro_3"],
    "Rojo":["rojo_1","rojo_2"],
    "Camuflaje":["camu_1","camu_2","camu_3"],
}
color_pics={}
for color,files in COLOR_MAP.items():
    ids=[]
    for f in files:
        pid=upload(f"{PICS_DIR}/{f}.jpg")
        if pid: ids.append(pid)
    color_pics[color]=ids
    print(f"  {color}: {len(ids)} pics uploaded -> {ids}")

all_pics=[]
for ids in color_pics.values():
    for p in ids:
        if p not in all_pics: all_pics.append(p)
print(f"\nTotal pics unicas: {len(all_pics)}")

# Category + atributos
cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs():
    a=[
        {"id":"BRAND","value_name":"Generica"},
        {"id":"MODEL","value_name":"BT Go Compact"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"MAX_BATTERY_AUTONOMY","value_name":"7 h"},
        {"id":"POWER_OUTPUT_RMS","value_name":"4.2 W"},
        {"id":"MAX_POWER","value_name":"4.2 W"},
        {"id":"MIN_FREQUENCY_RESPONSE","value_name":"95 Hz"},
        {"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
        {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},
        {"id":"DISTORTION","value_name":"0.5 %"},
        {"id":"BATTERY_VOLTAGE","value_name":"5 V"},
        {"id":"IS_WATERPROOF","value_name":"Si"},
        {"id":"IS_PORTABLE","value_name":"Si"},
        {"id":"IS_WIRELESS","value_name":"Si"},
        {"id":"IS_RECHARGEABLE","value_name":"Si"},
        {"id":"WITH_BLUETOOTH","value_name":"Si"},
        {"id":"HAS_BLUETOOTH","value_name":"Si"},
        {"id":"INCLUDES_CABLE","value_name":"Si"},
        {"id":"INCLUDES_BATTERY","value_name":"Si"},
        {"id":"HAS_MICROPHONE","value_name":"No"},
        {"id":"IS_DUAL_VOICE_COIL","value_name":"No"},
        {"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},
        {"id":"HAS_FM_RADIO","value_name":"No"},
        {"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},
        {"id":"HAS_LED_LIGHTS","value_name":"No"},
        {"id":"HAS_APP_CONTROL","value_name":"No"},
        {"id":"HAS_USB_INPUT","value_name":"No"},
        {"id":"WITH_AUX","value_name":"No"},
        {"id":"WITH_HANDSFREE_FUNCTION","value_name":"No"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},
        {"id":"PICKUPS_NUMBER","value_name":"1"},
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
attrs=build_attrs()

variations=[]
STK=10
for color,ids in color_pics.items():
    if not ids: continue
    variations.append({
        "price":199,"available_quantity":STK,
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
        "picture_ids":ids,
    })

TITLE="Bocina Bluetooth Portatil Compacta Ip67 Bass Manos Libres"[:60]

body={
    "site_id":"MLM","title":TITLE,"category_id":cat_id,"currency_id":"MXN",
    "price":199,"available_quantity":STK*len(variations),
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":attrs,
    "variations":variations,
}

print(f"\n=== POST item (6 variantes x{STK}u $199) ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
d=rp.json()
if rp.status_code not in (200,201):
    print(json.dumps(d,ensure_ascii=False,indent=2)[:2500])
    # Si falla por family_name, reintentar
    if "family_name" in rp.text:
        print("\n=== RETRY con family_name ===")
        body2=dict(body); body2.pop("title",None); body2["family_name"]=TITLE
        rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body2,timeout=60)
        print(f"status: {rp.status_code}")
        d=rp.json()
        if rp.status_code not in (200,201): print(json.dumps(d,ensure_ascii=False,indent=2)[:2500])

if rp.status_code in (200,201):
    new_id=d["id"]
    print(f"\n*** OK {new_id} ***")
    # Descripcion blindada
    DESC="""BOCINA BLUETOOTH PORTATIL COMPACTA SUMERGIBLE IP67

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 10 metros
- Resistente al agua y polvo grado IP67
- Bateria recargable 7 horas de autonomia
- Sonido claro con graves presentes
- Puerto USB-C para carga
- Ultra compacta para llevar a cualquier lugar
- Correa integrada para colgar o cargar
- Disponible en 6 colores

QUE INCLUYE:
- 1 Bocina Bluetooth
- 1 Cable USB-C de carga
- Manual de usuario

IMPORTANTE:
- Producto GENERICO de importacion. No es de marca reconocida.
- No cuenta con garantia de fabricante internacional.
- Funciona como bocina Bluetooth estandar. No requiere aplicacion movil.
- Garantia del vendedor de 30 dias por defectos de fabricacion.

POLITICA DE DEVOLUCIONES:
- Se aceptan devoluciones por defecto de fabrica comprobado dentro de los primeros 30 dias.
- NO se aceptan devoluciones por cambio de opinion.
- NO se aceptan reclamos por caracteristicas tecnicas ya informadas en esta publicacion.
- Toda devolucion requiere producto + empaque + accesorios completos.

ENVIO GRATIS - Despacho 24h habiles.

Al finalizar la compra acepta las condiciones de producto generico."""
    rd=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":DESC},timeout=30)
    print(f"desc: {rd.status_code}")
    # Guardar en stock config
    try:
        cfg=json.load(open("stock_config_asva.json")) if os.path.exists("stock_config_asva.json") else {}
    except: cfg={}
    cfg[new_id]={"title":TITLE,"variations":{c:STK for c in color_pics if color_pics[c]},"active":True}
    json.dump(cfg,open("stock_config_asva.json","w"),indent=2,ensure_ascii=False)
    print("stock config actualizado")
