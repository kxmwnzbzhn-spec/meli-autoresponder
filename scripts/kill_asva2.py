import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# MLM3937 is "Otras categorías" most likely
# Walk it deep
def walk(cid,depth=0,out=[]):
  if depth>5: return
  try:
    ci=requests.get(f"{API}/categories/{cid}",headers=H,timeout=10).json()
    n=(ci.get("name") or "")
    nl=n.lower()
    if "esot" in nl or "ritual" in nl or "perfum" in nl or "ocult" in nl or "san" in nl[:3]:
      print(f"{'  '*depth}{cid} - {n} {'[LEAF]' if not ci.get('children_categories') else ''}")
    for ch in ci.get("children_categories",[]):
      walk(ch["id"],depth+1,out)
  except Exception as e: pass

# Common top categories MLM site
TOP_CATS=["MLM3937","MLM43385","MLM1953","MLM5726","MLM1276","MLM86","MLM1500","MLM1574","MLM440","MLM1132"]
# Also try the ones we know
for c in TOP_CATS:
  print(f"\n=== {c} ===")
  walk(c)

# Better: list all top-level cats
print("\n=== ALL TOP-LEVEL CATS ===")
tree=requests.get(f"{API}/sites/MLM/categories",headers=H,timeout=15).json()
for t in tree:
  print(f"  {t['id']} - {t['name']}")
