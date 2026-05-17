-- =====================================================================
-- Go-live during ongoing operations — pending_orders_snapshot
-- =====================================================================
-- Snapshot point-in-time de las órdenes paid+no-enviadas en MELI.
-- Se captura JUSTO ANTES del conteo físico, y se reconcilia con
-- el stock contado mediante inv_go_live_seed.
-- =====================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS pending_orders_snapshot (
    id                   bigserial PRIMARY KEY,
    snapshot_batch       uuid NOT NULL DEFAULT gen_random_uuid(),  -- agrupa items del mismo snapshot run
    snapshot_ts          timestamptz NOT NULL DEFAULT now(),
    order_id             text NOT NULL,
    account_id           int REFERENCES accounts(id),
    mlm_id               text,
    sku                  text,                                     -- NULL si no mapeado (raw_order tiene info)
    qty                  int NOT NULL CHECK (qty > 0),
    unit_price           numeric(10,2),
    total_amount         numeric(12,2),
    date_paid            timestamptz,
    date_created         timestamptz,
    shipping_status      text,
    shipping_id          text,
    buyer_nick           text,
    applied_to_stock     bool NOT NULL DEFAULT false,
    applied_at           timestamptz,
    applied_movement_id  bigint REFERENCES stock_movements(id),
    skip_reason          text,                                     -- "cancelled_later", "shipped_after_snapshot", etc.
    raw_order            jsonb,
    raw_shipping         jsonb,
    created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pending_snapshot_batch
    ON pending_orders_snapshot(snapshot_batch);
CREATE INDEX IF NOT EXISTS idx_pending_unapplied
    ON pending_orders_snapshot(applied_to_stock) WHERE applied_to_stock = false;
CREATE INDEX IF NOT EXISTS idx_pending_sku
    ON pending_orders_snapshot(sku);
CREATE INDEX IF NOT EXISTS idx_pending_order_id
    ON pending_orders_snapshot(order_id);

COMMENT ON TABLE pending_orders_snapshot IS
'Snapshot point-in-time de órdenes paid+no-enviadas para reconciliación go-live. Cada batch es un run del script snapshot_pending_orders.py.';

-- Vista helper: latest batch
CREATE OR REPLACE VIEW v_pending_orders_latest AS
SELECT *
  FROM pending_orders_snapshot
 WHERE snapshot_batch = (
     SELECT snapshot_batch
       FROM pending_orders_snapshot
   ORDER BY snapshot_ts DESC
      LIMIT 1
 );

-- Vista helper: pending por SKU (latest batch)
CREATE OR REPLACE VIEW v_pending_by_sku AS
SELECT
    sku,
    COUNT(*) AS n_orders,
    SUM(qty) AS total_qty,
    SUM(total_amount) AS total_revenue_mxn,
    MIN(date_paid) AS oldest_paid,
    MAX(date_paid) AS newest_paid
FROM v_pending_orders_latest
WHERE applied_to_stock = false
GROUP BY sku
ORDER BY total_qty DESC;

INSERT INTO schema_migrations(id, description)
VALUES ('sprint1_pending_snapshot_v1', 'Pending orders snapshot table + views for go-live reconciliation')
ON CONFLICT (id) DO NOTHING;

COMMIT;
