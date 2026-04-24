import os,requests,json,time

ACCOUNTS={
    "JUAN":os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL":os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO":os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
}

# Templates de respuesta por keyword
TEMPLATES=[
    # (keywords, template) — match de palabras
    (["disponibl","stock","existencia","hay","en almacen"], "Buen dia, si tenemos disponibilidad inmediata. Despachamos en 24h habiles. Gracias."),
    (["envio","envi","mandar","enviar","llega","cuando llega","cuanto tarda"], "Buen dia, envio GRATIS con Mercado Envios. Despacho en 24h habiles, entrega estimada 2 a 5 dias segun zona. Gracias."),
    (["factura","facturar","fiscal","rfc"], "Buen dia, si facturamos. Al completar la compra envienos por mensaje privado sus datos fiscales (RFC, razon social, uso CFDI, email) y procesamos en 48h. Gracias."),
    (["garantia","warranty","reparar","falla","defecto"], "Buen dia, ofrecemos garantia del vendedor de 30 dias por defectos de fabrica comprobables con video. No cubre danos por agua excesiva, caidas o mal uso. Gracias."),
    (["original","autentico","autentica","replica","pirata","falso"], "Buen dia, el producto y sus caracteristicas se describen expresamente en la publicacion. Por favor lea la descripcion completa antes de comprar. Gracias."),
    (["app","aplicacion","portable","auracast"], "Buen dia, este modelo opera como bocina Bluetooth estandar y NO es compatible con app movil JBL Portable ni Auracast, tal como se indica en la descripcion. Gracias."),
    (["color","colores","disponib","tienes el"], "Buen dia, los colores disponibles aparecen en la variacion al seleccionar el producto. Por favor revise las opciones al agregar al carrito. Gracias."),
    (["precio","descuento","rebaja","ofrece","negociar","menos"], "Buen dia, el precio publicado es el precio final e incluye envio gratis. No aplica descuentos adicionales. Gracias."),
    (["bateria","duracion","horas","carga","cargador"], "Buen dia, la autonomia y caracteristicas de bateria se detallan en la descripcion del producto. Incluye cable USB-C de carga. Gracias."),
    (["ip67","agua","alberca","playa","lluvia","sumergible"], "Buen dia, el producto tiene certificacion IP67: resistente al polvo y sumergible en agua dulce hasta 1 metro por 30 minutos. Gracias."),
    (["usb","entrada","aux","cable"], "Buen dia, el producto cuenta con puerto USB-C para carga y entrada USB para alimentacion, tal como se indica en la descripcion. Gracias."),
]

DEFAULT="Buen dia, gracias por su pregunta. Las caracteristicas, garantia, politica de envio y demas detalles estan claramente descritos en la publicacion. Le invito a leer la descripcion completa. Gracias."

def match(text):
    t=text.lower()
    for kws,tpl in TEMPLATES:
        if any(k in t for k in kws):
            return tpl
    return DEFAULT

total_answered=0
for label,rt in ACCOUNTS.items():
    if not rt:
        print(f"\n=== {label}: sin refresh_token, skip ===")
        continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" not in r:
        print(f"\n=== {label}: token invalido ===")
        continue
    TOKEN=r["access_token"]
    H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    USER_ID=me["id"]
    print(f"\n=== {label} ({me.get('nickname')} {USER_ID}) ===")
    
    # Unanswered questions
    q=requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={USER_ID}&status=UNANSWERED&limit=50",headers=H,timeout=20).json()
    qs=q.get("questions") or []
    print(f"  unanswered: {len(qs)}")
    
    answered=0
    for ques in qs:
        qid=ques.get("id")
        text=ques.get("text","")
        item_id=ques.get("item_id")
        ans=match(text)
        print(f"  Q{qid} [{item_id}] '{text[:70]}' -> respuesta: '{ans[:60]}'")
        rp=requests.post("https://api.mercadolibre.com/answers",headers=H,
            json={"question_id":qid,"text":ans},timeout=15)
        if rp.status_code in (200,201):
            answered+=1
        else:
            print(f"    err: {rp.status_code} {rp.text[:200]}")
        time.sleep(1)
    print(f"  answered: {answered}/{len(qs)}")
    total_answered+=answered

print(f"\n=== TOTAL RESPONDIDAS: {total_answered} ===")
