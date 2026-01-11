-- VTT Analytics Schema for Supabase
-- Run this in Supabase SQL Editor

-- 1. Уникальные установки (каждое устройство)
CREATE TABLE IF NOT EXISTS vtt_installs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id TEXT UNIQUE NOT NULL,  -- Уникальный ID устройства
    os TEXT,                          -- windows/macos
    os_version TEXT,
    app_version TEXT,
    country TEXT,
    city TEXT,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    total_sessions INT DEFAULT 1,
    is_premium BOOLEAN DEFAULT FALSE,
    license_key TEXT
);

-- 2. События (все действия пользователей)
CREATE TABLE IF NOT EXISTS vtt_events (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    event_type TEXT NOT NULL,         -- app_launch, recording_start, recording_complete, etc.
    event_data JSONB,                 -- Дополнительные данные
    app_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Записи (статистика транскрибаций)
CREATE TABLE IF NOT EXISTS vtt_recordings (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    duration_seconds FLOAT,           -- Длительность записи
    text_length INT,                  -- Длина текста
    language TEXT,                    -- Язык
    ai_brain_used BOOLEAN DEFAULT FALSE,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Скачивания (с сайта/GitHub)
CREATE TABLE IF NOT EXISTS vtt_downloads (
    id BIGSERIAL PRIMARY KEY,
    platform TEXT,                    -- windows/macos
    version TEXT,
    source TEXT,                      -- github/website/telegram
    ip_address TEXT,
    user_agent TEXT,
    country TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Ошибки (для дебага)
CREATE TABLE IF NOT EXISTS vtt_errors (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT,
    error_type TEXT,
    error_message TEXT,
    stack_trace TEXT,
    app_version TEXT,
    os TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для быстрых запросов
CREATE INDEX IF NOT EXISTS idx_events_device ON vtt_events(device_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON vtt_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON vtt_events(created_at);
CREATE INDEX IF NOT EXISTS idx_recordings_device ON vtt_recordings(device_id);
CREATE INDEX IF NOT EXISTS idx_installs_device ON vtt_installs(device_id);

-- RLS (Row Level Security) - отключаем для простоты, включим потом
ALTER TABLE vtt_installs ENABLE ROW LEVEL SECURITY;
ALTER TABLE vtt_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE vtt_recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE vtt_downloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE vtt_errors ENABLE ROW LEVEL SECURITY;

-- Политики: разрешаем всё для anon (приложение отправляет без авторизации)
CREATE POLICY "Allow all for vtt_installs" ON vtt_installs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for vtt_events" ON vtt_events FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for vtt_recordings" ON vtt_recordings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for vtt_downloads" ON vtt_downloads FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for vtt_errors" ON vtt_errors FOR ALL USING (true) WITH CHECK (true);

-- Вьюхи для дашборда

-- Общая статистика
CREATE OR REPLACE VIEW vtt_stats AS
SELECT
    (SELECT COUNT(*) FROM vtt_installs) as total_installs,
    (SELECT COUNT(*) FROM vtt_installs WHERE last_seen > NOW() - INTERVAL '24 hours') as active_today,
    (SELECT COUNT(*) FROM vtt_installs WHERE last_seen > NOW() - INTERVAL '7 days') as active_week,
    (SELECT COUNT(*) FROM vtt_recordings) as total_recordings,
    (SELECT COUNT(*) FROM vtt_recordings WHERE created_at > NOW() - INTERVAL '24 hours') as recordings_today,
    (SELECT COUNT(*) FROM vtt_installs WHERE is_premium = true) as premium_users,
    (SELECT COUNT(*) FROM vtt_downloads) as total_downloads;

-- Статистика по дням
CREATE OR REPLACE VIEW vtt_daily_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as events,
    COUNT(DISTINCT device_id) as unique_users
FROM vtt_events
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Популярные события
CREATE OR REPLACE VIEW vtt_event_stats AS
SELECT
    event_type,
    COUNT(*) as count,
    COUNT(DISTINCT device_id) as unique_users
FROM vtt_events
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY event_type
ORDER BY count DESC;

-- Функция для трекинга сессий (upsert)
CREATE OR REPLACE FUNCTION track_session(p_device_id TEXT, p_app_version TEXT)
RETURNS void AS $$
BEGIN
    INSERT INTO vtt_installs (device_id, app_version, last_seen, total_sessions)
    VALUES (p_device_id, p_app_version, NOW(), 1)
    ON CONFLICT (device_id)
    DO UPDATE SET
        last_seen = NOW(),
        total_sessions = vtt_installs.total_sessions + 1,
        app_version = p_app_version;
END;
$$ LANGUAGE plpgsql;
