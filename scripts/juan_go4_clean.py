import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

IID="MLM2883448187"

# Descripcion profesional con disclaimers CLAROS pero bien presentados
DESC="""BOCINA JBL GO 4 BLUETOOTH PORTATIL IP67 - NUEVA EN CAJA

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 estable hasta 10 metros
- Resistente al agua y polvo grado IP67 (alberca, playa, lluvia)
- Bateria recargable con autonomia hasta 7 horas
- Sonido potente JBL Pro Sound
- Manos libres con microfono integrado
- Puerto USB-C para carga rapida
- 6 colores disponibles: Negro, Azul, Rojo, Rosa, Camuflaje, Aqua

INFORMACION IMPORTANTE DEL PRODUCTO:

- Este modelo NO es compatible con la aplicacion JBL Portable ni con Auracast. Funciona como bocina Bluetooth estandar, un dispositivo a la vez.
- Producto de importacion. No cuenta con respaldo ni garantia directa del distribuidor oficial JBL Mexico (Harman Mexico). La garantia aplicable es la que ofrece el vendedor directamente.
- Al finalizar la compra, el comprador declara haber leido y aceptado las caracteristicas y limitaciones descritas en esta publicacion.

GARANTIA DEL VENDEDOR:
- 30 dias contra defectos de fabricacion comprobables con video
- No cubre: danos por agua en exceso, caidas, mal uso, desgaste estetico normal
- Para tramitar: enviar video del defecto + numero de orden

POLITICA DE DEVOLUCIONES:
- Se aceptan devoluciones por defecto de fabrica comprobado dentro de los primeros 30 dias
- No se aceptan devoluciones por cambio de opinion
- No se aceptan reclamos por caracteristicas tecnicas ya informadas en esta descripcion (compatibilidad con app, origen de importacion, etc.)
- Toda devolucion requiere producto + empaque + accesorios completos sin danos

QUE INCLUYE EL EMPAQUE:
- 1 Bocina JBL Go 4
- 1 Cable USB-C
- Documentacion del empaque original

ENVIO GRATIS - Despacho en 24 horas habiles - Entrega estimada 2 a 5 dias segun zona.

Gracias por su compra."""

rd=requests.put(f"https://api.mercadolibre.com/items/{IID}/description",headers=H,json={"plain_text":DESC},timeout=30)
print(f"desc update: {rd.status_code}")
if rd.status_code not in (200,201):
    print(f"  err: {rd.text[:500]}")
else:
    print(f"  longitud: {len(DESC)} chars")
