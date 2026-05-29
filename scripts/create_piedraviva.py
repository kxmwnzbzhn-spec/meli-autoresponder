"""
Crear catalog_suggestion ASVA: Piedra Viva The Alchemia Lab Eau de Parfum 100ml (MLM-PERFUMES).
Datos oficiales del sitio thealchemialab.com. Fotos TAL desde Drive (portada + ritual/ofrenda/espíritu).
"""
import os, json, hashlib, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
print("ASVA uid:", requests.get(f"{API}/users/me",headers=H,timeout=15).json().get("id"))

DRIVE_IDS=[
 ("portada","11--fTV3zc_bIUADxcVoZ9e7Q-VSNr6iH"),
 ("ritual","1Qk0e0OwKuqZIDIngSZx9HpguTbnmgUzu"),
 ("ofrenda","1oSfdFgOFGOCi_4Xt-lMl-CX8x9SzTiKE"),
 ("espiritu","1oExzK6qznrcCxgr7vFKzBk_RxvmMf1k8"),
]
def dl(fid):
    r=requests.get(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",timeout=120)
    r.raise_for_status(); return r.content
pics=[]
for name,fid in DRIVE_IDS:
    img=dl(fid)
    rp=requests.post(f"{API}/pictures/items/upload",headers=H,
        files={"file":(f"piedraviva_{name}.png",img,"image/png")},timeout=120)
    print(f"  pic {name}: {rp.status_code}")
    if rp.status_code in (200,201):
        pics.append({"id":rp.json()["id"]})
print(f"fotos: {len(pics)}/{len(DRIVE_IDS)}")

h=hashlib.md5("the alchemia lab::piedra viva::mineral especiado 2024".encode()).hexdigest()
n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
EAN=b+str((10-(s%10))%10); print("EAN:",EAN)

TITLE=("Perfume Piedra Viva The Alchemia Lab Eau de Parfum 100ml Unisex | "
       "Mineral Especiado Terroso Incienso Madera Artesanal Mexicano Yucatán")

ATTRS=[
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
 {"id":"GTIN","values":[{"name":EAN}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]

DESC=(
"Piedra Viva de The Alchemia Lab, perfume de autor de la Colección México en la Piel, es una fragancia mineral, "
"seca y elegante con matices especiados y fondo terroso sofisticado. Inspirada en la fuerza ancestral de la piedra "
"volcánica mexicana. Una composición que abre con una sequedad mineral hipnótica, evoluciona hacia especias cálidas "
"y envolventes, y se asienta en un fondo terroso que recuerda la tierra húmeda después de la lluvia sobre roca volcánica.\n\n"
"CARACTERÍSTICAS PRINCIPALES\n"
"• Marca: The Alchemia Lab (perfumería artesanal mexicana)\n"
"• Colección: México en la Piel\n"
"• Concentración: Eau de Parfum (EDP)\n"
"• Volumen: 100 ml en frasco con vaporizador\n"
"• Familia olfativa: Mineral Especiado Terroso\n"
"• Carácter: Mineral · Especiado · Terroso\n"
"• Género: Unisex\n"
"• Duración aproximada: +8 horas\n"
"• Año: 2024\n"
"• Origen: Yucatán, México\n\n"
"PIRÁMIDE OLFATIVA\n"
"• Apertura: minerales secos con sequedad hipnótica\n"
"• Corazón: especias cálidas y envolventes con incienso rosado\n"
"• Fondo: terroso amaderado que evoca tierra húmeda sobre roca volcánica\n\n"
"¿POR QUÉ ELEGIR PIEDRA VIVA?\n"
"• Perfil unisex de carácter nicho con elegancia austera\n"
"• Composición mineral única en perfumería mexicana artesanal\n"
"• Excelente proyección y permanencia (+8 horas en piel)\n"
"• Identidad sofisticada para personalidades que buscan distinción\n\n"
"CASOS DE USO\n"
"• Uso diario para destacar con un perfil distinto\n"
"• Eventos, noches y momentos especiales\n"
"• Coleccionistas de perfumería de autor\n"
"• Para amantes de fragancias minerales, secas y terrosas\n\n"
"DETALLES DEL PRODUCTO\n"
"Frasco con vaporizador atomizador. Eau de Parfum 100 ml. Elaborado a mano en Yucatán, México por The Alchemia Lab.\n\n"
"Familia olfativa principal: Mineral Especiado Terroso\n"
"Notas dominantes: Minerales secos, Especias cálidas, Incienso, Fondo terroso amaderado"
)

body={"site_id":"MLM","domain_id":"MLM-PERFUMES","type":"EDIT","title":TITLE,"attributes":ATTRS,"pictures":pics}
print("\nPOST /catalog_suggestions ...")
r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
print("http",r.status_code)
rb=r.json(); print(json.dumps(rb,ensure_ascii=False)[:1800])
sid=rb.get("id") or rb.get("suggestion_id")
if sid:
    print(f"\n>>> SUGGESTION_ID = {sid}")
    import time; time.sleep(3)
    rd=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":DESC},timeout=20)
    print("descripción POST",rd.status_code, rd.text[:200])
