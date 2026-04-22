import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Go 4 activas
GO4=[
    ("MLM5227773714","Negra"),
    ("MLM5223451400","Rosa"),
    ("MLM5223214798","Azul Marino"),
    ("MLM2880763019","Roja"),
    ("MLM2880762615","Camuflaje"),
]

def seo_title(color):
    # Max 60 char, alta densidad keywords
    return f"Bocina Jbl Go 4 Bluetooth Portatil {color} Ip67 Nueva"[:60]

def seo_desc(color):
    return f"""Bocina JBL Go 4 Bluetooth Portatil - Color {color} - NUEVA Original con Factura

===== POR QUE NUESTRO PRECIO ES MAS BAJO QUE OTROS VENDEDORES =====

Nuestras bocinas JBL Go 4 son version de fabrica autorizada (Original Manufacturer Edition) con HARDWARE 100% identico al retail oficial. La diferencia es que vienen con FIRMWARE independiente de JBL Inc., optimizado por la comercializadora en fabrica. Este firmware:
- NO esta registrado en los servidores de autenticacion de la app oficial JBL Portable
- Por eso la app oficial JBL Portable (descargable de Play Store / App Store) NO reconoce este modelo y no puede administrarlo
- El audio, Bluetooth, codecs, bateria y todas las funciones fisicas operan al 100% identico al modelo retail
- Compatible con cualquier dispositivo via Bluetooth estandar sin necesidad de app

Si tu unico uso de la bocina es con la app oficial JBL, considera esta informacion antes de comprar.

===== CARACTERISTICAS TECNICAS JBL GO 4 =====

- Sonido JBL PRO Sound potente y claro
- Bateria de 7 horas de reproduccion continua
- Resistencia certificada al agua y polvo IP67
- Potencia de salida 4.2 W RMS
- Peso 190 g ultraligero
- Bluetooth 5.3 con alcance hasta 10 metros
- AI Sound Boost para adaptar el audio al espacio
- Correa integrada para llevar o colgar
- Carga rapida USB tipo C

===== INCLUYE EN LA CAJA ORIGINAL =====

- 1 x Bocina JBL Go 4 color {color}
- 1 x Caja original sellada
- 1 x Cable de carga USB-C
- 1 x Manual de usuario
- 1 x Guia rapida de uso
- 1 x Factura fiscal

===== GARANTIA Y ENVIO =====

- Producto 100% NUEVO sin uso en caja original
- Factura incluida en cada compra
- Garantia de 30 dias con nosotros contra defectos de fabrica
- Envio GRATIS a todo Mexico via Mercado Envios
- Envio el mismo dia si compras antes de las 2 PM (L-V)
- Entrega en 24 a 72 hrs habiles

===== COMPATIBILIDAD AMPLIA =====

Funciona perfecto con cualquier dispositivo que tenga Bluetooth estandar: iPhone (iOS), Android (Samsung, Xiaomi, Motorola, Huawei, Oppo, OnePlus), iPad, tablets, laptops Windows / Mac, Smart TVs, consolas de videojuegos, car audio.

===== PREGUNTAS FRECUENTES =====

- ¿Es original JBL? Si, hardware 100% original de fabrica con factura.
- ¿Funciona con la app JBL Portable? NO, por tener firmware independiente sin registro en servidores oficiales JBL.
- ¿Tiene garantia? Si, 30 dias con nosotros ante defecto de funcionamiento.
- ¿Factura? Si, fiscal con cada pedido.
- ¿Envio a todo Mexico? Si, gratis via Mercado Envios.

===== PALABRAS CLAVE SEO =====

bocina jbl go 4, altavoz bluetooth portatil, parlante jbl go4, bocina {color.lower()}, jbl bluetooth nueva, bocina waterproof ip67, bocina impermeable, bocina inalambrica, jbl original, jbl con factura, bocina alberca, bocina playa, bocina exterior, bocina fiesta, regalo bocina, bocina pequeña, bocina potente, bocina portatil, bocina go 4, jbl go 4 {color.lower()}.

Preguntanos cualquier duda antes de comprar. Respondemos en minutos y enviamos rapido el mismo dia."""

ok=0; err=0
for iid,color in GO4:
    # Update title
    new_title=seo_title(color)
    rt=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"title":new_title},timeout=15)
    print(f"  {iid} title: {rt.status_code}")
    time.sleep(0.5)
    # Update description
    rd=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":seo_desc(color)},timeout=15)
    if rd.status_code in (200,201):
        print(f"  {iid} desc OK")
        ok+=1
    else:
        print(f"  {iid} desc ERR: {rd.status_code} {rd.text[:120]}")
        err+=1
    time.sleep(0.5)

print(f"\n=== {ok} OK, {err} ERR ===")

# Actualizar qa_templates.json con el template de "por que no compatible firmware"
with open("qa_templates.json") as f: cfg=json.load(f)
new_template={
    "id":"auto_oem_firmware",
    "keywords":[
        "por que no se conecta","porque no se conecta","por que no es compatible","porque no es compatible",
        "por que no funciona la app","porque no funciona la app","por que no reconoce","porque no reconoce",
        "porque no la detecta","por que no la detecta","firmware","no aparece en la app",
        "no conecta con la app","no se empareja con la app","por que no puede conectar","porque no puede conectar"
    ],
    "response":"Hola! La razon es que nuestras bocinas JBL son version de fabrica autorizada con FIRMWARE independiente de JBL Inc. Este firmware no esta registrado en los servidores de autenticacion de la app oficial JBL Portable, por eso la app no las reconoce ni puede administrarlas. El hardware es 100% identico al retail (audio, bateria, bluetooth, codecs, resistencia al agua). Funciona perfecto via Bluetooth estandar con cualquier dispositivo (iPhone, Android, Samsung, etc). Factura y garantia 30 dias. Saludos!"
}
# replace si existe id
cfg["templates"]=[t for t in cfg["templates"] if t.get("id")!="auto_oem_firmware"]
cfg["templates"].append(new_template)
with open("qa_templates.json","w") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)
print("qa_templates.json: auto_oem_firmware agregado")
