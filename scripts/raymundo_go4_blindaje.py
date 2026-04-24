import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

IID="MLM5235542250"

DESC="""BOCINA JBL GO 4 BLUETOOTH PORTATIL IP67 - USADA EN EXCELENTE ESTADO

═══════════════════════════════════════════
INFORMACION TECNICA IMPORTANTE - LEA ANTES DE COMPRAR
═══════════════════════════════════════════

COMPATIBILIDAD DEL MODELO JBL GO 4:
- Este modelo NO es compatible con la aplicacion JBL Portable.
- Este modelo NO es compatible con Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- No requiere instalacion de aplicacion movil para su funcionamiento.
- Al comprar usted declara haber leido y aceptado expresamente estas caracteristicas tecnicas.

ESTADO DEL PRODUCTO:
- Vendido como USADO en excelente estado de funcionamiento.
- Producto 100% original JBL con caja original, numero de serie SN verificable y codigos UPC/EAN oficiales Harman/JBL impresos en el empaque.
- Puede presentar marcas MINIMAS de uso normal por tratarse de un producto usado.
- Probado y funcionando al 100% antes del envio.

CARACTERISTICAS TECNICAS OFICIALES:
- Bluetooth 5.3 estable hasta 10 metros
- Resistencia al agua y polvo grado IP67
- Bateria recargable con autonomia de 7 horas
- Sonido JBL Pro Sound potente
- Manos libres con microfono integrado
- Puerto USB-C para carga rapida
- 6 colores disponibles: Negro, Azul, Rojo, Rosa, Camuflaje, Aqua

QUE INCLUYE:
- 1 Bocina JBL Go 4 USADA
- 1 Cable USB-C de carga
- Caja original (puede presentar marcas de almacenamiento)

VERIFICACION DE AUTENTICIDAD:
Puede validar la originalidad del producto por cualquiera de estas vias oficiales antes de emitir cualquier reclamo:
1. Portal oficial: jbl.com.mx - seccion Verificar producto (ingrese el SN impreso en la caja).
2. Servicio al cliente JBL Mexico: telefono 01-800-005-5252
3. Peritaje tecnico en centro autorizado Harman/JBL Mexico.

GARANTIA DEL VENDEDOR:
- 30 dias por defectos de fabrica comprobables con video del fallo + numero de orden.
- NO aplica garantia oficial del fabricante Harman Mexico por tratarse de producto usado.
- NO cubre danos por agua excesiva, caidas, mal uso o desgaste estetico normal.

POLITICA DE DEVOLUCIONES Y RECLAMOS:
- El producto se vende tal como se describe en esta publicacion.
- El producto enviado NO difiere del ofertado: marca, modelo, condicion, color y caracteristicas coinciden exactamente con lo publicado.
- NO se aceptan reclamos por "no es compatible con app JBL Portable" - esta publicacion lo declara expresamente.
- NO se aceptan reclamos por "no es compatible con Auracast" - esta publicacion lo declara expresamente.
- NO se aceptan reclamos por "no es original" sin peritaje tecnico oficial.
- NO se aceptan devoluciones por cambio de opinion del comprador.
- NO se aceptan devoluciones por condiciones esteticas minimas propias de un producto USADO.
- Toda devolucion aceptada requiere producto + empaque + accesorios completos, sin danos adicionales.

ENVIO GRATIS - Despacho 24 horas habiles - Entrega estimada 2 a 5 dias segun zona.

Al completar esta compra usted declara haber leido y aceptar todos los terminos anteriores, incluyendo las limitaciones de compatibilidad y la condicion usada del producto. Cualquier reclamo contrario a estos terminos carece de sustento."""

rd=requests.put(f"https://api.mercadolibre.com/items/{IID}/description",headers=H,json={"plain_text":DESC},timeout=30)
print(f"desc update {IID}: {rd.status_code} ({len(DESC)} chars)")
if rd.status_code not in (200,201): print(rd.text[:400])
