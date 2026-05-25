import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
SRC="MLM2534863827"
it=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
pics=[{"id":p["id"]} for p in (it.get("pictures") or []) if p.get("id")][:10]
print("fotos:",len(pics))

TITLE=("Conjunto Deportivo Seamless Attessa´s Sports Mujer Sin Costura | Top y Leggings "
       "de Compresión Push Up Alto Rendimiento para Gym y Yoga")
ATTRS=[
 {"id":"BRAND","values":[{"name":"Attessa´s Sports"}]},
 {"id":"MODEL","values":[{"name":"Seamless Escultural"}]},
 {"id":"GENDER","values":[{"name":"Mujer"}]},
 {"id":"GTIN","values":[{"name":"028035188036"}]},
 {"id":"AGE_GROUP","values":[{"name":"Adultos"}]},
 {"id":"SLEEVE_TYPE","values":[{"name":"Corta"}]},
]
body={"site_id":"MLM","domain_id":"MLM-SPORTSWEAR_SETS","type":"EDIT","title":TITLE,"attributes":ATTRS,"pictures":pics}
r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
print("POST http",r.status_code)
rb=r.json(); print(json.dumps(rb,ensure_ascii=False)[:1500])
sid=rb.get("id") or rb.get("suggestion_id")
if sid:
    print(f"\n>>> SUGGESTION_ID = {sid}")
    desc=("Conjunto deportivo seamless de Attessa´s Sports, diseño escultural de alto rendimiento que realza tu figura "
          "y se adapta como una segunda piel. Top y leggings sin costura con tela de compresión y efecto push up.\n\n"
          "CARACTERÍSTICAS PRINCIPALES\n• Marca: Attessa´s Sports\n• Tipo: Conjunto deportivo (top + leggings)\n"
          "• Tejido seamless (sin costuras) para mayor comodidad y ajuste\n• Tela de compresión que moldea y realza la silueta\n"
          "• Cintura alta con efecto push up\n• Material elástico, transpirable y de secado rápido\n• Manga corta\n• Género: Mujer\n\n"
          "¿POR QUÉ ELEGIRLO?\nDiseño escultural de alto rendimiento, libertad total de movimiento y soporte donde lo necesitas. "
          "Ideal para gym, yoga, pilates, running y uso casual athleisure.\n\n"
          "CASOS DE USO\n• Entrenamiento de fuerza y gimnasio\n• Yoga, pilates y stretching\n• Running y cardio\n• Uso casual diario\n\n"
          "DETALLES DEL PRODUCTO\nConjunto seamless de top y leggings de compresión, tejido elástico de alto rendimiento, transpirable y de secado rápido.")
    rd=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
    print("desc POST",rd.status_code, rd.text[:200])
