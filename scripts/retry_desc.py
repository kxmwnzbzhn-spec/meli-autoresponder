import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

ITEMS=[
    ("MLM5223451400","Go 4","Rosa"),
    ("MLM2880762615","Go 4","Camuflaje"),
]
SPEC={"Go 4":{"bat":"7 horas","power":"4.2 W","ip":"IP67","weight":"190 g","extras":"Tamano bolsillo. AI Sound Boost. Correa integrada."}}

def seo_desc(model,color):
    s=SPEC.get(model,{})
    return f"""Bocina JBL {model} Bluetooth Portatil - Color {color} - Producto NUEVO OEM con Factura

AVISO IMPORTANTE: Version OEM (misma fabrica sin licencia retail oficial de JBL). Hardware identico al modelo retail. NO es compatible con la app oficial JBL Portable.

CARACTERISTICAS: Sonido JBL PRO Sound, bateria {s['bat']}, IP67, potencia {s['power']}, peso {s['weight']}, Bluetooth 5.3. {s['extras']}

INCLUYE: Bocina JBL {model} {color}, cable USB-C, caja generica, guia.

NO INCLUYE: empaque retail JBL, compatibilidad con app oficial JBL Portable.

GARANTIA: 30 dias. Envio GRATIS todo Mexico. Entrega 24-72 hrs.

COMPATIBILIDAD: iPhone, Android, Samsung, Xiaomi, tablets, laptops via Bluetooth.

Palabras clave: bocina jbl, altavoz bluetooth, jbl {model.lower()} {color.lower()}, oem, waterproof, impermeable, inalambrica, nueva, factura."""

for iid,m,c in ITEMS:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":seo_desc(m,c)},timeout=15)
    print(f"{iid}: {r.status_code} {r.text[:100]}")
    time.sleep(1)
