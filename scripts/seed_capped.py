import os, requests, json
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

# 1) Create table via PostgREST RPC (need execute SQL)
# Try direct execute via the SQL function if exists, else use schema cache
# Simplest: try INSERT to assumed schema. If table doesn't exist, will get error PGRST205.
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS meli_stock_capped (
  item_id text PRIMARY KEY,
  account text NOT NULL,
  visible_qty int NOT NULL DEFAULT 1,
  remaining int NOT NULL,
  original int NOT NULL,
  auto_pause_when_zero boolean NOT NULL DEFAULT true,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
"""

# Try to use Supabase's exec_sql if exposed via Edge Function or RPC.
# If not, just attempt insert — if table missing, user is informed via printed error.
items=[
    {"item_id":"MLM2967279139","account":"CLARIBEL","visible_qty":1,"remaining":89,"original":89,
     "notes":"JBL Go 3 Negro - capped por usuario, pausar al llegar a 0"},
    {"item_id":"MLM2967317601","account":"CLARIBEL","visible_qty":1,"remaining":19,"original":19,
     "notes":"JBL Go 4 Rojo - capped por usuario, pausar al llegar a 0"},
]

# Insert (upsert)
ru=requests.post(f"{SBU}/rest/v1/meli_stock_capped",
    headers={**SBH,"Prefer":"resolution=merge-duplicates,return=representation"},
    json=items, timeout=15)
print(f"UPSERT capped: HTTP {ru.status_code}: {ru.text[:600]}")

# Verify
rv=requests.get(f"{SBU}/rest/v1/meli_stock_capped?account=eq.CLARIBEL&select=*",headers=SBH,timeout=10)
print(f"\nGET capped: HTTP {rv.status_code}: {rv.text[:1000]}")
