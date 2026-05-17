-- Elite Market Inventory Platform — Schema v1.0
-- Supabase PostgreSQL

-- Cleanup (idempotent)
DROP TABLE IF EXISTS stock_movements CASCADE;
DROP TABLE IF EXISTS manual_adjustments CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS stock CASCADE;
DROP TABLE IF EXISTS listings CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;

-- ACCOUNTS (multi-tenant MELI sellers)
CREATE TABLE accounts (
  id SERIAL PRIMARY KEY,
  nickname TEXT NOT NULL UNIQUE,
  meli_user_id BIGINT UNIQUE,
  refresh_token_secret TEXT NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  notes TEXT
);
CREATE INDEX idx_accounts_active ON accounts(active);

-- PRODUCTS (SKUs canónicos)
CREATE TABLE products (
  sku TEXT PRIMARY KEY,
  modelo TEXT,
  color TEXT,
  brand TEXT,
  line TEXT,
  condition TEXT DEFAULT 'new' CHECK (condition IN ('new','used','refurbished','generic_mirror')),
  alert_threshold INT DEFAULT 5,
  archived BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  archived_at TIMESTAMPTZ,
  notes TEXT
);
CREATE INDEX idx_products_archived ON products(archived);
CREATE INDEX idx_products_modelo_color ON products(modelo, color);

-- LISTINGS (publicaciones MELI vinculadas a products)
CREATE TABLE listings (
  mlm_id TEXT PRIMARY KEY,
  account_id INT REFERENCES accounts(id) ON DELETE RESTRICT,
  sku TEXT REFERENCES products(sku) ON DELETE RESTRICT,
  title TEXT,
  catalog_product_id TEXT,
  price NUMERIC(10,2),
  status TEXT,
  sub_status TEXT,
  available_quantity INT,
  sold_quantity INT DEFAULT 0,
  last_sync TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_listings_account ON listings(account_id);
CREATE INDEX idx_listings_sku ON listings(sku);
CREATE INDEX idx_listings_status ON listings(status);

-- STOCK (cantidades por SKU + tipo de almacén)
CREATE TABLE stock (
  sku TEXT NOT NULL REFERENCES products(sku) ON DELETE RESTRICT,
  warehouse TEXT NOT NULL,                -- bodega_main | devolucion | transito | dañado
  qty INT NOT NULL DEFAULT 0 CHECK (qty >= 0),
  last_update TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (sku, warehouse)
);
CREATE INDEX idx_stock_qty ON stock(qty);

-- EVENTS (webhooks raw, inmutable)
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ DEFAULT NOW(),
  source TEXT NOT NULL,                   -- meli_webhook | manual | backfill | retry
  topic TEXT,                             -- orders_v2 | shipments | items | claims
  resource TEXT,                          -- /orders/2000016...
  user_id BIGINT,
  account_id INT REFERENCES accounts(id),
  raw_payload JSONB NOT NULL,
  received_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending','processing','done','error','skipped')),
  processing_error TEXT,
  attempts INT DEFAULT 0
);
CREATE INDEX idx_events_status ON events(processing_status);
CREATE INDEX idx_events_topic ON events(topic);
CREATE INDEX idx_events_resource ON events(resource);
CREATE INDEX idx_events_account ON events(account_id);

-- STOCK_MOVEMENTS (audit trail completo de cada cambio de qty)
CREATE TABLE stock_movements (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ DEFAULT NOW(),
  sku TEXT NOT NULL REFERENCES products(sku),
  warehouse TEXT NOT NULL,
  delta INT NOT NULL,                     -- negativo=salida, positivo=entrada
  before_qty INT NOT NULL,
  after_qty INT NOT NULL,
  movement_type TEXT NOT NULL CHECK (movement_type IN ('sale','return_meli','manual_in','manual_out','transfer','damage','reverse','initial_seed','backfill')),
  event_id BIGINT REFERENCES events(id),
  order_id TEXT,
  mlm_id TEXT,
  account_id INT REFERENCES accounts(id),
  reason TEXT,
  author TEXT DEFAULT 'system'
);
CREATE INDEX idx_movements_sku ON stock_movements(sku);
CREATE INDEX idx_movements_ts ON stock_movements(ts);
CREATE INDEX idx_movements_type ON stock_movements(movement_type);
CREATE INDEX idx_movements_order ON stock_movements(order_id);

-- MANUAL_ADJUSTMENTS (log inmutable de ajustes manuales)
CREATE TABLE manual_adjustments (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ DEFAULT NOW(),
  sku TEXT NOT NULL,
  warehouse TEXT NOT NULL,
  delta INT NOT NULL,
  reason TEXT NOT NULL,
  author TEXT NOT NULL,
  reverse_of BIGINT REFERENCES manual_adjustments(id),
  applied_movement_id BIGINT REFERENCES stock_movements(id)
);

-- VIEWS para reportes rápidos
CREATE OR REPLACE VIEW v_stock_current AS
SELECT
  p.sku, p.modelo, p.color, p.brand, p.line, p.condition, p.alert_threshold,
  COALESCE(SUM(CASE WHEN s.warehouse='bodega_main' THEN s.qty END),0) AS qty_bodega,
  COALESCE(SUM(CASE WHEN s.warehouse='devolucion' THEN s.qty END),0) AS qty_devolucion,
  COALESCE(SUM(CASE WHEN s.warehouse='transito' THEN s.qty END),0) AS qty_transito,
  COALESCE(SUM(s.qty),0) AS qty_total,
  CASE WHEN COALESCE(SUM(CASE WHEN s.warehouse='bodega_main' THEN s.qty END),0) < p.alert_threshold THEN true ELSE false END AS alert_low
FROM products p
LEFT JOIN stock s ON s.sku=p.sku
WHERE p.archived=false
GROUP BY p.sku, p.modelo, p.color, p.brand, p.line, p.condition, p.alert_threshold;

CREATE OR REPLACE VIEW v_sales_daily AS
SELECT
  DATE_TRUNC('day', m.ts) AS day,
  m.sku,
  p.modelo, p.color,
  SUM(-m.delta) AS sold,
  COUNT(*) AS orders
FROM stock_movements m
JOIN products p ON p.sku=m.sku
WHERE m.movement_type='sale'
GROUP BY DATE_TRUNC('day', m.ts), m.sku, p.modelo, p.color
ORDER BY day DESC;

-- Trigger: stock cannot go below 0 (returns oversell flag in error)
CREATE OR REPLACE FUNCTION block_negative_stock() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.qty < 0 THEN
    RAISE EXCEPTION 'OVERSELL: SKU=% warehouse=% would become %', NEW.sku, NEW.warehouse, NEW.qty;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_stock_no_negative BEFORE UPDATE ON stock
FOR EACH ROW EXECUTE FUNCTION block_negative_stock();

-- Function helper: decrement_stock(sku, warehouse, qty, type, event_id, order_id, mlm_id, account_id, reason)
CREATE OR REPLACE FUNCTION apply_stock_delta(
  p_sku TEXT, p_warehouse TEXT, p_delta INT,
  p_type TEXT, p_event_id BIGINT DEFAULT NULL,
  p_order_id TEXT DEFAULT NULL, p_mlm_id TEXT DEFAULT NULL,
  p_account_id INT DEFAULT NULL, p_reason TEXT DEFAULT NULL,
  p_author TEXT DEFAULT 'system'
) RETURNS BIGINT AS $$
DECLARE
  before_qty INT;
  after_qty INT;
  movement_id BIGINT;
BEGIN
  -- Ensure row exists
  INSERT INTO stock(sku, warehouse, qty) VALUES (p_sku, p_warehouse, 0)
  ON CONFLICT (sku, warehouse) DO NOTHING;

  SELECT qty INTO before_qty FROM stock WHERE sku=p_sku AND warehouse=p_warehouse FOR UPDATE;
  after_qty := before_qty + p_delta;

  UPDATE stock SET qty=after_qty, last_update=NOW()
  WHERE sku=p_sku AND warehouse=p_warehouse;

  INSERT INTO stock_movements (sku, warehouse, delta, before_qty, after_qty, movement_type,
    event_id, order_id, mlm_id, account_id, reason, author)
  VALUES (p_sku, p_warehouse, p_delta, before_qty, after_qty, p_type,
    p_event_id, p_order_id, p_mlm_id, p_account_id, p_reason, p_author)
  RETURNING id INTO movement_id;
  RETURN movement_id;
END;
$$ LANGUAGE plpgsql;
