import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Catalog actual Sony XB100 Negra
SRC_CATALOG="MLM5223210438"
CPID="MLM25912333"  # Sony SRS-XB100 negra
MODEL="Sony XB100"; COLOR="Negra"; PRICE=559

def seo_title(): return "Bocina Sony Srs-xb100 Bluetooth Portatil Negra Ipx4 Nueva"[:60]
def seo_desc():
    return """Sony SRS-XB100 Bluetooth Portatil - Color Negro - NUEVA 100% ORIGINAL CON FACTURA

CARACTERISTICAS PRINCIPALES:
- Sonido EXTRA BASS potente y claro de Sony
- Bateria de 16 horas de reproduccion continua
- Resistencia al agua IPX4 (salpicaduras)
- Diafragma de 46mm con rendimiento superior
- Peso 274 g - ultraportatil
- Correa integrada para colgar o llevar donde sea
- Bluetooth 5.3 con conexion estable hasta 10m
- Microfono integrado para llamadas manos libres

INCLUYE:
- 1x Bocina Sony SRS-XB100 color Negro
- 1x Cable de carga USB
- 1x Manual de usuario
- 1x Guia de inicio rapido

GARANTIA Y ENVIO:
- Producto NUEVO en caja sellada con factura
- Garantia de 30 dias
- Envio GRATIS a todo Mexico
- Envio mismo dia si compras antes de las 2 PM
- Entrega en 24-72 hrs via Mercado Envios

COMPATIBILIDAD: Compatible con cualquier dispositivo Bluetooth - iPhone, Android, Samsung, Xiaomi, Motorola, iPad, tablets, laptops Windows/Mac.

IMPORTANTE: Esta bocina Sony SRS-XB100 es 100% original, adquirida por medio de comercializadora autorizada con factura.

Palabras clave: bocina sony, sony xb100, srs-xb100, altavoz bluetooth, parlante portatil sony, bocina portatil, bluetooth sony, bocina extra bass, sony waterproof, bocina inalambrica sony."""

prod=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=15).json()
cat_id=prod.get("category_details",{}).get("id") or prod.get("category_id") or "MLM59800"
pics=[p["url"] for p in (prod.get("pictures") or []) if p.get("url")]
print(f"cat_id={cat_id} pics={len(pics)}")

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []
cat_attrs=get_cat_attrs(cat_id)

NUMSPEC={"bat":(16,"h"),"pwr":(10,"W"),"minf":(100,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")}
ATTR2KEY={"MAX_BATTERY_AUTONOMY":"bat","POWER_OUTPUT_RMS":"pwr","MAX_POWER":"pwr","MIN_FREQUENCY_RESPONSE":"minf","MAX_FREQUENCY_RESPONSE":"maxf","INPUT_IMPEDANCE":"imp","DISTORTION":"dis","BATTERY_VOLTAGE":"volt"}
def num_val(aid):
    k=ATTR2KEY.get(aid)
    if k and k in NUMSPEC: n,u=NUMSPEC[k]; return f"{n} {u}"
    return None

attrs=[
    {"id":"BRAND","value_name":"Sony"},
    {"id":"COLOR","value_name":"Negro"},
    {"id":"MODEL","value_name":"SRS-XB100"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"GTIN","value_name":"No aplica"},
    {"id":"ALPHANUMERIC_MODEL","value_name":"SRS-XB100"},
]
seen={a["id"] for a in attrs}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
    if not req or aid in seen: continue
    nv=num_val(aid)
    if nv: attrs.append({"id":aid,"value_name":nv}); seen.add(aid); continue
    vals=ca.get("values") or []
    vt=ca.get("value_type")
    if aid in ("RAM_MEMORY","INTERNAL_MEMORY"):
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")}); seen.add(aid)
        continue
    BOOL_YES={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","IS_WATERPROOF","INCLUDES_CABLE","INCLUDES_BATTERY"}
    BOOL_NO={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT"}
    if vt=="boolean":
        attrs.append({"id":aid,"value_name":"Si" if aid in BOOL_YES else ("No" if aid in BOOL_NO else "No")}); seen.add(aid); continue
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

body={
    "site_id":"MLM","title":seo_title(),"category_id":cat_id,"price":PRICE,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_pro",
    "catalog_listing":False,"catalog_product_id":CPID,"attributes":attrs,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}],
}
if pics: body["pictures"]=[{"source":u} for u in pics[:10]]

r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
retry=0
while r.status_code not in (200,201) and retry<6:
    retry+=1
    try: j=r.json()
    except: break
    bad=set(); miss=set(); fix=set()
    for c in j.get("cause",[]):
        msg=c.get("message","") or ""; code=c.get("code","") or ""
        if "missing_required" in code or "missing_catalog_required" in code or "missing_conditional_required" in code:
            mm=re.findall(r"\[([^\]]+)\]",msg)
            for gr in mm:
                for x in gr.split(","):
                    x=x.strip().strip("\"'")
                    if x and x.isupper(): miss.add(x)
            sp=re.search(r'campo\s+"([^"]+)"\s+es obligatorio',msg)
            if sp:
                fn=sp.group(1).lower()
                if fn=="memoria ram": miss.add("RAM_MEMORY")
                elif fn=="memoria interna": miss.add("INTERNAL_MEMORY")
        if "attributes.omitted" in code or "number_invalid_format" in code:
            mm=re.search(r"attribute\s+([A-Z_]+)",msg) or re.search(r"Attribute\s+([A-Z_]+)",msg)
            if mm: fix.add(mm.group(1))
        if "attributes.invalid" in code:
            mm=re.search(r"Attribute:\s+([A-Z_]+)",msg)
            if mm: bad.add(mm.group(1))
        if "product_identifier.invalid_format" in code: fix.add("GTIN")
    if bad: attrs=[a for a in attrs if a["id"] not in bad]
    for mid in miss:
        if not any(a["id"]==mid for a in attrs):
            nv=num_val(mid)
            if nv: attrs.append({"id":mid,"value_name":nv})
            elif mid in ("RAM_MEMORY","INTERNAL_MEMORY"):
                for ca in cat_attrs:
                    if ca.get("id")==mid:
                        vs=ca.get("values") or []
                        if vs: attrs.append({"id":mid,"value_id":vs[0]["id"],"value_name":vs[0].get("name","")})
                        break
            else: attrs.append({"id":mid,"value_name":"No aplica"})
    if "GTIN" in fix: attrs=[a for a in attrs if a["id"]!="GTIN"]
    body["attributes"]=attrs
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)

if r.status_code in (200,201):
    nid=r.json().get("id")
    requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":seo_desc()},timeout=15)
    print(f"OK Sony XB100 tradicional -> {nid}")
    # Cerrar el catálogo actual
    rr=requests.put(f"https://api.mercadolibre.com/items/{SRC_CATALOG}",headers=H,json={"status":"closed"},timeout=15)
    print(f"close catalog {SRC_CATALOG}: {rr.status_code}")
else:
    print(f"ERR Sony: {str(r.json())[:500]}")
