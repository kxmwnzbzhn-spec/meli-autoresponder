import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Responder las 3 pendientes
QS=[
    ("13567579399","Hola! Sí, es 100% original y nuevo, con factura de comercializadora autorizada y garantía de 30 días. Cualquier duda aquí estamos."),
    ("13568364206","Hola! Sí, es 100% original JBL, nuevo en caja sellada, con factura y garantía de 30 días. Saludos!"),
    ("13568374754","Hola! Sí, es 100% original y nuevo, con factura de comercializadora autorizada y garantía de 30 días. Saludos!"),
]
for qid,text in QS:
    r=requests.post("https://api.mercadolibre.com/answers",headers=H,json={"question_id":int(qid),"text":text},timeout=15)
    print(f"q{qid}: {r.status_code} {r.text[:150]}")
    time.sleep(1)

# Audit bocinas: ver cuáles están under_review
BOCINAS_NUEVAS=[
    "MLM2880803051","MLM5223449022","MLM5223449418","MLM2880804057",  # los ultimos
    "MLM2880763001","MLM2880774951","MLM2880762579","MLM5223214318","MLM2880762535","MLM2880794089","MLM2880762595","MLM2880775007","MLM2880766117","MLM2880763019","MLM5223214798","MLM2880774949",
]
print("\n=== AUDIT ===")
res=requests.get(f"https://api.mercadolibre.com/items?ids={','.join(BOCINAS_NUEVAS)}&attributes=id,title,status,sub_status,price",headers=H).json()
for x in res:
    b=x.get("body",{})
    ss=b.get("sub_status")
    ss_s=",".join(ss) if isinstance(ss,list) else str(ss)
    print(f"  {b.get('id')} | {b.get('status')}/{ss_s or '-'} | ${b.get('price')} | {b.get('title')[:55]}")
