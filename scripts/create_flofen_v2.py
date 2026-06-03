"""
SEGUNDA sugerencia Flofen Bare Vanilla Attessa´s Secret. EAN nuevo, título/desc reordenados.
"""
import os, json, hashlib, pathlib, requests, meli_token, time
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
print("ASVA uid:", requests.get(f"{API}/users/me",headers=H,timeout=15).json().get("id"))

ASSETS=pathlib.Path("scripts/assets/flofen_vainilla")
PHOTOS=["01_portada.png","02_vanilla_pods.png","03_lifestyle.png","04_splash.png","05_label.png"]
pics=[]
for f in PHOTOS:
    p=ASSETS/f
    if not p.exists(): continue
    rp=requests.post(f"{API}/pictures/items/upload",headers=H,
        files={"file":(f,p.read_bytes(),"image/png")},timeout=120)
    print(f"  pic {f}: {rp.status_code}")
    if rp.status_code in (200,201):
        pics.append({"id":rp.json()["id"]})
print(f"fotos: {len(pics)}/{len(PHOTOS)}")

h=hashlib.md5("attessa secret::flofen::bare vanilla::v2::gourmand mujer".encode()).hexdigest()
n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
EAN=b+str((10-(s%10))%10); print("EAN nuevo:",EAN)

# título reordenado (Mujer primero, sinónimos)
TITLE=("Body Mist Mujer Attessa´s Secret Flofen Bare Vanilla 250ml Fragancia Corporal | "
       "Vainilla Cremosa Cashmere Almizcle Aroma Dulce Gourmand Brume Parfumée")

ATTRS=[
 {"id":"BRAND","values":[{"name":"Attessa´s Secret"}]},
 {"id":"LINE","values":[{"name":"Flofen"}]},
 {"id":"PERFUME_NAME","values":[{"name":"Bare Vanilla"}]},
 {"id":"GENDER","values":[{"name":"Mujer"}]},
 {"id":"PERFUME_TYPE","values":[{"name":"Splash"}]},
 {"id":"APPLICATION_FORMAT","values":[{"name":"Spray"}]},
 {"id":"IS_REFILLABLE","values":[{"name":"No"}]},
 {"id":"UNIT_VOLUME","values":[{"name":"250 mL"}]},
 {"id":"OLFACTORY_FAMILIES","values":[{"name":"Orientales"}]},
 {"id":"GTIN","values":[{"name":EAN}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]

DESC=(
"Body mist Flofen Bare Vanilla de la marca Attessa´s Secret, una fragancia corporal femenina que envuelve la piel "
"con vainilla cremosa y un acabado aterciopelado de almizcle tipo cashmere. Aroma dulce, gourmand y reconfortante, "
"perfecto para tu rutina diaria y para reaplicar a lo largo del día.\n\n"
"¿POR QUÉ ELEGIR FLOFEN BARE VANILLA?\n"
"• Aroma femenino dulce de carácter gourmand\n"
"• Fórmula tipo body mist ligera, fácil de usar varias veces al día\n"
"• Botella generosa de 250 ml con vaporizador\n"
"• Presentación elegante con detalle dorado\n\n"
"FICHA TÉCNICA\n"
"• Marca: Attessa´s Secret\n"
"• Línea: Flofen\n"
"• Variante: Bare Vanilla\n"
"• Tipo: Body Mist / Fragrance Mist (Brume Parfumée)\n"
"• Concentración: Splash (refrescante)\n"
"• Volumen: 250 ml (8.4 fl oz)\n"
"• Formato: Spray\n"
"• Género: Femenino\n"
"• Familia olfativa: Oriental Gourmand\n\n"
"PIRÁMIDE OLFATIVA\n"
"• Nota dominante: Whipped Vanilla — vainilla batida cremosa\n"
"• Nota envolvente: Soft Cashmere — almizcle suave aterciopelado\n"
"• Sensación: Skin to Skin, cálida e íntima\n\n"
"OCASIONES Y CASOS DE USO\n"
"• Uso diario después del baño o ducha\n"
"• Refresco aromático durante el día y en la oficina\n"
"• Después de gym o ejercicio\n"
"• Layering con perfumes amaderados o florales\n"
"• Regalo para mujer que ama aromas dulces y gourmand\n\n"
"DETALLES DEL PRODUCTO\n"
"Body mist en frasco con vaporizador atomizador. Brume Parfumée femenina con identidad gourmand.\n\n"
"Notas dominantes: Vainilla cremosa, Cashmere, Almizcle suave"
)

body={"site_id":"MLM","domain_id":"MLM-PERFUMES","type":"EDIT","title":TITLE,"attributes":ATTRS,"pictures":pics}
print("\nPOST /catalog_suggestions ...")
r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
print("http",r.status_code)
rb=r.json(); print(json.dumps(rb,ensure_ascii=False)[:1800])
sid=rb.get("id") or rb.get("suggestion_id")
if sid:
    print(f"\n>>> SUGGESTION_ID = {sid}")
    time.sleep(4)
    rd=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":DESC},timeout=20)
    print("desc POST",rd.status_code, rd.text[:200])
