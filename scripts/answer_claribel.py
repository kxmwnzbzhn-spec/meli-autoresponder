import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"Cuenta: {me.get('nickname')}")

q=requests.get(f"https://api.mercadolibre.com/my/received_questions/search?status=UNANSWERED&limit=50",headers=H,timeout=15).json()
questions=q.get("questions",[])
print(f"UNANSWERED Claribel: {len(questions)}")

def classify(text):
    t=text.lower()
    if any(k in t for k in ["app","aplicaci","jbl portable","firmware"]): return "app"
    if any(k in t for k in ["original","autentico","autentica","pirata","clon","copia","replica"]): return "original"
    if any(k in t for k in ["disponible","stock","hay","tienes","tienen"]): return "disponible"
    if any(k in t for k in ["cuanto tarda","cuando llega","tiempo"]) and "gratis" not in t: return "envio"
    if any(k in t for k in ["garant","reclamo","devoluc","cambio","defecto"]): return "garantia"
    if any(k in t for k in ["caja","empaque","viene con"]): return "caja"
    if any(k in t for k in ["fotos","foto","imagen","real","ver"]): return "fotos"
    if any(k in t for k in ["precio","cuesta","barato","descuento"]): return "precio"
    if any(k in t for k in ["perfume","edp","eau","fragancia","duracion","dura","huele","mililitros","ml"]): return "perfume"
    return "generico"

RESP={
    "app":"Hola! Nuestras bocinas JBL son version OEM original de fabrica con firmware independiente. NO son compatibles con la app oficial JBL Portable. Funcionan al 100% via Bluetooth estandar con cualquier dispositivo. Factura y garantia 30 dias. Saludos!",
    "original":"Hola! Si, es 100% original con factura de comercializadora autorizada. Garantia 30 dias. Saludos!",
    "disponible":"Hola! Si, esta disponible con envio inmediato. Saludos!",
    "envio":"Hola! Enviamos el mismo dia si compras antes de las 2 pm. Entrega 1-3 dias habiles via Mercado Envios. Saludos!",
    "garantia":"Hola! Garantia de 30 dias por defecto de funcionamiento. Devoluciones requieren video del desempaque. Saludos!",
    "caja":"Hola! Viene en caja original con todos los accesorios y factura. Saludos!",
    "fotos":"Hola! Las fotos son reales del producto. Si necesitas una especifica, dimelo. Saludos!",
    "precio":"Hola! Nuestro precio es competitivo y garantizamos producto original con factura. Saludos!",
    "perfume":"Hola! Perfume 100% original con factura de comercializadora autorizada. La duracion y proyeccion dependen de factores personales (piel, clima, aplicacion). Garantia solo por producto danado en envio. Saludos!",
    "generico":"Hola! Gracias por tu interes. Producto 100% original con factura y garantia 30 dias. Saludos!"
}

ok=0; err=0
for qu in questions:
    qid=qu.get("id"); text=qu.get("text","") or ""
    cat=classify(text); resp=RESP.get(cat,RESP["generico"])
    r=requests.post("https://api.mercadolibre.com/answers",headers=H,json={"question_id":int(qid),"text":resp},timeout=15)
    if r.status_code in (200,201):
        print(f"OK q{qid} [{cat}] {text[:50]}")
        ok+=1
    else:
        print(f"ERR q{qid} [{cat}]: {r.status_code} {r.text[:100]}")
        err+=1
    time.sleep(1)
print(f"\n{ok}/{len(questions)} OK, {err} ERR")
