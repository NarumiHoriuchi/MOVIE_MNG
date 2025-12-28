import sqlite3

# DB接続
conn = sqlite3.connect("media.db")
c = conn.cursor()

# Volume table
c.execute("""
CREATE TABLE IF NOT EXISTS Volume (
    volume_id INTEGER PRIMARY KEY AUTOINCREMENT,
    volume_label TEXT,
    human_number TEXT,
    date_added DATE DEFAULT (DATE('now')),
    notes TEXT,
    write_count INTEGER DEFAULT 1
)
""")

# UNIQUE INDEX（重複防止）
c.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS idx_volume_unique
ON Volume(volume_label, human_number);
""")

# File table（セキュリティ情報追加版）
c.execute("""
CREATE TABLE IF NOT EXISTS File (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    volume_id INTEGER,
    channel_name TEXT,
    file_name TEXT,
    upload_date DATE,
    path TEXT,
    checksum TEXT,
    owner TEXT,
    readonly_flag BOOLEAN DEFAULT 0,
    encrypted_flag BOOLEAN DEFAULT 0,
    notes TEXT,
    FOREIGN KEY(volume_id) REFERENCES Volume(volume_id)
)
""")

# UNIQUE INDEX（重複防止）
c.execute("""
CREATE UNIQUE INDEX idx_file_unique ON File(volume_id, path, file_name);
ON Volume(volume_label, human_number);
""")

conn.commit()
conn.close()
