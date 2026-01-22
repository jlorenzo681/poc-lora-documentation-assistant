-- Connector configurations
CREATE TABLE IF NOT EXISTS connectors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    oauth_credentials TEXT,  -- JSON encrypted
    folders_to_sync TEXT,    -- JSON array
    file_filters TEXT,       -- JSON object
    sync_strategy TEXT,
    sync_interval INTEGER,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_sync TIMESTAMP WITH TIME ZONE
);

-- File sync state
CREATE TABLE IF NOT EXISTS file_sync_state (
    connector_id TEXT,
    file_id TEXT,
    file_path TEXT,
    last_modified TIMESTAMP WITH TIME ZONE,
    hash TEXT,
    processed BOOLEAN DEFAULT FALSE,
    vector_store_key TEXT,
    PRIMARY KEY (connector_id, file_id)
);

-- Sync logs
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    connector_id TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT,  -- "success" | "failed" | "partial"
    files_processed INTEGER,
    errors TEXT,  -- JSON array
    FOREIGN KEY (connector_id) REFERENCES connectors(id)
);
