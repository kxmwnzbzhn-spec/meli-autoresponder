import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# sin emojis, ASCII puro, bien formateado
DESC_TPL="""BOCINA BLUETOOTH PORTATIL SUMERGIBLE IP67 - COLOR {COLOR}

CARACTERISTICAS PRINCIPALES:
- Sonido potente 35W RMS con graves profundos
- Bateria 16 horas de uso continuo
- Resistente al agua y polvo IP67 (alberca, playa, lluvia)
- Bluetooth 5.3 estable hasta 15 metros
- Manos libres para contestar llamadas
- Microfono integrado de alta calidad
- Botones fisicos de control de volumen y reproduccion

QUE INCLUYE:
- Bocina
- Cable USB-C de carga
- Manual de usuario

OTROS COLORES DISPONIBLES:
Negro, Azul, Rojo, Morado

GARANTIA:
30 dias por defectos de fabrica. Producto nuevo en caja original sellada.

ENVIO:
GRATIS. Llega en 24 a 48 horas habiles."""

IDS={"Azul":"MLM5233454100","Rojo":"MLM2886030837","Morado":"MLM2886136351","Negro":"MLM5233480022"}

for color,iid in IDS.items():
    body={"plain_text":DESC_TPL.format(COLOR=color)}
    # primer intento: PUT (actualiza descripcion existente o crea)
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json=body,timeout=15)
    if rp.status_code not in (200,201):
        # si no, intenta POST (crea nueva)
        rp=requests.post(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json=body,timeout=15)
    print(f"{color} {iid}: {rp.status_code}")
    if rp.status_code not in (200,201):
        print(f"  err: {rp.text[:400]}")
    time.sleep(1)
