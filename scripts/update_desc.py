import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Todas las JBL activas + pending_documentation (no Sony)
ITEMS=[
    ("MLM2880763001","Charge 6","Azul"),
    ("MLM2880774951","Charge 6","Roja"),
    ("MLM2880762579","Charge 6","Camuflaje"),
    ("MLM2880803051","Charge 6","Negra"),
    ("MLM5223214318","Flip 7","Roja"),
    ("MLM2880754185","Flip 7","Negra"),
    ("MLM2880758743","Flip 7","Morada"),
    ("MLM2880762535","Clip 5","Morada"),
    ("MLM2880766045","Clip 5","Negra"),
    ("MLM2880754229","Clip 5","Rosa"),
    ("MLM2880794089","Grip","Negra"),
    ("MLM2880762595","Go Essential 2","Azul"),
    ("MLM2880775007","Go Essential 2","Roja"),
    ("MLM2880766117","Go 4","Negra"),
    ("MLM2880763019","Go 4","Roja"),
    ("MLM5223451400","Go 4","Rosa"),
    ("MLM5223214798","Go 4","Azul Marino"),
    ("MLM2880762615","Go 4","Camuflaje"),
    ("MLM2880774949","Go 3","Negra"),
]

SPEC={
    "Charge 6": {"bat":"28 horas","power":"40 W","ip":"IP68","weight":"970 g","extras":"Powerbank integrada de 5V/3A para cargar tu telefono. AURACAST para conectar multiples bocinas. Modo Playtime Boost +4 hrs."},
    "Flip 7":   {"bat":"16 horas","power":"35 W","ip":"IP68","weight":"560 g","extras":"AI Sound Boost para adaptar el audio al ambiente. AURACAST multi-bocina. Playtime Boost +2 hrs."},
    "Clip 5":   {"bat":"12 horas","power":"7 W",  "ip":"IP67","weight":"285 g","extras":"Mosqueton integrado para llevar donde quieras. AURACAST para sincronizar con otras bocinas."},
    "Grip":     {"bat":"12 horas","power":"8 W",  "ip":"IP68","weight":"400 g","extras":"Iluminacion LED dinamica sincronizada al ritmo de la musica. Forma pensada para agarrar con una mano."},
    "Go 4":     {"bat":"7 horas", "power":"4.2 W","ip":"IP67","weight":"190 g","extras":"Tamano bolsillo. AI Sound Boost. Correa integrada para llevar donde sea."},
    "Go Essential 2": {"bat":"7 horas","power":"3.1 W","ip":"IPX7","weight":"200 g","extras":"Edicion esencial con Bluetooth 5.1. Clip integrado para colgar."},
    "Go 3":     {"bat":"5 horas", "power":"4.2 W","ip":"IP67","weight":"209 g","extras":"Diseno iconico JBL con cuerda integrada para colgar. Resistente al agua y polvo."},
}

def seo_desc(model, color):
    s=SPEC.get(model,{})
    return f"""Bocina JBL {model} Bluetooth Portatil - Color {color} - Producto NUEVO OEM con Factura

AVISO IMPORTANTE: Version OEM (Original Equipment Manufacturer, misma fabrica sin empaque/licencia retail oficial de JBL). El hardware y la calidad de audio son identicos al modelo retail oficial, pero con las siguientes diferencias: NO es compatible con la app oficial JBL Portable, no incluye empaque retail con licencia de marca, se entrega en caja generica de proteccion. Funciona al 100% con cualquier dispositivo via Bluetooth estandar.

CARACTERISTICAS TECNICAS:
- Sonido JBL PRO Sound potente y claro
- Bateria de {s.get('bat','')} de reproduccion continua
- Resistencia certificada al agua y polvo {s.get('ip','')}
- Potencia de salida {s.get('power','')}
- Peso ligero de {s.get('weight','')} ideal para llevar
- Bluetooth 5.3 con alcance hasta 10 metros
- {s.get('extras','')}

INCLUYE EN EL PAQUETE:
- 1 x Bocina JBL {model} color {color}
- 1 x Cable de carga USB-C
- 1 x Caja generica de proteccion (no retail oficial)
- 1 x Guia rapida de uso

NO INCLUYE:
- Empaque retail oficial de JBL
- Compatibilidad con la app oficial JBL Portable
- Accesorios opcionales de la version retail

CONDICIONES DE VENTA:
- Producto NUEVO sin uso en caja generica
- Factura incluida con cada compra
- Garantia de 30 dias por nosotros contra defectos de fabrica
- Envio GRATIS a todo Mexico via Mercado Envios
- Envio el mismo dia si compras antes de las 2 PM (L-V)
- Entrega en 24 a 72 hrs habiles en toda Republica Mexicana

COMPATIBILIDAD:
Funciona perfecto con cualquier dispositivo que tenga Bluetooth estandar: iPhone (iOS), Android (Samsung, Xiaomi, Motorola, Huawei, Oppo, OnePlus), iPad, tablets, laptops Windows/Mac, Smart TVs, consolas, y cualquier otro equipo Bluetooth.

PREGUNTAS FRECUENTES:
- Es original JBL? Es version OEM del fabricante original, hardware identico al retail, sin licencia de marca oficial.
- Tiene garantia? Si, 30 dias con nosotros ante cualquier defecto.
- Funciona con la app JBL Portable? NO, por ser version OEM no es compatible con la app oficial.
- Factura? Si, enviamos factura fiscal con cada pedido.
- Envio a mi ciudad? Si, enviamos gratis a toda Republica Mexicana.

PALABRAS CLAVE PARA BUSQUEDA:
bocina jbl, altavoz bluetooth, parlante portatil, jbl {model.lower()}, bocina {color.lower()}, bluetooth portatil, bocina waterproof, bocina impermeable, bocina inalambrica, jbl oem, bocina nueva con factura, jbl {model.lower()} {color.lower()}, bocina economica, bocina fiesta, bocina exterior, regalo bocina, bocina playa, bocina alberca, bocina potente, bocina bajos, sonido pro.

Preguntanos cualquier duda antes de comprar. Respondemos en minutos y enviamos rapido."""

ok=0; err=0
for iid,model,color in ITEMS:
    desc=seo_desc(model,color)
    # Intentar primero POST (crear), si falla porque ya existe, PUT (actualizar)
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":desc},timeout=15)
    if r.status_code in (200,201):
        print(f"OK {iid} [{model} {color}]")
        ok+=1
    else:
        print(f"ERR {iid} [{model} {color}]: {r.status_code} {r.text[:150]}")
        err+=1
    time.sleep(0.8)

print(f"\nTotal: {ok} OK, {err} ERR")
