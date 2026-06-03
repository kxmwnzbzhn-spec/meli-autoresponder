"""
Crear SEGUNDA sugerencia de Piedra Viva The Alchemia Lab (EAN diferente, título/desc reordenados).
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
        files={"file":(f"piedraviva_v2_{name}.png",img,"image/png")},timeout=120)
    print(f"  pic {name}: {rp.status_code}")
    if rp.status_code in (200,201):
        pics.append({"id":rp.json()["id"]})
print(f"fotos: {len(pics)}")

# nuevo EAN con seed distinto
h=hashlib.md5("the alchemia lab::piedra viva::edicion artesanal mexico yucatan v2".encode()).hexdigest()
n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
EAN=b+str((10-(s%10))%10); print("EAN nuevo:",EAN)

# título reordenado / sinónimos
TITLE=("Perfume Unisex Piedra Viva The Alchemia Lab Eau de Parfum 100ml | "
       "Amaderado Mineral Especias Incienso Terroso Perfumería Artesanal de México Yucatán")

ATTRS=[
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
 {"id":"GTIN","values":[{"name":EAN}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]

DESC=(
"Piedra Viva, perfume de autor de The Alchemia Lab dentro de la colección México en la Piel, captura la esencia "
"ancestral de la piedra volcánica mexicana en una composición mineral, seca y profundamente elegante. Esta fragancia "
"unisex de carácter nicho combina sequedad mineral con especias cálidas y un fondo terroso amaderado de excelente sofisticación.\n\n"
"CARACTERÍSTICAS\n"
"• Marca: The Alchemia Lab — perfumería artesanal mexicana\n"
"• Colección: México en la Piel\n"
"• Tipo: Eau de Parfum (EDP)\n"
"• Volumen: 100 ml en frasco con vaporizador\n"
"• Familia olfativa: Amaderado Mineral Especiado\n"
"• Carácter: Mineral · Especiado · Terroso · Nicho\n"
"• Género: Unisex\n"
"• Duración: más de 8 horas en piel\n"
"• Hecho a mano en Yucatán, México\n\n"
"ESTRUCTURA OLFATIVA\n"
"• Salida: notas minerales secas con efecto hipnótico\n"
"• Corazón: especias cálidas y envolventes con un acento de incienso rosado\n"
"• Fondo: terroso amaderado, recuerda la tierra húmeda sobre roca volcánica tras la lluvia\n\n"
"¿POR QUÉ ELEGIRLO?\n"
"• Identidad olfativa única en perfumería artesanal mexicana\n"
"• Perfil unisex de elegancia austera y carácter nicho\n"
"• Excelente proyección con permanencia prolongada\n"
"• Para personalidades que buscan distinción y diferenciación\n\n"
"CASOS DE USO\n"
"• Uso diario con personalidad marcada\n"
"• Noches, eventos y momentos especiales\n"
"• Coleccionistas de perfumería de autor mexicana\n"
"• Amantes de fragancias minerales y terrosas\n\n"
"PRESENTACIÓN\n"
"Frasco con vaporizador atomizador. Eau de Parfum 100 ml. Elaborado artesanalmente en Yucatán por The Alchemia Lab.\n\n"
"Familia principal: Amaderado Mineral Especiado\n"
"Notas dominantes: Minerales, Especias cálidas, Incienso, Madera terrosa"
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
    print("desc POST",rd.status_code, rd.text[:200])
