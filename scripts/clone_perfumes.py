import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H_JUAN={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
H_CLA={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
cla=requests.get("https://api.mercadolibre.com/users/me",headers=H_CLA).json()
print(f"Claribel: {cla.get('nickname')} id={cla.get('id')}")

# Load perfumes únicos
with open("juan_perfumes_uniq.json") as f: perfumes=json.load(f)

# Cargar stock config
try:
    with open("stock_config_oficial.json") as f: sc=json.load(f)
except: sc={}

BLINDAJE="""

===== AVISO IMPORTANTE =====
Producto 100% ORIGINAL con factura de comercializadora autorizada.
RECLAMOS: Solo aceptamos cambios por producto dañado en envio o diferente al anunciado. NO por percepcion subjetiva de aroma, duracion o preferencias. Devoluciones requieren video sin cortes del desempaque. Al comprar aceptas estas condiciones."""

def get_full_item(iid, headers):
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=headers,timeout=15).json()
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=headers,timeout=15)
    desc=""
    if d.status_code==200:
        try: desc=d.json().get("plain_text","")
        except: pass
    return it, desc

def publish_claribel(p_juan):
    iid=p_juan.get("id")
    # traer full data del juan item
    full_juan,desc_juan=get_full_item(iid,H_JUAN)
    title=full_juan.get("title","")
    price=full_juan.get("price")
    cat_id=full_juan.get("category_id") or "MLM159230"
    cpid=full_juan.get("catalog_product_id")
    pics=[p["url"] for p in (full_juan.get("pictures") or []) if p.get("url")]
    attrs_raw=full_juan.get("attributes") or []
    
    # Preparar attrs limpios (quitar los que causan problemas)
    attrs=[]
    for a in attrs_raw:
        aid=a.get("id")
        if aid in ("SELLER_SKU","MPN","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"): continue
        vid=a.get("value_id"); vn=a.get("value_name")
        if not vid and not vn: continue
        e={"id":aid}
        if vid: e["value_id"]=vid
        if vn: e["value_name"]=vn
        attrs.append(e)
    
    # desc final
    if not desc_juan:
        desc_juan=f"{title} - 100% original con factura. Garantia 30 dias. Envio GRATIS."
    final_desc = desc_juan
    if "AVISO IMPORTANTE" not in final_desc:
        final_desc += BLINDAJE
    
    body={
        "site_id":"MLM","title":title[:60],"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_pro",
        "catalog_listing":False,"attributes":attrs,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
    }
    if cpid: body["catalog_product_id"]=cpid
    if pics: body["pictures"]=[{"source":u} for u in pics[:10]]
    
    r=requests.post("https://api.mercadolibre.com/items",headers=H_CLA,json=body,timeout=30)
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
                    if m_.startswith("MLM"): continue
                    miss.add(m_)
            if "invalid" in code or "omitted" in code:
                mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
                if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
            if "product_identifier.invalid_format" in code: bad.add("GTIN")
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                attrs.append({"id":mid,"value_name":"No aplica"})
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H_CLA,json=body,timeout=30)
    
    if r.status_code in (200,201):
        nid=r.json().get("id")
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H_CLA,json={"plain_text":final_desc},timeout=15)
        return nid, None
    return None, str(r.json())[:400]

# Batch de los primeros 10 perfumes (para no timeout)
BATCH_SIZE=15
START=int(os.environ.get("START",0))
END=min(START+BATCH_SIZE,len(perfumes))
print(f"\n=== Publicando perfumes {START}..{END-1} de {len(perfumes)} ===\n")

ok=0; err=0
for p in perfumes[START:END]:
    title=p.get("title","")
    print(f"[{START+ok+err}] {title[:60]}")
    nid,e=publish_claribel(p)
    if nid:
        print(f"  OK -> {nid}")
        sc[nid]={"real_stock":1,"sku":f"PERF-CLA-{nid}","label":title[:50],"auto_replenish":False,"replenish_quantity":1,"min_visible_stock":1,"account":"oficial","cloned_from":p.get("id")}
        ok+=1
    else:
        print(f"  ERR: {e[:200]}")
        err+=1
    time.sleep(2)

with open("stock_config_oficial.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"\n{ok} OK, {err} ERR")
