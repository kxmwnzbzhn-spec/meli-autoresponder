import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Get source pictures from the catalog product (not the new item since it has no own pics)
src=requests.get("https://api.mercadolibre.com/products/MLM49608224",headers=H).json()
pic_urls=[(p.get("url") or p.get("secure_url")) for p in (src.get("pictures") or [])][:8]
print(f"source pics: {len(pic_urls)}")
for u in pic_urls[:3]: print(f"  {u}")

# Upload via multipart
def upload(url):
    img=requests.get(url,timeout=20)
    if img.status_code!=200: return None
    files={"file":("pic.jpg",img.content,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",
                    headers={"Authorization":f"Bearer {T}"}, files=files)
    return r.json().get("id") if r.status_code<300 else None

pic_ids=[]
for u in pic_urls:
    pid=upload(u)
    if pid: pic_ids.append(pid)
print(f"uploaded: {len(pic_ids)} pics")

SEO_TITLE="Bocina Bluetooth Portatil Charge 6 Espejo Ip67 30w"
SEO_DESC = """BOCINA BLUETOOTH PORTATIL CHARGE 6 - CALIDAD ESPEJO 1:1
Producto remanufacturado de excelente calidad. No es original JBL.

ESPECIFICACIONES TECNICAS:
- Conexion Bluetooth 5.3 de largo alcance (hasta 12 metros)
- Resistencia IP67: sumergible y a prueba de polvo
- Bateria recargable de 28 horas de reproduccion continua
- Potencia total 40W RMS - graves profundos y agudos cristalinos
- Puerto de carga USB-C de alta velocidad
- Diseno robusto con correa de transporte
- Funcion power bank para cargar otros dispositivos
- Compatible con asistentes de voz vinculados al telefono

CONTENIDO DEL EMPAQUE:
- 1 bocina bluetooth portatil
- 1 cable USB-C de carga
- 1 manual de usuario
- Empaque protector

AVISO IMPORTANTE PARA EL COMPRADOR:
- Producto CALIDAD ESPEJO 1:1: replica fiel del modelo original
- NO es producto original de la marca JBL
- NO es compatible con la aplicacion JBL Portable
- Condicion: REMANUFACTURADO - revisado y reacondicionado a estandares de fabrica
- Calidad de sonido y construccion equivalentes al original
- Acabados premium en todos los detalles

GARANTIA Y SERVICIO:
- Garantia del vendedor por 30 dias contra defectos de fabrica
- Soporte al cliente personalizado via mensajes Mercado Libre
- Devoluciones aceptadas segun politicas Mercado Libre

USOS RECOMENDADOS:
Ideal para fiestas, reuniones, playa, alberca, ducha, camping, gimnasio, oficina, viajes, regalos. Compatible con cualquier dispositivo con Bluetooth: celulares Android, iPhone, tabletas, laptops Windows, Mac, Smart TVs.

ENVIO GRATIS a todo Mexico via Mercado Envios. Despacho en 24 a 48 horas habiles desde nuestro almacen en Mexico.

Bocina Bluetooth, Bocina Portatil, Speaker Portatil, Altavoz, Charge Bluetooth, Bocina Inalambrica, Bluetooth Speaker, Altavoz Resistente al Agua, IP67, 40W, Sumergible, Bocina Recargable, Charge 6, Bocina Charge"""

body={
    "title": SEO_TITLE,
    "category_id": "MLM59800",
    "price": 799,
    "currency_id": "MXN",
    "available_quantity": 1,
    "buying_mode": "buy_it_now",
    "listing_type_id": "gold_pro",
    "condition": "used",
    "pictures": [{"id":pid} for pid in pic_ids],
    "attributes": [
        {"id":"BRAND","value_name":"Genérica"},
        {"id":"MODEL","value_name":"Charge 6 Espejo"},
        
    ],
    "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"drop_off"},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ]
}
print("\n--- POSTING ---")
r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
print(f"POST http={r.status_code}")
if r.status_code<300:
    new=r.json()
    nid=new.get("id")
    print(f"NEW_ID={nid} price=${new.get('price')} status={new.get('status')} condition={new.get('condition')}")
    print(f"link=https://articulo.mercadolibre.com.mx/{nid}")
    d=requests.put(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":SEO_DESC})
    if d.status_code>=300:
        d=requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":SEO_DESC})
    print(f"DESC http={d.status_code}")
else:
    print(f"ERR: {r.text[:1200]}")
