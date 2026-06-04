import os, requests
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
# Try the SQL endpoint via management API (only with personal access token)
# Instead, use a Supabase Edge Function if available, or print SQL for user to run.
SQL="""CREATE TABLE IF NOT EXISTS meli_stock_capped (
  item_id text PRIMARY KEY,
  account text NOT NULL,
  visible_qty int NOT NULL DEFAULT 1,
  remaining int NOT NULL,
  original int NOT NULL,
  auto_pause_when_zero boolean NOT NULL DEFAULT true,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);"""
# Try via PostgREST /rpc/exec or similar
for ep in ["/rest/v1/rpc/exec_sql","/rest/v1/rpc/exec","/rest/v1/rpc/sql"]:
    rr=requests.post(f"{SBU}{ep}",
        headers={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"},
        json={"sql":SQL,"query":SQL},timeout=10)
    print(f"  {ep} HTTP {rr.status_code}: {rr.text[:200]}")
