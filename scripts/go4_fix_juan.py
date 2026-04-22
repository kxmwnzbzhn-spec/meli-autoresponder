import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# === 1) Ajustar TODAS las Go 4 activas a $499 ===
sid=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()["id"]
ids=[]
for st in ["active","paused"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}",headers=H,timeout=20).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break

go4_ids=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,status",headers=H,timeout=20).json()
    for x in res:
        b=x.get("body",{})
        if not b: continue
        t=(b.get("title") or "").lower()
        if ("go 4" in t or "go4" in t) and "go essential" not in t:
            go4_ids.append(b)

print(f"=== {len(go4_ids)} Go 4 actuales ===")
for b in go4_ids:
    iid=b.get("id"); cur_price=b.get("price"); cur_status=b.get("status")
    if cur_price != 499:
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":499},timeout=15)
        print(f"  {iid} ({cur_status}) ${cur_price}->$499: {r.status_code}")
    else:
        print(f"  {iid} ya en $499")
    time.sleep(0.3)

# === 2) Publicar Go 4 Negra nueva ===
print("\n=== Publicando Go 4 Negra NUEVA ===")
# Buscar catalog
rs=requests.get("https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q=JBL+Go+4+Negro",headers=H,timeout=15).json()
cpid=None
for it in rs.get("results",[])[:10]:
    nm=(it.get("name") or "").lower()
    if any(b in nm for b in ["funda","case","cover","tester"]): continue
    if "go 4" in nm and ("negro" in nm or "negra" in nm or "black" in nm):
        cpid=it.get("id"); print(f"  cpid: {cpid} - {it.get('name')}"); break

if not cpid:
    cpid="MLM44731940"  # default Go 4 Negro

prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
cat_id=prod.get("category_details",{}).get("id") or "MLM59800"
pics=[p["url"] for p in (prod.get("pictures") or []) if p.get("url")]

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

def num_val(aid):
    NS={"MAX_BATTERY_AUTONOMY":"7 h","POWER_OUTPUT_RMS":"4.2 W","MAX_POWER":"4.2 W","MIN_FREQUENCY_RESPONSE":"180 Hz","MAX_FREQUENCY_RESPONSE":"20 kHz","INPUT_IMPEDANCE":"4 Ω","DISTORTION":"1 %","BATTERY_VOLTAGE":"5 V"}
    return NS.get(aid)

cat_attrs=get_cat_attrs(cat_id)
attrs=[
    {"id":"BRAND","value_name":"JBL"},
    {"id":"COLOR","value_name":"Negro"},
    {"id":"MODEL","value_name":"Go 4"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"GTIN","value_name":"6925281995194"},
]
seen={a["id"] for a in attrs}
BAD={"EAN","UPC","MPN","SELLER_SKU","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"}
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
        attrs.append({"id":aid,"value_name":"JBLGO4BLK"}); seen.add(aid); continue
    BY={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","INCLUDES_CABLE","INCLUDES_BATTERY"}
    BN={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT","IS_WATERPROOF"}
    if vt=="boolean":
        attrs.append({"id":aid,"value_name":"Si" if aid in BY else ("No" if aid in BN else "No")}); seen.add(aid); continue
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

title="Bocina Jbl Go 4 Bluetooth Portatil Negra Ip67 Nueva Original"[:60]
desc="""JBL Go 4 Bluetooth Portatil - Color Negro - NUEVA con caja original y factura

Sonido JBL PRO, 7 horas bateria, IP67, potencia 4.2W, peso 190g, AI Sound Boost, correa integrada.

INCLUYE: Bocina Go 4 Negra + caja original + cable USB-C + manual + factura.
GARANTIA 30 dias. Envio GRATIS todo Mexico."""

body={
    "site_id":"MLM","title":title,"category_id":cat_id,"price":499,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_pro",
    "catalog_listing":False,"catalog_product_id":cpid,"attributes":attrs,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
}
if pics: body["pictures"]=[{"source":u} for u in pics[:10]]

r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
retry=0
while r.status_code not in (200,201) and retry<6:
    retry+=1
    try: j=r.json()
    except: break
    bad=set(); miss=set()
    for c in j.get("cause",[]):
        msg=c.get("message","") or ""; code=c.get("code","") or ""
        if "missing" in code:
            for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                if m_.startswith("MLM") or m_ in BAD: continue
                miss.add(m_)
        if "invalid" in code or "omitted" in code or "number_invalid_format" in code:
            mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
            if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
        if "product_identifier.invalid_format" in code: bad.add("GTIN")
    if bad: attrs=[a for a in attrs if a["id"] not in bad]
    for mid in miss:
        if not any(a["id"]==mid for a in attrs):
            nv=num_val(mid)
            if nv: attrs.append({"id":mid,"value_name":nv})
            else: attrs.append({"id":mid,"value_name":"No aplica"})
    body["attributes"]=attrs
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)

if r.status_code in (200,201):
    nid=r.json().get("id")
    requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":desc},timeout=15)
    print(f"\n✅ Go 4 Negra NUEVA publicada: {nid} - $499")
else:
    print(f"\n❌ ERR: {r.json()}")
