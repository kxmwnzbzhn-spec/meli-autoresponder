"""
Crear catalog_suggestion FLOFEN Bare Vanilla (Attessa´s Secret) body mist 250ml en MLM-PERFUMES.
Sube las 5 fotos (en scripts/assets/flofen_vainilla/) a MELI, construye body con SEO optimizado.
"""
import os, json, hashlib, pathlib, requests, meli_token

API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
print("ASVA uid:",me.get("id"))

ASSETS=pathlib.Path("scripts/assets/flofen_vainilla")
PHOTOS=["01_portada.png","02_vanilla_pods.png","03_lifestyle.png","04_splash.png","05_label.png"]

pics=[]
for f in PHOTOS:
    p=ASSETS/f
    if not p.exists():
        print(f"  ⚠ falta {p}"); continue
    img=p.read_bytes()
    rp=requests.post(f"{API}/pictures/items/upload",headers=H,
        files={"file":(f,img,"image/png")},timeout=120)
    print(f"  pic {f}: {rp.status_code}")
    if rp.status_code in (200,201):
        pics.append({"id":rp.json()["id"]})
    else:
        print("    ",rp.text[:200])
print(f"\nfotos subidas: {len(pics)}/{len(PHOTOS)}")

# EAN-13 interno
h=hashlib.md5("attessa secret::flofen::bare vanilla".encode()).hexdigest()
nine="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
b="290"+nine; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
EAN=b+str((10-(s%10))%10); print("EAN:",EAN)

TITLE=("Body Mist Flofen Bare Vanilla Attessa´s Secret Fragrance Mist 250ml | "
       "Vainilla Cremosa Cashmere Almizcle Dulce Mujer Brume Parfumée")

ATTRS=[
 {"id":"BRAND","values":[{"name":"Attessa´s Secret"}]},
 {"id":"LINE","values":[{"name":"Flofen"}]},
 {"id":"PERFUME_NAME","values":[{"name":"Bare Vanilla"}]},
 {"id":"GENDER","values":[{"name":"Mujer"}]},
 {"id":"PERFUME_TYPE","values":[{"name":"Splash"}]},
 {"id":"APPLICATION_FORMAT","values":[{"name":"Spray"}]},
 {"id":"IS_REFILLABLE","values":[{"name":"No"}]},
 {"id":"UNIT_VOLUME","values":[{"name":"250 mL"}]},
 {"id":"OLFACTORY_FAMILIES","values":[{"name":"Gourmand"}]},
 {"id":"GTIN","values":[{"name":EAN}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]

DESC=(
"Flofen Bare Vanilla de Attessa´s Secret es un body mist femenino que envuelve la piel con una caricia cálida "
"de vainilla cremosa y un fondo aterciopelado de almizcle tipo cashmere. Una fragancia corporal dulce, sensual "
"y ligera, ideal para uso diario, para reaplicar durante el día y para acompañar tu rutina de cuidado personal.\n\n"
"CARACTERÍSTICAS PRINCIPALES\n"
"• Marca: Attessa´s Secret\n"
"• Línea: Flofen\n"
"• Variante: Bare Vanilla\n"
"• Tipo: Body Mist / Fragrance Mist (Brume Parfumée)\n"
"• Concentración: Splash (ligera, refrescante)\n"
"• Formato: Spray\n"
"• Volumen: 250 ml (8.4 fl oz)\n"
"• Género: Femenino\n"
"• Familia olfativa: Gourmand\n\n"
"PIRÁMIDE OLFATIVA\n"
"• Notas dominantes: Whipped Vanilla (vainilla cremosa batida)\n"
"• Notas envolventes: Soft Cashmere (almizcle suave aterciopelado)\n"
"• Sensación: Skin to Skin — cálida, íntima y cercana a la piel\n\n"
"¿POR QUÉ ELEGIR FLOFEN BARE VANILLA?\n"
"• Aroma dulce y reconfortante con identidad gourmand\n"
"• Fórmula ligera ideal para reaplicar durante el día sin saturar\n"
"• Frasco generoso de 250 ml con vaporizador para mayor rendimiento\n"
"• Perfecto para uso casual, oficina, escuela, gym y noches relajadas\n\n"
"CASOS DE USO\n"
"• Uso diario después del baño o ducha\n"
"• Refresco rápido durante el día\n"
"• Después de actividad física o gym\n"
"• Capa base para layering con perfumes amaderados o florales\n"
"• Regalo para mujer amante de aromas dulces y gourmand\n\n"
"DETALLES DEL PRODUCTO\n"
"Body mist en frasco con vaporizador atomizador. Aroma envolvente de vainilla cremosa y almizcle cashmere, "
"ideal para mujer. Presentación elegante con etiqueta dorada.\n\n"
"Familia olfativa principal: Gourmand\n"
"Notas dominantes: Vainilla, Cashmere, Almizcle suave"
)

body={"site_id":"MLM","domain_id":"MLM-PERFUMES","type":"EDIT","title":TITLE,"attributes":ATTRS,"pictures":pics}
print("\nPOST /catalog_suggestions ...")
r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
print("http",r.status_code)
rb=r.json()
print(json.dumps(rb,ensure_ascii=False)[:2000])
sid=rb.get("id") or rb.get("suggestion_id")
if sid:
    print(f"\n>>> SUGGESTION_ID = {sid}")
    rd=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":DESC},timeout=20)
    print("descripción POST",rd.status_code, rd.text[:200])
