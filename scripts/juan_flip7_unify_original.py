import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# 1) Cerrar las 2 anteriores (Negro MLM2886592129 + unificada 3colores MLM5236045906)
OLD=["MLM2886592129","MLM5236045906"]
print("=== CERRAR viejas ===")
for iid in OLD:
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=20)
    print(f"  close {iid}: {rp.status_code}")
    time.sleep(1)

# 2) Re-subir pics originales CON logo JBL (las 11 del Flip 7 originales que estan en ASVA)
# Negro: pic_00, pic_01 caja, pic_08 / Azul: pic_10, pic_06 caja / Rojo: pic_02, pic_03 caja, pic_05, pic_07 / Morado: pic_04, pic_09
PICS_SRC={
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

print("\n=== UPLOAD PICS con logo JBL ===")
color_pics={}
for c,pids in PICS_SRC.items():
    out=[]
    for p in pids:
        n=reupload(p)
        if n: out.append(n)
    color_pics[c]=out
    print(f"  {c}: {len(out)} pics")

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs():
    a=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Flip 7"},
        {"id":"LINE","value_name":"Flip"},
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
        {"id":"HAS_APP_CONTROL","value_name":"No"},{"id":"HAS_USB_INPUT","value_name":"Si"},
        {"id":"WITH_AUX","value_name":"No"},{"id":"WITH_HANDSFREE_FUNCTION","value_name":"Si"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},{"id":"PICKUPS_NUMBER","value_name":"1"},
        {"id":"SPEAKER_FORMAT","value_name":"1.0"},
    ]
    seen={x["id"] for x in a}
    BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GTIN"}
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
    if color_pics.get(c):
        variations.append({
            "price":799,"available_quantity":10,
            "attribute_combinations":[{"id":"COLOR","value_name":c}],
            "picture_ids":color_pics[c],
        })
all_pics=[]
for c in ["Negro","Azul","Rojo","Morado"]:
    for p in color_pics.get(c,[]):
        if p not in all_pics: all_pics.append(p)

TITLE="Bocina Jbl Flip 7 Bluetooth Portatil Ip67 Bass Original Color"[:60]

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

print(f"\n=== POST UNIFICADA JBL Flip 7 4 colores $799 ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
d=rp.json()
if rp.status_code in (200,201):
    NEW=d["id"]
    print(f"*** OK {NEW} ***")
    DESC="""BOCINA JBL FLIP 7 BLUETOOTH PORTATIL IP67 - ORIGINAL - 4 COLORES

CARACTERISTICAS:
- Bluetooth 5.3 conexion estable hasta 15 metros
- Resistente al agua y polvo grado IP67 (alberca, playa, lluvia)
- Bateria recargable 16 horas de autonomia
- Sonido potente 35W RMS con graves profundos JBL Pro Sound
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida
- Entrada USB para alimentacion directa
- Correa integrada para llevar a cualquier lado

COLORES DISPONIBLES:
Negro, Azul, Rojo, Morado. Elija su color al comprar.

IMPORTANTE - INFORMACION TECNICA DEL MODELO:
- Este modelo JBL Flip 7 cuenta con entrada USB para alimentacion/datos.
- Este modelo NO es compatible con la aplicacion JBL Portable ni con Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- Al finalizar la compra usted declara haber leido y aceptado estas caracteristicas.

QUE INCLUYE:
- 1 Bocina JBL Flip 7
- 1 Cable USB-C de carga
- Documentacion original

GARANTIA:
- 30 dias por defectos de fabrica
- Requiere video del defecto + numero de orden para tramitar

POLITICA DE DEVOLUCIONES:
- No se aceptan reclamos por caracteristicas tecnicas ya informadas (compatibilidad app, entrada USB)
- No se aceptan devoluciones por cambio de opinion
- Devoluciones por defecto requieren producto + empaque + accesorios completos

ENVIO GRATIS - Despacho 24h habiles."""
    rd=requests.put(f"https://api.mercadolibre.com/items/{NEW}/description",headers=H,json={"plain_text":DESC},timeout=30)
    print(f"desc: {rd.status_code}")
    # stock config
    try:
        cfg=json.load(open("stock_config.json")) if os.path.exists("stock_config.json") else {}
    except: cfg={}
    cfg[NEW]={"line":"Flip7-Original","variations":{c:10 for c in ["Negro","Azul","Rojo","Morado"]},"active":True,"price":799}
    # Marcar old como cerrados
    for oiid in OLD:
        if oiid in cfg: cfg[oiid]["active"]=False; cfg[oiid]["closed"]=True
    json.dump(cfg,open("stock_config.json","w"),indent=2,ensure_ascii=False)
else:
    print(json.dumps(d,ensure_ascii=False)[:1500])

# ==========================================================================
# 3) PUBLICAR GRIP $699 ORIGINAL con disclaimer USB + no-app
# ==========================================================================
print("\n\n=== PUBLICAR GRIP $699 ===")
# Buscar el catalog_product_id del JBL Grip
s=requests.get("https://api.mercadolibre.com/products/search?site_id=MLM&q=JBL+Grip&limit=5",headers=H).json()
CPID_GRIP=None
for p in (s.get("results") or []):
    if "Grip" in p.get("name","") and "JBL" in p.get("name",""):
        CPID_GRIP=p.get("id")
        print(f"  catalog Grip: {CPID_GRIP} | {p.get('name','')[:60]}")
        break
if not CPID_GRIP:
    print("  no encontrado catalog Grip - publicar sin cpid")

# Buscar Grip existente en Juan para reusar pics si las hay
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
sj=requests.get(f"https://api.mercadolibre.com/users/{me['id']}/items/search?q=grip&status=active,closed&limit=20",headers=H).json()
grip_pics=[]
for iid in (sj.get("results") or [])[:5]:
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,pictures,catalog_product_id",headers=H).json()
    if "grip" in (d.get("title","") or "").lower():
        grip_pics=[p.get("id") for p in (d.get("pictures") or [])]
        print(f"  pics Grip reutilizadas de {iid}: {len(grip_pics)}")
        break

# Si no hay pics, intentar sacarlas del catalog
if not grip_pics and CPID_GRIP:
    cd=requests.get(f"https://api.mercadolibre.com/products/{CPID_GRIP}",headers=H).json()
    grip_pics=[p.get("id") for p in (cd.get("pictures") or [])][:5]
    print(f"  pics Grip desde catalog: {len(grip_pics)}")

# re-upload pics
def reup2(pid):
    try:
        img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

new_grip_pics=[]
for p in grip_pics[:5]:
    n=reup2(p)
    if n: new_grip_pics.append(n)
print(f"  grip pics en juan: {len(new_grip_pics)}")

if new_grip_pics:
    grip_attrs=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Grip"},
        {"id":"LINE","value_name":"Grip"},
        {"id":"COLOR","value_name":"Negro"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"MAX_BATTERY_AUTONOMY","value_name":"12 h"},
        {"id":"POWER_OUTPUT_RMS","value_name":"15 W"},
        {"id":"MAX_POWER","value_name":"15 W"},
        {"id":"MIN_FREQUENCY_RESPONSE","value_name":"85 Hz"},
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
        {"id":"HAS_APP_CONTROL","value_name":"No"},{"id":"HAS_USB_INPUT","value_name":"Si"},
        {"id":"WITH_AUX","value_name":"No"},{"id":"WITH_HANDSFREE_FUNCTION","value_name":"Si"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},{"id":"PICKUPS_NUMBER","value_name":"1"},
        {"id":"SPEAKER_FORMAT","value_name":"1.0"},
    ]
    seen={x["id"] for x in grip_attrs}
    BAD={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GTIN"}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD: continue
        vals=ca.get("values") or []; vt=ca.get("value_type")
        if vals: grip_attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): grip_attrs.append({"id":aid,"value_name":"1"})
        else: grip_attrs.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    
    gbody={
        "site_id":"MLM","title":"Bocina Jbl Grip Bluetooth Portatil Ip67 Original Negra","category_id":cat_id,"currency_id":"MXN",
        "price":699,"available_quantity":10,
        "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
        "pictures":[{"id":p} for p in new_grip_pics],
        "attributes":grip_attrs,
    }
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=gbody,timeout=60)
    print(f"  status: {rp.status_code}")
    if rp.status_code in (200,201):
        gid=rp.json()["id"]
        print(f"  *** OK Grip {gid} ***")
        GDESC="""BOCINA JBL GRIP BLUETOOTH PORTATIL IP67 - ORIGINAL

CARACTERISTICAS:
- Bluetooth 5.3 conexion estable
- Resistente al agua y polvo grado IP67
- Bateria recargable 12 horas de autonomia
- Sonido potente JBL Pro Sound
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida
- Entrada USB para alimentacion
- Diseno ergonomico con agarre

IMPORTANTE - INFORMACION TECNICA DEL MODELO:
- Este modelo JBL Grip cuenta con entrada USB para alimentacion y datos.
- Este modelo NO es compatible con la aplicacion JBL Portable ni con Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- Al finalizar la compra usted declara haber leido y aceptado estas caracteristicas tecnicas.

QUE INCLUYE:
- 1 Bocina JBL Grip
- 1 Cable USB-C de carga
- Documentacion original

GARANTIA:
- 30 dias por defectos de fabrica con video + numero de orden

POLITICA:
- No se aceptan reclamos por caracteristicas tecnicas ya informadas (compatibilidad app, entrada USB)
- No se aceptan devoluciones por cambio de opinion
- Devoluciones por defecto requieren producto + empaque + accesorios completos

ENVIO GRATIS - Despacho 24h habiles."""
        requests.put(f"https://api.mercadolibre.com/items/{gid}/description",headers=H,json={"plain_text":GDESC},timeout=30)
        cfg[gid]={"line":"Grip-Original","stock":10,"max_stock":10,"active":True,"price":699}
        json.dump(cfg,open("stock_config.json","w"),indent=2,ensure_ascii=False)
    else:
        print(f"  err: {rp.text[:500]}")
else:
    print("  no se pudo, falta pics del Grip")
