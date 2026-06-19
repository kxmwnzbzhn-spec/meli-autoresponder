"""
Bot mejorado de alertas de reclamos: poll TODAS las cuentas + Telegram con link directo.
Por ahora NO auto-responde porque endpoint MELI POST /messages devuelve 405.
"""
import os, requests, json
from datetime import datetime, timezone, timedelta

API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
SB=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation,resolution=merge-duplicates"}
TG_BOT=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")

ACCOUNTS=[
  ("AH","MELI_REFRESH_TOKEN_AH"),
  ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
  ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
  ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
  ("JUAN","MELI_REFRESH_TOKEN_JUAN"),
  ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
  ("BREN","MELI_REFRESH_TOKEN_BREN"),
  ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
  ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
]

def tg(msg, link=None):
  if not TG_BOT or not TG_CHAT: print(f"[tg-skip] {msg[:80]}"); return
  if link: msg+=f"\n\n<a href='{link}'>Abrir caso →</a>"
  try:
    requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
      data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"HTML","disable_web_page_preview":False},timeout=8)
  except Exception as e: print(f"[tg-err] {e}")

def get_token(env_key):
  rt=os.environ.get(env_key)
  if not rt: return None
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
  return r.json()["access_token"] if r.status_code<400 else None

# Already alerted
alerted=set()
try:
  r=requests.get(f"{SB}/rest/v1/meli_claim_responses?action=eq.alerted&ts=gte.{(datetime.now(timezone.utc)-timedelta(hours=12)).isoformat()}&select=claim_id",headers=SBH,timeout=15)
  if r.status_code==200: alerted={str(x["claim_id"]) for x in r.json()}
except: pass

now=datetime.now(timezone.utc)
total_opened=0
total_alerted=0
for acct,key in ACCOUNTS:
  AT=get_token(key)
  if not AT: 
    print(f"[{acct}] no token, skip")
    continue
  H={"Authorization":f"Bearer {AT}"}
  
  # Get user_id
  me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
  uid=me.get("id")
  
  # Search claims as respondent
  r=requests.get(f"{API}/post-purchase/v1/claims/search?status=opened&player.role=respondent&limit=50",headers=H,timeout=20)
  if r.status_code!=200:
    print(f"[{acct}] claims search HTTP {r.status_code}")
    continue
  claims=r.json().get("data") or r.json().get("results") or []
  if not claims: print(f"[{acct}] no opened claims"); continue
  print(f"[{acct}] {len(claims)} opened claims")
  total_opened+=len(claims)
  
  for c in claims:
    cid=str(c.get("id"))
    # Get full
    full=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=15).json()
    stage=full.get("stage")
    reason=full.get("reason_id")
    
    # Find seller available_actions and due
    seller_actions=[]
    for p in full.get("players",[]):
      if p.get("role")=="respondent":
        seller_actions=[a.get("action") if isinstance(a,dict) else a for a in (p.get("available_actions") or [])]
        break
    
    if not seller_actions: continue  # nothing seller can do
    
    # Due date
    due=None
    for p in full.get("players",[]):
      if p.get("role")=="respondent":
        for a in (p.get("available_actions") or []):
          if isinstance(a,dict) and a.get("due_date"):
            try: due=datetime.fromisoformat(a["due_date"].replace("Z","+00:00")); break
            except: pass
    
    # Get order/product
    res_id=full.get("resource_id")
    product=""
    if res_id:
      try:
        o=requests.get(f"{API}/orders/{res_id}",headers=H,timeout=10).json()
        product=(o.get("order_items",[{}])[0].get("item",{}).get("title","") or "")[:50]
      except: pass
    
    # Upsert tracked
    try:
      requests.post(f"{SB}/rest/v1/meli_claims_tracked",headers=SBH,
        json={"claim_id":int(cid),"account_nick":acct,"status":"opened","stage":stage,
              "reason_id":reason,"product_title":product,"action_responsible":"respondent",
              "due_date":due.isoformat() if due else None,
              "last_polled_at":now.isoformat()},timeout=10)
    except Exception as e: print(f"  [{cid}] tracked err {e}")
    
    # Alert if not alerted recently AND (due in <24h OR fresh)
    if cid in alerted: continue
    
    urgency=""
    if due:
      h=(due-now).total_seconds()/3600
      if h<0: urgency=f"⚠️⚠️ VENCIDO hace {abs(h):.1f}h"
      elif h<6: urgency=f"🚨 vence en {h:.1f}h"
      elif h<24: urgency=f"⚠️ vence en {h:.0f}h"
      else: urgency=f"🟡 vence en {h/24:.1f}d"
    
    link=f"https://www.mercadolibre.com.mx/reclamos/casos/{cid}"
    msg=(f"🛒 <b>RECLAMO {acct}</b>\n"
         f"{urgency}\n"
         f"Stage: {stage} | Reason: {reason}\n"
         f"Producto: {product}\n"
         f"Acciones disponibles: {', '.join(seller_actions)}")
    tg(msg, link)
    
    # Log alert
    requests.post(f"{SB}/rest/v1/meli_claim_responses",headers=SBH,
      json={"claim_id":int(cid),"account_nick":acct,"action":"alerted",
            "message_text":msg[:500],"ts":now.isoformat(),"notes":"telegram alert"},timeout=10)
    total_alerted+=1

print(f"\n=== DONE === opened={total_opened} alerted={total_alerted}")
if total_opened==0:
  tg("✅ Bot reclamos: 0 reclamos abiertos en todas las cuentas")
