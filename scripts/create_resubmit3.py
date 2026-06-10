"""
Resubmit: Flofen V3 + Piedra Viva V3 (Amaderado) + Piedra Viva V4 (Especiados).
EAN y títulos distintos para cada uno; mismas fotos.
"""
import os, json, hashlib, pathlib, requests, meli_token, time
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
print("ASVA uid:", requests.get(f"{API}/users/me",headers=H,timeout=15).json().get("id"))

def ean13(seed):
    h=hashlib.md5(seed.encode()).hexdigest()
    n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
    b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
    return b+str((10-(s%10))%10)

def upload_local(fp, name):
    rp=requests.post(f"{API}/pictures/items/upload",headers=H,
        files={"file":(name,fp.read_bytes(),"image/png")},timeout=120)
    return rp.json()["id"] if rp.status_code in (200,201) else None

def upload_drive(fid, name):
    r=requests.get(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",timeout=120)
    rp=requests.post(f"{API}/pictures/items/upload",headers=H,
        files={"file":(name,r.content,"image/png")},timeout=120)
    return rp.json()["id"] if rp.status_code in (200,201) else None

def post(body, desc):
    r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
    print(" POST", r.status_code)
    rb=r.json()
    sid=rb.get("id") or rb.get("suggestion_id")
    if sid:
        print(f" >>> SUGGESTION_ID = {sid}  status={rb.get('status')}")
        time.sleep(4)
        rd=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
        print(" desc",rd.status_code)
    else:
        print(" body:", json.dumps(rb,ensure_ascii=False)[:400])
    return sid

# ============ 1) FLOFEN V3 ============
print("\n=== 1) FLOFEN V3 ===")
ASSETS=pathlib.Path("scripts/assets/flofen_vainilla")
flo_pics=[]
for f in ["01_portada.png","02_vanilla_pods.png","03_lifestyle.png","04_splash.png","05_label.png"]:
    pid=upload_local(ASSETS/f, f)
    if pid: flo_pics.append({"id":pid})
print("fotos:",len(flo_pics))
ean_f=ean13("attessa secret::flofen::bare vanilla::v3::mujer sensual")
print("EAN F3:",ean_f)
title_f=("Fragancia Corporal Mujer Flofen Bare Vanilla Attessa´s Secret 250ml Body Mist Vainilla Cremosa | "
         "Aroma Sensual Femenino Cashmere Almizcle Gourmand Brume Parfumée")
attrs_f=[
 {"id":"BRAND","values":[{"name":"Attessa´s Secret"}]},
 {"id":"LINE","values":[{"name":"Flofen"}]},
 {"id":"PERFUME_NAME","values":[{"name":"Bare Vanilla"}]},
 {"id":"GENDER","values":[{"name":"Mujer"}]},
 {"id":"PERFUME_TYPE","values":[{"name":"Splash"}]},
 {"id":"APPLICATION_FORMAT","values":[{"name":"Spray"}]},
 {"id":"IS_REFILLABLE","values":[{"name":"No"}]},
 {"id":"UNIT_VOLUME","values":[{"name":"250 mL"}]},
 {"id":"OLFACTORY_FAMILIES","values":[{"name":"Gourmand"}]},
 {"id":"GTIN","values":[{"name":ean_f}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]
desc_f=("Flofen Bare Vanilla Body Mist de Attessa´s Secret. Fragancia corporal femenina de carácter gourmand "
        "y sensual, que combina vainilla cremosa con un fondo aterciopelado de almizcle cashmere. Aroma cálido, "
        "dulce y reconfortante en presentación de 250 ml.\n\n"
        "DETALLES\n• Marca: Attessa´s Secret\n• Línea: Flofen\n• Variante: Bare Vanilla\n"
        "• Body Mist / Fragrance Mist (Brume Parfumée)\n• 250 ml con vaporizador\n• Splash · Spray · Mujer\n"
        "• Familia: Gourmand\n\nNOTAS\n• Whipped Vanilla (vainilla cremosa)\n• Soft Cashmere (almizcle aterciopelado)\n"
        "• Sensación Skin to Skin\n\nIDEAL PARA\n• Uso diario y reaplicación\n• Después del baño y del gym\n"
        "• Layering con perfumes florales o amaderados\n• Mujer que ama aromas dulces gourmand")
body_f={"site_id":"MLM","domain_id":"MLM-PERFUMES","type":"EDIT","title":title_f,"attributes":attrs_f,"pictures":flo_pics}
post(body_f, desc_f)

# ============ 2) PIEDRA VIVA V3 (Amaderado, variación de V2) ============
print("\n=== 2) PIEDRA VIVA V3 ===")
pv_pics=[]
for nm,fid in [("portada","11--fTV3zc_bIUADxcVoZ9e7Q-VSNr6iH"),("ritual","1Qk0e0OwKuqZIDIngSZx9HpguTbnmgUzu"),
               ("ofrenda","1oSfdFgOFGOCi_4Xt-lMl-CX8x9SzTiKE"),("espiritu","1oExzK6qznrcCxgr7vFKzBk_RxvmMf1k8")]:
    pid=upload_drive(fid, f"pv3_{nm}.png")
    if pid: pv_pics.append({"id":pid})
print("fotos:",len(pv_pics))
ean_p3=ean13("the alchemia lab::piedra viva::nicho amaderado mineral v3")
print("EAN PV3:",ean_p3)
title_p3=("Perfume Nicho Piedra Viva The Alchemia Lab 100ml Eau de Parfum Unisex | "
          "Mineral Madera Especias Incienso Terroso Yucatán Perfumería Artesanal Mexicana")
attrs_p3=[
 {"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
 {"id":"LINE","values":[{"name":"México en la Piel"}]},
 {"id":"PERFUME_NAME","values":[{"name":"Piedra Viva"}]},
 {"id":"GENDER","values":[{"name":"Sin género"}]},
 {"id":"PERFUME_TYPE","values":[{"name":"Eau de parfum"}]},
 {"id":"APPLICATION_FORMAT","values":[{"name":"Spray"}]},
 {"id":"IS_REFILLABLE","values":[{"name":"No"}]},
 {"id":"UNIT_VOLUME","values":[{"name":"100 mL"}]},
 {"id":"OLFACTORY_FAMILIES","values":[{"name":"Amaderado"}]},
 {"id":"COUNTRY_OF_ORIGIN","values":[{"name":"México"}]},
 {"id":"GTIN","values":[{"name":ean_p3}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]
desc_p3=("Piedra Viva es un perfume de nicho de The Alchemia Lab, parte de la colección México en la Piel. Fragancia "
        "amaderada con un perfil mineral, seco y terroso, evolucionando hacia especias cálidas e incienso rosado. "
        "Hecha a mano en Yucatán, México.\n\nDETALLES\n• Marca: The Alchemia Lab\n• Colección: México en la Piel\n"
        "• Eau de Parfum 100 ml\n• Unisex\n• Familia: Amaderado Mineral\n• Duración: +8 horas\n\n"
        "ESTRUCTURA OLFATIVA\n• Apertura: minerales secos\n• Corazón: especias cálidas, incienso rosado\n"
        "• Fondo: madera terrosa, recuerda tierra húmeda sobre roca volcánica\n\nIDEAL PARA\n"
        "• Personalidades distintivas\n• Coleccionistas de perfumería de autor mexicana\n"
        "• Uso diario, noches, eventos especiales")
body_p3={"site_id":"MLM","domain_id":"MLM-PERFUMES","type":"EDIT","title":title_p3,"attributes":attrs_p3,"pictures":pv_pics}
post(body_p3, desc_p3)

# ============ 3) PIEDRA VIVA V4 (Especiados, variación de V1) ============
print("\n=== 3) PIEDRA VIVA V4 ===")
ean_p4=ean13("the alchemia lab::piedra viva::especiado mineral terroso v4 mexico")
print("EAN PV4:",ean_p4)
title_p4=("Perfume Piedra Viva The Alchemia Lab Eau de Parfum 100ml Colección México en la Piel | "
          "Especias Incienso Madera Mineral Terroso Unisex Yucatán Artesanal")
attrs_p4=[
 {"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
 {"id":"LINE","values":[{"name":"México en la Piel"}]},
 {"id":"PERFUME_NAME","values":[{"name":"Piedra Viva"}]},
 {"id":"GENDER","values":[{"name":"Sin género"}]},
 {"id":"PERFUME_TYPE","values":[{"name":"Eau de parfum"}]},
 {"id":"APPLICATION_FORMAT","values":[{"name":"Spray"}]},
 {"id":"IS_REFILLABLE","values":[{"name":"No"}]},
 {"id":"UNIT_VOLUME","values":[{"name":"100 mL"}]},
 {"id":"OLFACTORY_FAMILIES","values":[{"name":"Especiados"}]},
 {"id":"COUNTRY_OF_ORIGIN","values":[{"name":"México"}]},
 {"id":"GTIN","values":[{"name":ean_p4}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]
desc_p4=("Piedra Viva — perfume de la colección México en la Piel de The Alchemia Lab. Fragancia especiada de carácter "
        "mineral y terroso, con un corazón cálido de especias e incienso rosado sobre un fondo amaderado. Elaborada en "
        "Yucatán, México con técnica artesanal.\n\nDETALLES\n• Marca: The Alchemia Lab\n• Colección: México en la Piel\n"
        "• Eau de Parfum 100 ml\n• Género: Unisex\n• Familia: Especiados\n• Duración: +8 horas en piel\n\n"
        "PIRÁMIDE\n• Salida: minerales secos con sequedad hipnótica\n• Corazón: especias cálidas, incienso rosado\n"
        "• Fondo: madera terrosa que evoca tierra húmeda sobre piedra volcánica\n\nINSPIRACIÓN\n"
        "Captura la fuerza ancestral de la piedra volcánica mexicana, con identidad sofisticada y nicho.")
body_p4={"site_id":"MLM","domain_id":"MLM-PERFUMES","type":"EDIT","title":title_p4,"attributes":attrs_p4,"pictures":pv_pics}
post(body_p4, desc_p4)

print("\n[OK] terminado")
