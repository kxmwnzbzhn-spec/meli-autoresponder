import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
print(f"Cuenta: {me.get('nickname')} id={me.get('id')}")

# Buscar catalog Flip 7 Negro
def search_cpid():
    r=requests.get("https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q=JBL+Flip+7+Negro",headers=H,timeout=15).json()
    for it in r.get("results",[])[:10]:
        nm=(it.get("name") or "").lower()
        if any(b in nm for b in ["funda","case","tester","cover"]): continue
        if "flip 7" in nm and ("negro" in nm or "negra" in nm or "black" in nm):
            return it.get("id"), it.get("name")
    return None, None

cpid, cname = search_cpid()
print(f"Catalog: {cpid} - {cname}")

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

cat_id="MLM59800"; pics=[]
if cpid:
    prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
    cat_id=prod.get("category_details",{}).get("id") or "MLM59800"
    pics=[p["url"] for p in (prod.get("pictures") or []) if p.get("url")]

cat_attrs=get_cat_attrs(cat_id)

def num_val(aid):
    NS={"MAX_BATTERY_AUTONOMY":"16 h","POWER_OUTPUT_RMS":"35 W","MAX_POWER":"35 W","MIN_FREQUENCY_RESPONSE":"60 Hz","MAX_FREQUENCY_RESPONSE":"20 kHz","INPUT_IMPEDANCE":"4 Ω","DISTORTION":"0.5 %","BATTERY_VOLTAGE":"5 V"}
    return NS.get(aid)

attrs=[
    {"id":"BRAND","value_name":"JBL"},
    {"id":"COLOR","value_name":"Negro"},
    {"id":"MODEL","value_name":"Flip 7"},
    {"id":"GTIN","value_name":"6925281992384"},
]
seen={a["id"] for a in attrs}
BAD={"EAN","UPC","MPN","SELLER_SKU","ITEM_CONDITION","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    nv=num_val(aid)
    if nv: attrs.append({"id":aid,"value_name":nv}); seen.add(aid); continue
    vals=ca.get("values") or []; vt=ca.get("value_type")
    if aid in ("RAM_MEMORY","INTERNAL_MEMORY"):
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")}); seen.add(aid)
        continue
    if aid=="ALPHANUMERIC_MODEL":
        attrs.append({"id":aid,"value_name":"JBLFLIP7BLK"}); seen.add(aid); continue
    BY={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","INCLUDES_CABLE","INCLUDES_BATTERY"}
    BN={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT","IS_WATERPROOF"}
    if vt=="boolean":
        attrs.append({"id":aid,"value_name":"Si" if aid in BY else ("No" if aid in BN else "No")}); seen.add(aid); continue
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

BLINDAJE="""

===== IMPORTANTE LEE ANTES DE COMPRAR =====
Producto REACONDICIONADO (no nuevo). Revisado, limpiado y probado al 100%.
RECLAMOS: Solo aceptamos cambios por defecto funcional. NO por audio subjetivo, estetica minima, ni cambio de opinion. Devolucion requiere video desempaque completo desde Mercado Envios.
Entrada USB-C funcional. Version OEM. NO compatible con app oficial JBL Portable. Al comprar aceptas condiciones."""

title="Bocina Jbl Flip 7 Bluetooth Reacondicionada Negra Usb-c"[:60]
desc=f"""Bocina JBL Flip 7 Bluetooth Portatil - Color Negro - REACONDICIONADA

Sonido JBL PRO, bateria 16 horas, IP68 resistencia agua/polvo, potencia 35W, peso 560g, AURACAST, AI Sound Boost. Entrada USB-C funcional. Version OEM.

INCLUYE: Bocina Flip 7 Negra reacondicionada + cable USB-C + caja generica + factura. Garantia 30 dias.

Envio GRATIS toda Mexico via Mercado Envios. Entrega 24-72 hrs.

Palabras clave: jbl flip 7, bocina reacondicionada, negra, bluetooth portatil, waterproof, impermeable, economica, oem.
{BLINDAJE}"""

body={
    "site_id":"MLM","title":title,"category_id":cat_id,"price":399,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","condition":"used","listing_type_id":"gold_pro",
    "catalog_listing":False,"attributes":attrs,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
}
if cpid: body["catalog_product_id"]=cpid
if pics: body["pictures"]=[{"source":u} for u in pics[:10]]

r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
retry=0
while r.status_code not in (200,201) and retry<5:
    retry+=1
    try: j=r.json()
    except: break
    bad=set(); miss=set()
    for c in j.get("cause",[]):
        msg=c.get("message","") or ""; code=c.get("code","") or ""
        if "missing" in code:
            for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                if m_.startswith("MLM") or m_ in BAD: continue
                if re.match(r'^[A-Z][A-Z_]+$',m_): miss.add(m_)
        if "invalid" in code or "number_invalid_format" in code:
            mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
            if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
        if "product_identifier.invalid_format" in code: bad.add("GTIN")
    if bad: attrs=[a for a in attrs if a["id"] not in bad]
    for mid in miss:
        if not any(a["id"]==mid for a in attrs):
            nv=num_val(mid)
            if nv: attrs.append({"id":mid,"value_name":nv})
            elif mid=="GTIN": attrs.append({"id":"GTIN","value_name":"6925281992384"})
            else: attrs.append({"id":mid,"value_name":"No aplica"})
    body["attributes"]=attrs
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)

if r.status_code in (200,201):
    nid=r.json().get("id")
    requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":desc},timeout=15)
    print(f"\nOK Flip 7 Negra reacond $399 -> {nid}")
    # Guardar en stock_config_oficial
    try:
        with open("stock_config_oficial.json") as f: sc=json.load(f)
    except: sc={}
    sc[nid]={"real_stock":10,"sku":"REACOND-Flip7-NEGRA","label":"Flip 7 Negra Reacond Claribel","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1,"account":"oficial"}
    with open("stock_config_oficial.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
    print(f"stock_config_oficial.json: real_stock=10")
else:
    print(f"ERR: {r.json()}")
