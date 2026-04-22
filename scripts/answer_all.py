import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

RESP_APP_JBL = """Hola! Gracias por tu interes. Nuestras bocinas JBL son de fabrica original (OEM), con hardware y componentes identicos al modelo retail. Sin embargo, por ser version OEM NO son compatibles con la app oficial JBL Portable (la app requiere codigo de autenticacion de la version retail con caja oficial).

Funciona al 100% via Bluetooth estandar con cualquier dispositivo: iPhone, Android, Samsung, etc. Viene con factura y garantia de 30 dias. Cualquier duda avisame!"""

RESP_ORIGINAL_PRICE = """Hola! Si, es 100% original JBL de fabrica (version OEM). El precio mas accesible se debe a que es version OEM sin el empaque retail oficial licenciado. El hardware es identico al modelo retail. Viene con factura y garantia 30 dias."""

RESP_COMO_VIENE = """Hola! Viene con su caja original sellada, cable de carga USB-C, manual de usuario y guia de inicio. Factura incluida con cada pedido. Garantia 30 dias contra defectos de fabrica. Envio gratis mismo dia si compras antes de las 2 PM. Saludos!"""

RESP_RESENAS = """Hola! Puedes ver las reseñas en la propia pagina de MELI (seccion 'Opiniones' y 'Preguntas'). Si necesitas fotos adicionales del producto real antes de comprar, avisame y te envio. Saludos!"""

RESP_MORADA_ORIGINAL = """Hola! Si, la bocina color morado es JBL Flip 7 original (version OEM) con factura y garantia de 30 dias. El precio accesible se debe a que es version OEM sin empaque retail oficial. Hardware identico al modelo retail. Saludos!"""

# Respuestas por question_id
QS = {
    13568425076: RESP_COMO_VIENE,
    13567683175: RESP_APP_JBL,
    13568448682: RESP_APP_JBL,
    13568499610: RESP_APP_JBL,
    13568507734: RESP_RESENAS,
    13568529464: RESP_APP_JBL,
    13567780371: RESP_APP_JBL,
    13567782291: RESP_APP_JBL,
    13567783237: RESP_ORIGINAL_PRICE,
    13568543518: RESP_MORADA_ORIGINAL,
    13567788433: RESP_MORADA_ORIGINAL,
}

ok=0; err=0
for qid,text in QS.items():
    r=requests.post("https://api.mercadolibre.com/answers",headers=H,json={"question_id":qid,"text":text},timeout=15)
    if r.status_code in (200,201):
        print(f"OK q{qid}")
        ok+=1
    else:
        print(f"ERR q{qid}: {r.status_code} {r.text[:150]}")
        err+=1
    time.sleep(1)
print(f"\n{ok} OK, {err} ERR")

# Tambien actualizar template auto_06 para que incluya mencion de no-compatibilidad
import json
with open("qa_templates.json") as f: cfg=json.load(f)
# Busca template para "jbl app" pattern
new_app_keywords = ["app jbl","jbl portable","aplicacion jbl","app oficial","no se conecta","jbl portable app","conectar con la app","app de jbl","aplicación jbl","aplicación oficial"]
# Busca si ya existe el template auto_07 para app
found=False
for t in cfg["templates"]:
    if t.get("id")=="auto_jbl_app":
        t["keywords"]=new_app_keywords
        t["response"]=RESP_APP_JBL.replace("\n\n"," ")
        found=True; break
if not found:
    cfg["templates"].append({
        "id":"auto_jbl_app",
        "keywords":new_app_keywords,
        "response":RESP_APP_JBL.replace("\n\n"," ")
    })
# Template "por que no es original si cuesta tan barato"
cfg["templates"].append({
    "id":"auto_oem_precio",
    "keywords":["por que tan barato","porque el precio","precio bajo","precio accesible","tan economico","es replica","no es oficial","donde viene","donde se fabrica"],
    "response":RESP_ORIGINAL_PRICE.replace("\n\n"," ")
})
with open("qa_templates.json","w") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)
print("qa_templates.json actualizado con templates OEM+app")
