import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

# Items de las preguntas fallidas
IDS=["MLM2880763001","MLM2880774951","MLM2880763019","MLM2880865935","MLM2880762615","MLM2880877603","MLM2880865911","MLM2880758743"]
print("=== STATUS DE ITEMS CON PREGUNTAS ===")
for iid in IDS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    print(f"{iid} | {it.get('status')}/{it.get('sub_status')} | {it.get('title','')[:60]}")

# Estado general del seller
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
# Contar items por status
uid=me["id"]
for st in ["active","paused","closed","under_review","inactive"]:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=1",headers=H,timeout=15).json()
    print(f"{st}: {r.get('paging',{}).get('total',0)}")

# Chequeos adicionales
print("\n=== USER ADVICES ===")
adv=requests.get(f"https://api.mercadolibre.com/users/{uid}/advice",headers=H,timeout=15)
print(f"{adv.status_code}: {adv.text[:1000]}")

print("\n=== DISPUTAS ABIERTAS ===")
dis=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?role=respondent&stage=claim&status=opened",headers=H,timeout=15)
print(f"{dis.status_code}: {dis.text[:500]}")
