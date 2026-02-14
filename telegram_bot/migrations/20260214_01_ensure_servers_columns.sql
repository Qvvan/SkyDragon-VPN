-- Ensure all Servers columns exist (idempotent).
-- Run this if 20260213_01 was applied but columns are missing or sub_port was never added.

-- available_ports
ALTER TABLE servers ADD COLUMN IF NOT EXISTS available_ports INTEGER[];
UPDATE servers SET available_ports = ARRAY[443] WHERE available_ports IS NULL;

-- panel_port
ALTER TABLE servers ADD COLUMN IF NOT EXISTS panel_port INTEGER;
UPDATE servers SET panel_port = 443 WHERE panel_port IS NULL;
ALTER TABLE servers DROP CONSTRAINT IF EXISTS chk_panel_port_range;
ALTER TABLE servers ADD CONSTRAINT chk_panel_port_range CHECK (panel_port IS NULL OR (panel_port > 0 AND panel_port <= 65535));

-- url_secret
ALTER TABLE servers ADD COLUMN IF NOT EXISTS url_secret VARCHAR(255);
UPDATE servers SET url_secret = '' WHERE url_secret IS NULL;

-- sub_port (port for /sub/ endpoint, usually 2096)
ALTER TABLE servers ADD COLUMN IF NOT EXISTS sub_port INTEGER;
-- do not set default; NULL means use app config (SUB_PORT)
