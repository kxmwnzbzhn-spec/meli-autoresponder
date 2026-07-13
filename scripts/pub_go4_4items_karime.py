import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

COLORS=[
  ("Negra","MLM44710240"),
  ("Rosa","MLM63973616"),
  ("Roja","MLM44710313"),
  ("Celeste","MLM61262890"),
]

DESC="""====================================================
   LEE TODO ANTES DE COMPRAR - INFORMACION IMPORTANTE
====================================================

*** PRODUCTO REACONDICIONADO - CALIDAD PREMIUM 1:1 ***

Se trata de una version alterna del popular Go 4, con acabado, sonido
y funcionamiento identicos al modelo original de la marca. Fabricacion
proveniente de Asia con estandares de calidad revisados por nuestro
equipo. El precio de $499 MXN habla por si solo.

Si buscas un producto 100% oficial de la marca JBL, este NO es para ti.
Si aceptas una alternativa premium 1:1 a una fraccion del costo, adelante.

====================================================
       DEFECTO PRINCIPAL - NO SE OMITE NADA
====================================================

*** NO ES COMPATIBLE CON LA APLICACION OFICIAL JBL PORTABLE ***

Este es el UNICO defecto del producto. NO se conecta ni se configura
mediante la app oficial. Todas las demas funciones operan al 100%:
sonido, bateria, Bluetooth 5.3 y resistencia al agua IP67.

Si tu unico interes es la app oficial, ABSTENTE de comprar y de hacer
preguntas relacionadas con la app - la respuesta siempre sera la misma.

====================================================
    CONDICIONES QUE ACEPTAS AL CONFIRMAR TU COMPRA
====================================================

1. Este producto es REACONDICIONADO con acabado 1:1 al original.
2. NO se conecta con la app oficial JBL Portable.
3. Fabricacion alterna asiatica; no es distribucion oficial de la marca.
4. Todas las demas funciones operan al 100%.
5. NO abriras un reclamo por motivos ya descritos en esta publicacion.

Si estas de acuerdo con TODAS estas condiciones, te llevaras un
EXCELENTE producto a una fraccion del precio de uno oficial.

====================================================
                     QUE INCLUYE
====================================================

- 1 Bocina Bluetooth portatil modelo Go 4
- 1 Cable de carga USB-C
- Manual de usuario / instrucciones basicas
- Empaque puede presentar detalles minimos de manipulacion

====================================================
                CARACTERISTICAS TECNICAS
====================================================

- Sonido JBL Pro potente y nitido
- Bluetooth 5.3 estable hasta 10 metros
- Resistencia al agua y polvo grado IP67 (sumergible)
- Bateria recargable hasta 7 horas de reproduccion continua
- Diseno ultra compacto y ligero
- Correa integrada para llevar a todos lados

====================================================
     PREGUNTAS FRECUENTES - LEE PRIMERO POR FAVOR
====================================================

- "Es original de fabrica?" -> El precio te indica la naturaleza del producto.
- "Viene con caja sellada / hologramas oficiales?" -> No.
- "Se puede registrar en la pagina oficial JBL?" -> No.
- "Se conecta con la app oficial?" -> NO. Es el defecto principal.
- "Funciona el Bluetooth normal con celular?" -> SI, sin problemas.
- "Es resistente al agua real?" -> SI, IP67 sumergible.
- "Da la bateria completa (7 horas)?" -> SI.
- "Puedo devolverlo si funciona todo excepto la app?" -> No, ese defecto
   esta descrito claramente en esta publicacion.

====================================================
                CONDICIONES DE VENTA
====================================================

- ENVIO EL MISMO DIA si compras antes de las 3pm.
- GARANTIA POR ELITE MARKET - 30 dias solo contra fallas no relacionadas
  con el defecto de la app.
- COMPRA PROTEGIDA por MERCADO LIBRE.

Si aceptas las condiciones y el precio te parece justo, adelante.
Enviamos hoy y recibiras un excelente producto.

Cualquier duda DIFERENTE a las ya respondidas arriba, escribenos.
Gracias por preferir Elite Market."""

results=[]

for cname, cpid in COLORS:
    print(f"\n=== {cname} ({cpid}) ===",flush=True)
    # Get pics from CPID
    p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=10).json()
    urls=[pic.get("url") for pic in p.get("pictures",[])[:8] if pic.get("url")]
    print(f"  pics from CPID: {len(urls)}",flush=True)
    
    payload={
        "family_name":f"Bocina Bluetooth Go 4 Reacondicionada {cname}",
        "category_id":"MLM59800",
        "condition":"used",
        "listing_type_id":"gold_pro",
        "buying_mode":"buy_it_now",
        "currency_id":"MXN",
        "price":499,
        "available_quantity":100,
        "pictures":[{"source":u} for u in urls],
        "attributes":[
            {"id":"BRAND","value_name":"Genérica"},
            {"id":"MODEL","value_name":"Go 4"},
            {"id":"LINE","value_name":"Go 4 Reacondicionada"},
            {"id":"COLOR","value_name":cname},
            {"id":"ITEM_CONDITION","value_name":"Usado"},
            {"id":"MAX_POWER","value_name":"4 W"},
            {"id":"POWER_SOURCE","value_name":"Bluetooth"},
            {"id":"WATER_RESISTANCE","value_name":"IP67"},
        ],
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"}
        ],
        "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False,"logistic_type":"drop_off"}
    }
    
    post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=30).json()
    if "id" in post:
        new_id=post["id"]
        print(f"  ✅ POSTED: {new_id} status={post.get('status')} title={post.get('title','?')[:60]}",flush=True)
        print(f"  URL: {post.get('permalink','?')}",flush=True)
        
        d=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                       headers=H,json={"plain_text":DESC},timeout=15)
        print(f"  description: {d.status_code}",flush=True)
        results.append((cname,new_id))
    else:
        print(f"  ❌ FAIL: {json.dumps(post)[:1500]}",flush=True)
        results.append((cname,None))
    time.sleep(1)

print(f"\n=== SUMMARY ===",flush=True)
for cname, iid in results:
    print(f"  {cname}: {iid}",flush=True)
