import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Traer todas UNANSWERED
q=requests.get(f"https://api.mercadolibre.com/my/received_questions/search?status=UNANSWERED&limit=50",headers=H,timeout=15).json()
questions=q.get("questions",[])
print(f"UNANSWERED: {len(questions)}")

def classify(text):
    t=text.lower()
    if any(k in t for k in ["app","aplicaci","jbl portable","conectar con la"]):
        return "app"
    if any(k in t for k in ["original","autentico","autentica","pirata","clon","copia","replica"]):
        return "original"
    if any(k in t for k in ["disponible","stock","hay","tienes"]):
        return "disponible"
    if any(k in t for k in ["cuanto tarda","cuando llega","tiempo","envio"]) and "gratis" not in t:
        return "envio"
    if any(k in t for k in ["garant","reclamo","devoluc","cambio","defecto"]):
        return "garantia"
    if any(k in t for k in ["caja","empaque","viene con"]):
        return "caja"
    if any(k in t for k in ["fotos","foto","imagen","real","ver"]):
        return "fotos"
    if any(k in t for k in ["precio","cuesta","barato","descuento"]):
        return "precio"
    return "generico"

RESP={
    "app": "Hola! Nuestras bocinas JBL son version OEM original de fabrica (hardware identico al retail). Por ser version OEM NO son compatibles con la app oficial JBL Portable. Funcionan al 100% via Bluetooth estandar con cualquier dispositivo (iPhone, Android, Samsung, etc). Factura y garantia 30 dias incluidas. Saludos!",
    "original": "Hola! Si, es 100% original de fabrica JBL (version OEM). Hardware identico al retail oficial. Incluye factura de comercializadora autorizada y garantia de 30 dias con nosotros. Saludos!",
    "disponible": "Hola! Si, esta disponible con envio inmediato. Factura y garantia 30 dias. Saludos!",
    "envio": "Hola! Enviamos el mismo dia si compras antes de las 2 pm. Tiempo estimado: 1-3 dias habiles via Mercado Envios gratis. Saludos!",
    "garantia": "Hola! Contamos con garantia de 30 dias por defecto de funcionamiento. Cambios por producto danado en envio requieren video del desempaque. Saludos!",
    "caja": "Hola! Viene con su caja original JBL sellada, cable de carga USB-C, manual y factura incluida. Saludos!",
    "fotos": "Hola! Las fotos del anuncio son reales del producto. Si necesitas una especifica, dimelo y te la tomo. Saludos!",
    "precio": "Hola! El precio accesible se debe a que es version OEM original de fabrica (sin licencia retail oficial). Hardware identico al modelo retail, 100% funcional. Factura y garantia 30 dias. Saludos!",
    "generico": "Hola! Gracias por tu interes. Nuestro producto es 100% original con factura y garantia de 30 dias. Envio gratis. Si tienes alguna duda especifica dimelo. Saludos!"
}

ok=0; err=0; details={}
for qu in questions:
    qid=qu.get("id")
    text=qu.get("text","") or ""
    item_id=qu.get("item_id","")
    cat=classify(text)
    resp=RESP.get(cat,RESP["generico"])
    r=requests.post("https://api.mercadolibre.com/answers",headers=H,json={"question_id":int(qid),"text":resp},timeout=15)
    if r.status_code in (200,201):
        print(f"OK q{qid} [{cat}] {text[:50]}")
        ok+=1
        details.setdefault(cat,0)
        details[cat]+=1
    else:
        try: msg=r.json().get("message","")
        except: msg=r.text[:100]
        print(f"ERR q{qid} [{cat}] {text[:50]}: {r.status_code} {msg[:80]}")
        err+=1
    time.sleep(1)

print(f"\n=== {ok}/{len(questions)} OK, {err} ERR ===")
print(f"Por categoria: {details}")
