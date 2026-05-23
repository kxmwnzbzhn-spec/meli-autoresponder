import os,requests,json,time
import meli_token

ACCOUNTS={
    "JUAN":os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL":os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO":os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "WILBERT":os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "MILDRED":os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "DILCIE":os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "BREN":os.environ.get("MELI_REFRESH_TOKEN_BREN"),
    "YC_NEW":os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
}

# Templates AFIRMATIVOS — JAMAS evasivas. Siempre confirmar originalidad.
# Para "app/aplicacion/auracast" → respuesta depende del condition (new vs used/refurbished)
APP_NEW="Buen dia, si, es producto 100% original y nuevo. Es compatible con la app JBL Portable y Auracast. Gracias."
APP_USED="Buen dia, si, es producto 100% original. Por ser modelo reacondicionado, NO es compatible con la app JBL Portable ni Auracast. Funciona perfectamente como bocina Bluetooth estandar. Gracias."

TEMPLATES=[
    (["disponibl","stock","existencia","hay disponible","en almacen","tienen"], "Buen dia, si tenemos disponibilidad inmediata. Despachamos en 24h habiles. Gracias."),
    (["envio","envi","mandar","enviar","llega","cuando llega","cuanto tarda","tiempo de entrega"], "Buen dia, envio GRATIS con Mercado Envios. Despacho en 24h habiles, entrega estimada 2 a 5 dias segun zona. Gracias."),
    (["factura","facturar","fiscal","rfc"], "Buen dia, si facturamos. Al completar la compra envienos por mensaje privado sus datos fiscales (RFC, razon social, uso CFDI, email) y procesamos en 48h. Gracias."),
    (["garantia","warranty","reparar","falla","defecto"], "Buen dia, son productos 100% originales y ofrecemos garantia del vendedor de 30 dias por defectos de fabrica comprobables con video. No cubre danos por agua excesiva, caidas o mal uso. Gracias."),
    (["original","autentic","replica","pirata","falso","clon","imitacion","fake"], "Buen dia, si, son productos 100% originales y nuevos, con garantia del vendedor. Gracias."),
    (["fabricad","fabrica","china","vietnam","mexico","origen","pais","made in","procedenc"], "Buen dia, son productos 100% originales fabricados en las plantas oficiales autorizadas por la marca. Gracias."),
    # APP keyword especial — usa condition
    (["__APP__","app","aplicacion","auracast","jbl portable"], "__APP_PLACEHOLDER__"),
    (["color","colores","disponib","que color","tienes el"], "Buen dia, los colores disponibles aparecen en la variacion al seleccionar el producto. Por favor revise las opciones al agregar al carrito. Gracias."),
    (["precio","descuento","rebaja","ofrece","negociar","menos"], "Buen dia, el precio publicado es el precio final e incluye envio gratis. No aplica descuentos adicionales. Gracias."),
    (["bateria","duracion","horas","carga","cargador"], "Buen dia, son productos 100% originales. La autonomia y caracteristicas de bateria se detallan en la descripcion. Incluye cable USB-C de carga. Gracias."),
    (["ip67","agua","alberca","playa","lluvia","sumergible","resistente","resiste"], "Buen dia, son productos 100% originales con certificacion IP67: resistente al polvo y sumergible en agua dulce hasta 1 metro por 30 minutos. Gracias."),
    (["usb","entrada","aux","cable","conexion"], "Buen dia, son productos 100% originales. Cuenta con puerto USB-C para carga y entrada USB para alimentacion, tal como se indica en la descripcion. Gracias."),
    (["talla","talles","medida","cm","centimetro","kilo","peso"], "Buen dia, las medidas y guia de tallas se detallan en la descripcion del producto. Le invitamos a revisarlas antes de comprar. Gracias."),
    (["tela","material","algodon","nailon","poliester","esponja","top"], "Buen dia, los materiales y composicion estan detallados en la descripcion del producto. Gracias."),
]

DEFAULT="Buen dia, son productos 100% originales y nuevos. Para mas detalles tecnicos revise la descripcion del producto. Gracias."

# cache condition por iid
ITEM_CONDITION_CACHE={}

def get_condition(iid, headers):
    if iid in ITEM_CONDITION_CACHE: return ITEM_CONDITION_CACHE[iid]
    try:
        b=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=condition,title",headers=headers,timeout=12).json()
        c=b.get("condition","new")
        # También chequear si el title menciona reacond
        title=(b.get("title","") or "").lower()
        if "reacond" in title or "refurbished" in title or "usado" in title or "caja abierta" in title:
            c="used"
    except Exception:
        c="new"
    ITEM_CONDITION_CACHE[iid]=c
    return c

def match(text, item_id, headers):
    t=text.lower()
    for kws,tpl in TEMPLATES:
        if any(k in t for k in kws):
            if tpl=="__APP_PLACEHOLDER__":
                cond=get_condition(item_id, headers)
                return APP_NEW if cond=="new" else APP_USED
            return tpl
    # Si no match, default. Pero también chequear si "app" estaba en alguna otra palabra:
    return DEFAULT

total_answered=0
for label,rt in ACCOUNTS.items():
    if not rt:
        print(f"\n=== {label}: sin refresh_token, skip ===")
        continue
    try:
        r=meli_token.refresh(rt).json()
    except Exception as e:
        print(f"\n=== {label}: ERROR refresh ({e}) ==="); continue
    if "access_token" not in r:
        print(f"\n=== {label}: token invalido ({r.get('error','?')}) ==="); continue
    TOKEN=r["access_token"]
    H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
    HG={"Authorization":f"Bearer {TOKEN}"}
    try:
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
    except Exception as e:
        print(f"\n=== {label}: error /me ({e}) ==="); continue
    USER_ID=me.get("id")
    if not USER_ID:
        print(f"\n=== {label}: /me sin id (token expirado) ==="); continue
    print(f"\n=== {label} ({me.get('nickname')} {USER_ID}) ===")
    try:
        q=requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={USER_ID}&status=UNANSWERED&limit=50",headers=H,timeout=20).json()
    except Exception as e:
        print(f"  err questions: {e}"); continue
    qs=q.get("questions") or []
    print(f"  unanswered: {len(qs)}")
    answered=0
    for ques in qs:
        qid=ques.get("id")
        text=ques.get("text","")
        item_id=ques.get("item_id")
        ans=match(text, item_id, HG)
        print(f"  Q{qid} [{item_id}] '{text[:65]}' -> '{ans[:55]}'")
        try:
            rp=requests.post("https://api.mercadolibre.com/answers",headers=H,
                json={"question_id":qid,"text":ans},timeout=15)
            if rp.status_code in (200,201):
                answered+=1
            else:
                print(f"    err: {rp.status_code} {rp.text[:160]}")
        except Exception as e:
            print(f"    exc: {e}")
        time.sleep(1)
    print(f"  answered: {answered}/{len(qs)}")
    total_answered+=answered

print(f"\n=== TOTAL RESPONDIDAS: {total_answered} ===")
