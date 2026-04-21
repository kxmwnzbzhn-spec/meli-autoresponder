import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# === PARTE 1: Actualizar descripciones JBL corregidas (caja original SI, app NO) ===
JBL_ITEMS=[
    ("MLM2880763001","Charge 6","Azul"),("MLM2880774951","Charge 6","Roja"),
    ("MLM2880762579","Charge 6","Camuflaje"),("MLM2880803051","Charge 6","Negra"),
    ("MLM5223214318","Flip 7","Roja"),("MLM2880762535","Clip 5","Morada"),
    ("MLM2880794089","Grip","Negra"),("MLM2880762595","Go Essential 2","Azul"),
    ("MLM2880775007","Go Essential 2","Roja"),("MLM2880763019","Go 4","Roja"),
    ("MLM5223451400","Go 4","Rosa"),("MLM5223214798","Go 4","Azul Marino"),
    ("MLM2880774949","Go 3","Negra"),
]
SPEC={
    "Charge 6":{"bat":"28 horas","power":"40 W","ip":"IP68","weight":"970 g","extras":"Powerbank integrada para cargar tu telefono. AURACAST multi-bocina. Playtime Boost +4 hrs."},
    "Flip 7":{"bat":"16 horas","power":"35 W","ip":"IP68","weight":"560 g","extras":"AI Sound Boost. AURACAST. Playtime Boost +2 hrs."},
    "Clip 5":{"bat":"12 horas","power":"7 W","ip":"IP67","weight":"285 g","extras":"Mosqueton integrado para llevar donde quieras. AURACAST."},
    "Grip":{"bat":"12 horas","power":"8 W","ip":"IP68","weight":"400 g","extras":"Iluminacion LED dinamica sincronizada con la musica."},
    "Go 4":{"bat":"7 horas","power":"4.2 W","ip":"IP67","weight":"190 g","extras":"AI Sound Boost. Correa integrada."},
    "Go Essential 2":{"bat":"7 horas","power":"3.1 W","ip":"IPX7","weight":"200 g","extras":"Bluetooth 5.1. Clip integrado."},
    "Go 3":{"bat":"5 horas","power":"4.2 W","ip":"IP67","weight":"209 g","extras":"Diseno iconico con cuerda integrada."},
}

def jbl_desc(model, color):
    s=SPEC.get(model,{})
    return f"""Bocina JBL {model} Bluetooth Portatil - Color {color} - Producto NUEVO con caja original y factura

AVISO DE COMPATIBILIDAD: Este modelo NO es compatible con la aplicacion oficial "JBL Portable". Funciona al 100% via Bluetooth estandar con cualquier dispositivo. Si tu unico interes es usar la app oficial JBL Portable, considera antes de comprar.

CARACTERISTICAS TECNICAS:
- Sonido JBL PRO Sound potente y claro
- Bateria de {s.get('bat','')} de reproduccion continua
- Resistencia certificada al agua y polvo {s.get('ip','')}
- Potencia de salida {s.get('power','')}
- Peso de {s.get('weight','')} ideal para llevar
- Bluetooth 5.3 con alcance hasta 10 metros
- {s.get('extras','')}

INCLUYE EN LA CAJA ORIGINAL:
- 1 x Bocina JBL {model} color {color} NUEVA
- 1 x Caja original JBL sellada
- 1 x Cable de carga USB-C
- 1 x Guia rapida de uso
- 1 x Factura oficial

CONDICIONES DE VENTA:
- Producto 100% NUEVO sin uso, en caja original sellada
- Factura incluida con cada compra
- Garantia de 30 dias con nosotros contra defectos de fabrica
- Envio GRATIS a todo Mexico via Mercado Envios
- Envio mismo dia si compras antes de las 2 PM (L-V)
- Entrega en 24-72 hrs habiles en toda la Republica Mexicana

COMPATIBILIDAD:
Funciona con cualquier dispositivo con Bluetooth estandar: iPhone (iOS), Android (Samsung, Xiaomi, Motorola, Huawei, Oppo, OnePlus), iPad, tablets, laptops Windows/Mac, Smart TVs, consolas, etc.

PREGUNTAS FRECUENTES:
- Viene con caja original? Si, en caja original sellada JBL con todos los accesorios.
- Tiene garantia? Si, 30 dias con nosotros ante cualquier defecto de fabrica.
- Funciona con la app JBL Portable? NO, este modelo no es compatible con la app oficial.
- Factura? Si, factura fiscal incluida.
- Envio a mi ciudad? Si, enviamos gratis a toda Republica Mexicana.

PALABRAS CLAVE:
bocina jbl, altavoz bluetooth, parlante portatil, jbl {model.lower()}, bocina {color.lower()}, bluetooth portatil, bocina waterproof, bocina impermeable, bocina inalambrica, jbl nueva original, bocina con factura, bocina garantia, jbl {model.lower()} {color.lower()}.

Preguntanos cualquier duda antes de comprar. Respondemos en minutos."""

print("=== JBL descriptions ===")
ok=err=0
for iid,m,c in JBL_ITEMS:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":jbl_desc(m,c)},timeout=15)
    if r.status_code in (200,201): ok+=1; print(f"  OK {iid} [{m} {c}]")
    else: err+=1; print(f"  ERR {iid}: {r.text[:100]}")
    time.sleep(0.6)
print(f"JBL desc: {ok} OK, {err} ERR")

# === PARTE 2: Descripciones BLINDADAS para perfumes ===
# Primero traer lista de perfumes activos
sid=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()["id"]
ids=[]; s=0
while True:
    d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status=active&limit=100&offset={s}",headers=H).json()
    got=d.get("results",[])
    if not got: break
    ids+=got; s+=100
    if s>=d.get("paging",{}).get("total",0): break

perfumes=[]
for i in range(0,len(ids),20):
    b=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={b}&attributes=id,title,category_id",headers=H).json()
    for x in res:
        b2=x.get("body",{})
        if b2.get("category_id","").startswith("MLM1271") or "perfume" in (b2.get("title") or "").lower() or "edp" in (b2.get("title") or "").lower() or "eau de" in (b2.get("title") or "").lower():
            perfumes.append(b2)
print(f"\n=== Perfumes: {len(perfumes)} ===")

BLINDADO="""

===== AVISO IMPORTANTE PARA EL COMPRADOR (Lee antes de comprar) =====

Este perfume es 100% ORIGINAL, adquirido por medio de comercializadora autorizada con factura fiscal. Antes de comprar, entiende lo siguiente:

SOBRE LA PERCEPCION DEL AROMA:
- La duracion y proyeccion de un perfume son SUBJETIVAS y dependen de factores personales: tipo de piel (seca, grasa, normal), pH del cuerpo, temperatura ambiente, dieta, medicamentos, estres, ejercicio, humedad del aire.
- Un mismo perfume huele distinto en dos personas. No podemos garantizar una duracion especifica de horas ya que varia persona a persona.
- Si tu nariz es sensible a cambios de formula del fabricante, considera que las marcas reformulan sus productos periodicamente. Lo que compraste hace 2 anos puede tener un dry-down ligeramente distinto al actual.

SOBRE LA ORIGINALIDAD:
- Todos nuestros perfumes vienen en empaque de fabrica con los sellos y codigos originales. El producto sale directo de la comercializadora autorizada.
- Presentamos FACTURA FISCAL con cada venta como prueba de trazabilidad del origen autorizado.
- La variacion en el tono del jugo, la textura del frasco o pequenas diferencias en serigrafia entre lotes de fabrica NO son defecto ni producto falso. Las casas perfumeras producen por lotes y estos pueden variar.
- Si tienes dudas sobre originalidad, te invitamos a verificar el codigo batch en la base de datos de la marca. No aceptamos reclamos basados en "me dijeron que no huele igual" sin comprobante oficial del fabricante.

SOBRE ALMACENAMIENTO:
- Los perfumes son sensibles a la luz directa, calor y oscilaciones de temperatura. Antes de comprar, considera que si dejas el frasco en el carro al sol o cerca de la ventana, el jugo puede oxidarse y degradarse. Esto NO es defecto de fabrica.
- Almacena en lugar fresco, seco y oscuro. Idealmente entre 15 y 22 grados Celsius.

POLITICA DE RECLAMOS:
- Aceptamos reclamos unicamente por: producto danado en envio (frasco quebrado, caja reventada), producto diferente al anunciado, producto no entregado.
- NO se aceptan reclamos por: percepcion subjetiva de aroma ("no me dura", "no es el que recordaba", "huele distinto"), cambios en formula del fabricante, variaciones de lote, preferencias personales, cambio de opinion despues de usarlo.
- El comprador se compromete a revisar el producto en las primeras 24 horas y abrir reclamo SOLO si aplica bajo las causales indicadas arriba.
- Reclamos despues de 7 dias de recibido no proceden.

GARANTIA:
- Cambios y devoluciones aplican unicamente si el producto llega en mal estado o es diferente al publicado. Si aplicamos cambio por defecto de envio, requerimos video sin cortes del desempaque desde la caja de Mercado Envios intacta.

Al hacer la compra, aceptas estas condiciones de venta."""

PERF_SEO_TEMPLATE="""{old}

{blindado}

PALABRAS CLAVE: {kw}"""

# Traer descripcion actual de cada perfume y AGREGAR el blindaje al final (sin borrar contenido util)
ok=err=0
for p in perfumes:
    iid=p["id"]
    title=p.get("title","")
    # Obtener descripcion actual
    rd=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,timeout=15)
    cur=""
    if rd.status_code==200:
        try: cur=rd.json().get("plain_text","")
        except: cur=""
    # Detectar si ya tiene el blindaje
    if "AVISO IMPORTANTE PARA EL COMPRADOR" in cur:
        print(f"  SKIP {iid} (ya tiene blindaje)")
        continue
    # SEO keywords dinamicas
    kw_base="perfume original, edp, eau de parfum, perfume lujo, regalo perfume, perfume mujer, perfume hombre, perfume unisex, fragancia original, perfume con factura, envio gratis"
    newdesc = (cur or f"Perfume 100% original - {title}") + BLINDADO + f"\n\nPALABRAS CLAVE: {kw_base}"
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":newdesc[:19999]},timeout=15)
    if r.status_code in (200,201): ok+=1; print(f"  OK {iid} | {title[:50]}")
    else: err+=1; print(f"  ERR {iid}: {r.text[:100]}")
    time.sleep(0.5)
print(f"\nPerfumes blindado: {ok} OK, {err} ERR")
