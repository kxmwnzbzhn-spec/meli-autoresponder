import os, requests
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
H={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"}

ITEMS=[
  ("MLM5633127222","Sony SRS-XB100 Negro"),
  ("MLM5633114522","JBL Charge 6 Negro Portátil"),
  ("MLM5633114356","JBL Charge 6 Negro"),
  ("MLM5633089028","JBL Go 4 Rosa Impermeable"),
  ("MLM5633114492","JBL Charge 6 Bocina Portátil"),
  ("MLM5633114554","Sony SRS-XB100"),
  ("MLM5633114404","JBL Go 4 Waterproof Celeste"),
  ("MLM5633114418","JBL Go 4 Waterproof Negra"),
  ("MLM5633114476","JBL Go 4 Rojo"),
  ("MLM5633127266","JBL Go 4 Waterproof Roja"),
  ("MLM5633127318","Dzyp JBL Go 4 Rosa"),
  ("MLM5633114498","JBL Go 4 Ultraportátil Rosado"),
  ("MLM5633089236","JBL Go4 Camuflado"),
  ("MLM5633114458","JBL Go 4 Camuflaje"),
  ("MLM5633089220","JBL Go 4 Negro"),
]
# Delete from no_replenish
for iid,_ in ITEMS:
  r=requests.delete(f"{SB}/rest/v1/meli_no_replenish_items?item_id=eq.{iid}",headers=H,timeout=8)
  print(f"del no_replenish {iid}: {r.status_code}")

# Insert into priority_replenish
for iid,name in ITEMS:
  r=requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=H,
    json={"account":"LUPITA","item_id":iid,"default_qty":1,"product_name":name[:60],"reason":"Reactivado + autostock 2026-07-03"},timeout=8)
  print(f"add priority {iid}: {r.status_code}")

# Directive
r=requests.post(f"{SB}/rest/v1/meli_user_directives",headers=H,
  json={"account":"LUPITA","scope":"batch","scope_value":"reactivate_15","directive_type":"reactivate","raw_user_message":"activa las publicaciones de lupita que pausaste y activa el autostock"},timeout=8)
print(f"directive: {r.status_code}")
