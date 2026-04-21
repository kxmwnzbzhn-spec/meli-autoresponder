import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

SRC=[
    ("MLM2880754323","Go 3","Negra",469),
    ("MLM2880758735","Charge 6","Roja",919),
    ("MLM2880758747","Clip 5","Morada",719),
    ("MLM2880758751","Grip","Negra",619),
    ("MLM2880766021","Flip 7","Roja",819),
    ("MLM5222936976","Charge 6","Azul",919),
    ("MLM5222983008","Charge 6","Camuflaje",919),
    ("MLM5222983106","Go Essential 2","Azul",469),
    ("MLM5222983110","Go Essential 2","Roja",469),
    ("MLM5222983148","Go 4","Camuflaje",469),
    ("MLM5222987710","Go 4","Roja",469),
    ("MLM5222987718","Go 4","Azul Marino",469),
    ("MLM5222987720","Go 4","Rosa",469),
]

def seo_title(m, c):
    tm={
        "Charge 6": f"Bocina Jbl Charge 6 Bluetooth Portatil {c} Ip68 Nueva",
        "Flip 7":   f"Bocina Jbl Flip 7 Bluetooth Portatil {c} Ip68 Nueva",
        "Clip 5":   f"Bocina Jbl Clip 5 Bluetooth Portatil {c} Ip67 Nueva",
        "Grip":     f"Bocina Jbl Grip Bluetooth Portatil {c} Luz Led Nueva",
        "Go 4":     f"Bocina Jbl Go 4 Bluetooth Portatil {c} Ip67 Nueva",
        "Go Essential 2": f"Jbl Go Essential 2 Bluetooth Portatil {c} Ip67",
        "Go 3":     f"Bocina Jbl Go 3 Bluetooth Portatil {c} Ip67 Nueva",
    }
    return tm.get(m,f"Bocina Jbl {m} Bluetooth Portatil {c} Nueva")[:60]

SPEC={
    "Charge 6": {"bat":"28 horas","power":"40W","ip":"IP68","weight":"970 g","extras":"Powerbank integrada. AURACAST multi-bocina. Conexion con app JBL Portable."},
    "Flip 7":   {"bat":"16 horas","power":"35W","ip":"IP68","weight":"560 g","extras":"AI Sound Boost. AURACAST. Conexion con app JBL Portable."},
    "Clip 5":   {"bat":"12 horas","power":"7W","ip":"IP67","weight":"285 g","extras":"Mosqueton integrado para llevar donde sea. AURACAST."},
    "Grip":     {"bat":"12 horas","power":"8W","ip":"IP68","weight":"400 g","extras":"Iluminacion LED dinamica. Forma pensada para agarrar con una mano."},
    "Go 4":     {"bat":"7 horas","power":"4.2W","ip":"IP67","weight":"190 g","extras":"Tamano bolsillo. AI Sound Boost. Conexion con app JBL Portable."},
    "Go Essential 2": {"bat":"7 horas","power":"3.1W","ip":"IPX7","weight":"200 g","extras":"Edicion esencial. Bluetooth 5.1. Clip integrado."},
    "Go 3":     {"bat":"5 horas","power":"4.2W","ip":"IP67","weight":"209 g","extras":"Diseno iconico JBL. Cuerda integrada para colgar."},
}

def seo_desc(m, c, price):
    s=SPEC.get(m,{"bat":"","power":"","ip":"","weight":"","extras":""})
    return f"""JBL {m} Bluetooth Portatil - Color {c} - NUEVA 100% ORIGINAL CON FACTURA

CARACTERISTICAS PRINCIPALES:
- Sonido JBL PRO Sound potente y claro
- Bateria de {s['bat']} de reproduccion continua
- Resistencia al agua y polvo {s['ip']}
- Potencia {s['power']}
- Peso {s['weight']} - ultraportatil
- {s['extras']}

INCLUYE:
- 1x Bocina JBL {m} color {c}
- 1x Cable de carga USB-C
- 1x Manual de usuario
- 1x Guia de inicio rapido

GARANTIA Y ENVIO:
- Producto NUEVO en caja sellada con factura
- Garantia de 30 dias con nosotros
- Envio GRATIS a todo Mexico
- Envio el mismo dia si compras antes de las 2 PM
- Entrega en 24-72 hrs via Mercado Envios

COMPATIBILIDAD:
Compatible con cualquier dispositivo Bluetooth: iPhone, Android, Samsung, Xiaomi, Motorola, iPad, tablets, laptops Windows/Mac.

IMPORTANTE:
Esta bocina JBL {m} es 100% original, adquirida por medio de comercializadora autorizada con factura. No es reacondicionada, no es replica.

Preguntanos lo que quieras antes de comprar. Respondemos en menos de 1 hora.

Palabras clave: bocina jbl, altavoz bluetooth, parlante portatil, jbl {m.lower()}, bocina {c.lower()}, bluetooth portatil, bocina waterproof, bocina impermeable, bocina inalambrica, bocina jbl original, jbl {m.lower()} {c.lower()}, regalo bocina, bocina fiesta, bocina exterior."""

created=[]
closed=[]
for iid,model,color,price in SRC:
    item=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    cpid=item.get("catalog_product_id")
    cat_id=item.get("category_id") or "MLM1055"
    pics=[p["url"] for p in item.get("pictures",[]) if p.get("url")]
    prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json() if cpid else {}
    attrs=[]
    for a in (prod.get("attributes") or []):
        aid=a.get("id"); vid=a.get("value_id"); vn=a.get("value_name")
        if not aid: continue
        if not vid and not vn: continue
        if aid in ("SELLER_SKU","GTIN","EAN","UPC","MPN"): continue
        e={"id":aid}
        if vid: e["value_id"]=vid
        if vn and isinstance(vn,str) and vn.strip()!="" and not vn.lower().endswith(" nan"):
            e["value_name"]=vn
        attrs.append(e)
    seen={a["id"] for a in attrs}
    if "BRAND" not in seen: attrs.append({"id":"BRAND","value_name":"JBL"})
    if "COLOR" not in seen: attrs.append({"id":"COLOR","value_name":color})
    if "ITEM_CONDITION" not in seen: attrs.append({"id":"ITEM_CONDITION","value_name":"Nuevo"})
    title=seo_title(model,color)
    body={
        "site_id":"MLM","title":title,"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_pro",
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
        bad=set()
        for c in j.get("cause",[]):
            msg=(c.get("message") or "")
            mm=re.search(r"attribute\s+([A-Z_]+)",msg)
            if mm: bad.add(mm.group(1))
            mm2=re.search(r"\[([A-Z_, ]+)\]",msg)
            if mm2:
                for x in mm2.group(1).split(","):
                    x=x.strip()
                    if x and x.isupper(): bad.add(x)
        if not bad: break
        attrs=[a for a in attrs if a["id"] not in bad]
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    if r.status_code in (200,201):
        resp=r.json()
        new_id=resp.get("id")
        requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":seo_desc(model,color,price)},timeout=15)
        print(f"OK {iid} -> {new_id} [{model} {color}]")
        created.append({"src":iid,"new":new_id,"model":model,"color":color,"price":price})
    else:
        err=str(r.json() if r.headers.get("content-type","").startswith("application") else r.text)[:300]
        print(f"ERR {iid} [{model} {color}]: {err}")
        created.append({"src":iid,"model":model,"color":color,"err":err[:200]})
    time.sleep(2)

print("\n=== CERRANDO ORIGINALES ===")
for c in created:
    if c.get("new"):
        rr=requests.put(f"https://api.mercadolibre.com/items/{c['src']}",headers=H,json={"status":"closed"},timeout=15)
        print(f"close {c['src']}: {rr.status_code}")
        closed.append(c['src'])
        time.sleep(0.5)

print("\n=== SUMMARY ===")
print(f"Tradicionales creadas: {sum(1 for c in created if c.get('new'))}/{len(SRC)}")
print(f"Catalogos cerrados: {len(closed)}")
print("\n=== MAPPING ===")
for c in created:
    if c.get("new"): print(f"  {c['src']} -> {c['new']} [{c['model']} {c['color']}] ${c['price']}")
    else: print(f"  {c['src']} FAILED: {c.get('err')}")
