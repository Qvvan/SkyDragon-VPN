-- Миграция для добавления полей для новой API и поддержки множественных портов
-- Расширение таблицы servers для работы с новой API панели 3x-ui

------------------------------------------------------------
-- ДОБАВЛЕНИЕ ПОЛЯ available_ports
------------------------------------------------------------

ALTER TABLE servers 
ADD COLUMN IF NOT EXISTS available_ports INTEGER[];

-- Обновляем существующие записи: если available_ports NULL, устанавливаем [443]
UPDATE servers 
SET available_ports = ARRAY[443]
WHERE available_ports IS NULL;

-- Добавляем комментарий
COMMENT ON COLUMN servers.available_ports IS 'Список портов для инбаундов на данном сервере';

------------------------------------------------------------
-- ДОБАВЛЕНИЕ ПОЛЯ panel_port
------------------------------------------------------------

ALTER TABLE servers 
ADD COLUMN IF NOT EXISTS panel_port INTEGER;

-- Обновляем существующие записи: если panel_port NULL, устанавливаем 443
-- (в production это должно быть значение из конфига PORT_X_UI или 54321)
UPDATE servers 
SET panel_port = 443
WHERE panel_port IS NULL;

-- Добавляем ограничение на диапазон портов (идемпотентно: удаляем если есть, затем добавляем)
ALTER TABLE servers DROP CONSTRAINT IF EXISTS chk_panel_port_range;
ALTER TABLE servers ADD CONSTRAINT chk_panel_port_range CHECK (panel_port > 0 AND panel_port <= 65535);

-- Добавляем комментарий
COMMENT ON COLUMN servers.panel_port IS 'Порт панели управления 3x-ui';

------------------------------------------------------------
-- ДОБАВЛЕНИЕ ПОЛЯ url_secret
------------------------------------------------------------

ALTER TABLE servers 
ADD COLUMN IF NOT EXISTS url_secret VARCHAR(255);

-- Обновляем существующие записи: если url_secret NULL, устанавливаем пустую строку
-- (в production это должно быть значение из конфига MY_SECRET_URL)
-- Пустая строка означает, что будет использоваться значение из конфига
UPDATE servers 
SET url_secret = ''
WHERE url_secret IS NULL;

-- Добавляем комментарий
COMMENT ON COLUMN servers.url_secret IS 'URL-секрет панели (пустая строка = использовать из конфига)';
