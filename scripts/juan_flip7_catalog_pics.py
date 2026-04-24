import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# 1) Cerrar la publicacion anterior con pics sin logo
OLD_WRONG="MLM2887821733"
print(f"=== CLOSE {OLD_WRONG} ===")
rp=requests.put(f"https://api.mercadolibre.com/items/{OLD_WRONG}",headers=H,json={"status":"closed"},timeout=20)
print(f"  close: {rp.status_code}")

# 2) Explorar varios catalog products de JBL Flip 7 para encontrar uno con pictures
catalog_candidates=["MLM64166697","MLM63648344","MLM62944208","MLM47584787"]
pics_by_color={"Negro":[],"Azul":[],"Rojo":[],"Morado":[]}

for cpid in catalog_candidates:
    try:
        p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
        color=None
        for a in (p.get("attributes") or []):
            if a.get("id")=="COLOR": color=a.get("value_name"); break
        pics=[x.get("url") for x in (p.get("pictures") or []) if x.get("url")]
        print(f"  {cpid} | {p.get('name','')[:60]} | COLOR={color} | pics={len(pics)}")
        if color in pics_by_color and pics: 
            pics_by_color[color]=pics
        # tambien children
        for kid in (p.get("children_ids") or []):
            pk=requests.get(f"https://api.mercadolibre.com/products/{kid}",headers=H,timeout=15).json()
            ck=None
            for a in (pk.get("attributes") or []):
                if a.get("id")=="COLOR": ck=a.get("value_name"); break
            kpics=[x.get("url") for x in (pk.get("pictures") or []) if x.get("url")]
            print(f"    child {kid} | {pk.get('name','')[:50]} | COLOR={ck} | pics={len(kpics)}")
            if ck in pics_by_color and kpics and not pics_by_color[ck]:
                pics_by_color[ck]=kpics
    except Exception as e:
        print(f"  err {cpid}: {e}")

# 3) Fallback: buscar en items LIVE con catalog_listing=True para cada color
print("\n=== FALLBACK: items catalog live ===")
for color in pics_by_color:
    if pics_by_color[color]: continue
    q=f"JBL Flip 7 {color}"
    s=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={q}&category=MLM59800&limit=20&condition=new",headers=H).json()
    for r_ in (s.get("results") or [])[:20]:
        if "Flip 7" not in r_.get("title","") or "JBL" not in r_.get("title",""): continue
        iid=r_.get("id")
        d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=pictures,attributes,title",headers=H).json()
        item_color=None
        for a in (d.get("attributes") or []):
            if a.get("id")=="COLOR": item_color=a.get("value_name"); break
        if item_color==color:
            urls=[x.get("url") for x in (d.get("pictures") or []) if x.get("url")][:5]
            if urls:
                pics_by_color[color]=urls
                print(f"  {color} <- item {iid} ({len(urls)} pics)")
                break

for c,u in pics_by_color.items():
    print(f"  {c}: {len(u)} URLs")

# 4) Subir pics a Juan
def upload(url):
    try:
        img=requests.get(url,timeout=20).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

color_pic_ids={}
for color,urls in pics_by_color.items():
    ids=[]
    for u in urls[:5]:
        pid=upload(u)
        if pid: ids.append(pid)
    color_pic_ids[color]=ids
    print(f"  upload {color}: {len(ids)}")

# 5) Crear publicacion unificada JBL Flip 7 ORIGINAL con pics del catalog
if any(color_pic_ids.values()):
    cat_id="MLM59800"
    cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H).json()
    GTIN_PER_COLOR={"Negro":"1200130019272","Azul":"1200130019289","Rojo":"1200130019296","Morado":"1200130019319"}
    
    def build_attrs():
        a=[
            {"id":"BRAND","value_name":"JBL"},{"id":"MODEL","value_name":"Flip 7"},
            {"id":"ITEM_CONDITION","value_name":"Nuevo"},
            {"id":"MAX_BATTERY_AUTONOMY","value_name":"16 h"},
            {"id":"POWER_OUTPUT_RMS","value_name":"35 W"},{"id":"MAX_POWER","value_name":"35 W"},
            {"id":"MIN_FREQUENCY_RESPONSE","value_name":"60 Hz"},{"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
            {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},{"id":"DISTORTION","value_name":"0.5 %"},
            {"id":"BATTERY_VOLTAGE","value_name":"5 V"},{"id":"IS_WATERPROOF","value_name":"Si"},
            {"id":"IS_PORTABLE","value_name":"Si"},{"id":"IS_WIRELESS","value_name":"Si"},
            {"id":"IS_RECHARGEABLE","value_name":"Si"},{"id":"WITH_BLUETOOTH","value_name":"Si"},
            {"id":"HAS_BLUETOOTH","value_name":"Si"},{"id":"INCLUDES_CABLE","value_name":"Si"},
            {"id":"INCLUDES_BATTERY","value_name":"Si"},
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
        pics=color_pic_ids.get(c,[])
        if not pics: continue
        variations.append({
            "price":799,"available_quantity":10,
            "attribute_combinations":[{"id":"COLOR","value_name":c}],
            "attributes":[{"id":"GTIN","value_name":GTIN_PER_COLOR[c]}],
            "picture_ids":pics,
        })
    all_pics=[]
    for c in ["Negro","Azul","Rojo","Morado"]:
        for p in color_pic_ids.get(c,[]):
            if p not in all_pics: all_pics.append(p)
    
    body={
        "site_id":"MLM","title":"Bocina Jbl Flip 7 Bluetooth Portatil Ip67 Original Nueva",
        "category_id":cat_id,"currency_id":"MXN",
        "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
        "pictures":[{"id":p} for p in all_pics],
        "attributes":build_attrs(),
        "variations":variations,
    }
    print(f"\n=== POST JBL Flip 7 ORIGINAL catalog pics ===")
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
    print(f"status: {rp.status_code}")
    if rp.status_code in (200,201):
        NID=rp.json()["id"]
        print(f"*** ORIGINAL OK {NID} ***")
        DESC="""BOCINA JBL FLIP 7 BLUETOOTH PORTATIL IP67 - ORIGINAL - 4 COLORES

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo IP67
- Bateria 16 horas de autonomia
- Sonido potente 35W RMS JBL Pro Sound
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida
- Entrada USB para alimentacion y datos
- Correa integrada

COLORES: Negro, Azul, Rojo, Morado.

IMPORTANTE - INFORMACION TECNICA:
- Este modelo JBL Flip 7 cuenta con entrada USB para alimentacion y datos.
- Este modelo NO es compatible con la app JBL Portable ni Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- Al comprar usted declara haber leido y aceptado estas caracteristicas tecnicas.

QUE INCLUYE: Bocina JBL Flip 7, cable USB-C, documentacion original.

GARANTIA: 30 dias por defecto de fabrica (video + orden).

POLITICA: no se aceptan reclamos por caracteristicas informadas (compatibilidad app, entrada USB) ni devoluciones por cambio de opinion.

ENVIO GRATIS."""
        requests.put(f"https://api.mercadolibre.com/items/{NID}/description",headers=H,json={"plain_text":DESC},timeout=30)
        print("desc OK")
    else:
        print(rp.text[:1500])
else:
    print("!!! SIN pics disponibles")
