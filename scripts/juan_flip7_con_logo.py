import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# 1) CERRAR publicaciones sin logo que ya existen en Juan
OLD=["MLM2886592129","MLM5236045906"]
print("=== CERRAR publicaciones sin logo ===")
for iid in OLD:
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=20)
    print(f"  close {iid}: {rp.status_code}")
    time.sleep(1)

# 2) Fotos ORIGINALES con logo JBL (subidas a ASVA, re-subir a Juan)
# Mapping visual (verificado antes):
# pic_00 Negro / pic_01 Negro caja / pic_02 Rojo / pic_03 Rojo caja / pic_04 Morado / pic_05 Rojo / pic_06 Azul caja / pic_07 Rojo / pic_08 Negro / pic_09 Morado / pic_10 Azul
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

print("\n=== UPLOAD PICS CON LOGO ===")
color_pics={}
for c,pids in PICS_SRC.items():
    out=[]
    for p in pids:
        n=reupload(p)
        if n: out.append(n)
    color_pics[c]=out
    print(f"  {c}: {len(out)}")

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs(color=None):
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
    if color: a.append({"id":"COLOR","value_name":color})
    seen={x["id"] for x in a}
    BAD={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","LINE","ALPHANUMERIC_MODEL","GTIN"}
    if not color: BAD.add("COLOR")
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

DESC_BASE="""BOCINA BLUETOOTH PORTATIL SUMERGIBLE IP67 - 35W RMS

AVISO LEGAL IMPORTANTE - LEA ANTES DE COMPRAR:
Este producto NO es original de la marca JBL, ni cuenta con garantia oficial del fabricante Harman Mexico. 
Es una replica de diseno similar al modelo comercial, fabricada por importador generico.
Las fotos muestran el modelo de referencia para su comparacion visual.
Al finalizar la compra usted declara conocer y aceptar expresamente que NO esta comprando un producto original de marca.

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo grado IP67
- Bateria recargable 16 horas de uso continuo
- Sonido potente 35W RMS con graves profundos
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida

QUE INCLUYE:
- 1 Bocina Bluetooth
- 1 Cable USB-C de carga
- Manual

GARANTIA (del vendedor unicamente):
- 30 dias contra defectos de fabrica comprobables con video
- NO aplica garantia oficial de JBL ni de Harman
- NO cubre danos por agua excesiva, caidas, mal uso

POLITICA DE DEVOLUCIONES:
- NO se aceptan reclamos por "no es original" - esta publicacion lo declara expresamente
- NO se aceptan reclamos por "no es compatible con app JBL" - este modelo no requiere app
- NO se aceptan devoluciones por cambio de opinion
- Devoluciones por defecto de fabrica comprobado requieren producto + empaque + accesorios completos

ENVIO GRATIS."""

# 3) Publicar Negro individual
print("\n=== POST Negro ===")
tb=f"Bocina Bluetooth Portatil Ip67 Bass 35w 16h Negra"[:60]
body={
    "site_id":"MLM","title":tb,"category_id":cat_id,"currency_id":"MXN",
    "price":399,"available_quantity":10,
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in color_pics["Negro"]],
    "attributes":build_attrs("Negro"),
}
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"  status: {rp.status_code}")
NEW_IDS={}
if rp.status_code in (200,201):
    iid=rp.json()["id"]; print(f"  OK Negro: {iid}")
    requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":DESC_BASE},timeout=20)
    NEW_IDS["Negro"]=iid
else: print(f"  err: {rp.text[:400]}")

# 4) Publicar unificada Azul+Rojo+Morado
print("\n=== POST Unificada 3 colores ===")
tb="Bocina Bluetooth Portatil Ip67 Bass 35w 16h Multicolor"[:60]
variations=[]
for c in ["Azul","Rojo","Morado"]:
    if color_pics.get(c):
        variations.append({
            "price":399,"available_quantity":10,
            "attribute_combinations":[{"id":"COLOR","value_name":c}],
            "picture_ids":color_pics[c],
        })
all_pics=[]
for c in ["Azul","Rojo","Morado"]:
    for p in color_pics.get(c,[]):
        if p not in all_pics: all_pics.append(p)

body={
    "site_id":"MLM","title":tb,"category_id":cat_id,"currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":build_attrs(),
    "variations":variations,
}
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"  status: {rp.status_code}")
if rp.status_code in (200,201):
    iid=rp.json()["id"]; print(f"  OK unificada: {iid}")
    requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":DESC_BASE},timeout=20)
    NEW_IDS["Unificada"]=iid
else: print(f"  err: {rp.text[:600]}")

print("\n=== RESUMEN NUEVAS ===")
for k,v in NEW_IDS.items(): print(f"  {k}: {v}")
print(f"\nCerradas: {OLD}")
