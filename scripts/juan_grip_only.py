import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H).json()

# Pics Grip desde catalog
grip_pics_urls=[]
for cpid in ["MLM61785271"]:
    pr=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
    for p in (pr.get("pictures") or [])[:5]:
        if p.get("url"): grip_pics_urls.append(p.get("url"))
    for kid in (pr.get("children_ids") or [])[:3]:
        pk=requests.get(f"https://api.mercadolibre.com/products/{kid}",headers=H).json()
        for p in (pk.get("pictures") or [])[:3]:
            if p.get("url") and p.get("url") not in grip_pics_urls: grip_pics_urls.append(p.get("url"))
if not grip_pics_urls:
    ps=requests.get("https://api.mercadolibre.com/sites/MLM/search?q=bocina+JBL+Grip&limit=5",headers=H).json()
    for r_ in (ps.get("results") or [])[:3]:
        d=requests.get(f"https://api.mercadolibre.com/items/{r_.get('id')}?attributes=pictures,title",headers=H).json()
        if "Grip" in d.get("title",""):
            for p in (d.get("pictures") or [])[:5]:
                if p.get("url"): grip_pics_urls.append(p.get("url"))
            if grip_pics_urls: break
print(f"URLs pics: {len(grip_pics_urls)}")

def upload_url(url):
    try:
        img=requests.get(url,timeout=20).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

pics=[]
for u in grip_pics_urls[:5]:
    n=upload_url(u)
    if n: pics.append(n)
print(f"pics uploaded: {len(pics)}")

# Atributos SIN GTIN (para evitar formato inválido), con catalog_product_id
ga=[
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Grip"},
    {"id":"GTIN","value_name":"0050036459333"},
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
    {"id":"SPEAKERS_NUMBER","value_name":"1"},{"id":"PICKUPS_NUMBER","value_name":"1"},
    {"id":"SPEAKER_FORMAT","value_name":"1.0"},
]
seen={x["id"] for x in ga}
BAD={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","LINE","GRADING","HAS_MICROPHONE","IS_DUAL_VOICE_COIL","WITH_HANDSFREE_FUNCTION","HAS_LED_LIGHTS","IS_DUAL_VOICE_ASSISTANTS","HAS_FM_RADIO","HAS_SD_MEMORY_INPUT","HAS_APP_CONTROL","WITH_AUX","HAS_USB_INPUT"}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    vals=ca.get("values") or []; vt=ca.get("value_type")
    if vals: ga.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): ga.append({"id":aid,"value_name":"1"})
    else: ga.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

body={
    "site_id":"MLM",
    "title":"Bocina Jbl Grip Bluetooth Portatil Ip67 Original Negra",
    "catalog_product_id":"MLM62279317",
    "category_id":cat_id,"currency_id":"MXN",
    "price":699,"available_quantity":10,
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in pics],
    "attributes":ga,
}
print(f"\n=== POST Grip con catalog_product_id ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
d=rp.json()
if rp.status_code in (200,201):
    GID=d["id"]
    print(f"*** Grip OK {GID} ***")
    GDESC="""BOCINA JBL GRIP BLUETOOTH PORTATIL IP67 - ORIGINAL NEGRA

CARACTERISTICAS:
- Bluetooth 5.3 conexion estable
- Resistente al agua y polvo IP67
- Bateria 12 horas de autonomia
- Sonido JBL Pro Sound
- Manos libres con microfono
- Puerto USB-C de carga
- Entrada USB para alimentacion y datos
- Diseno ergonomico con agarre

IMPORTANTE - INFORMACION TECNICA DEL MODELO:
- Este modelo JBL Grip cuenta con entrada USB para alimentacion y transferencia.
- Este modelo NO es compatible con la app JBL Portable ni Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- Al comprar usted declara haber leido y aceptado estas caracteristicas tecnicas.

QUE INCLUYE: Bocina JBL Grip, cable USB-C, documentacion original.

GARANTIA: 30 dias por defectos de fabrica (requiere video del defecto + numero de orden).

POLITICA DE DEVOLUCIONES:
- No se aceptan reclamos por caracteristicas tecnicas ya informadas (compatibilidad app, entrada USB).
- No se aceptan devoluciones por cambio de opinion.
- Devoluciones por defecto requieren producto + empaque + accesorios completos.

ENVIO GRATIS - Despacho 24h habiles."""
    requests.put(f"https://api.mercadolibre.com/items/{GID}/description",headers=H,json={"plain_text":GDESC},timeout=30)
    print("desc OK")
    try:
        cfg=json.load(open("stock_config.json")) if os.path.exists("stock_config.json") else {}
    except: cfg={}
    cfg[GID]={"line":"Grip-Original","stock":10,"max_stock":10,"active":True,"price":699}
    json.dump(cfg,open("stock_config.json","w"),indent=2,ensure_ascii=False)
else:
    print(json.dumps(d,ensure_ascii=False)[:2000])
