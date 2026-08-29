import pathlib
import sqlite3


def get_db_path() -> str:
    # Use ~/.anklient for global data, fallback to local if needed, 
    # but for this iteration, let's use ~/.anklient/anklient.db
    home_dir = pathlib.Path.home()
    app_dir = home_dir / ".anklient"
    app_dir.mkdir(exist_ok=True)
    return str(app_dir / "anklient.db")

def init_db(db_path: str = None):
    if db_path is None:
        db_path = get_db_path()
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            category TEXT,
            ttft_ms REAL,
            total_ms REAL,
            word_count INTEGER,
            char_count INTEGER,
            status TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            template TEXT NOT NULL,
            tags TEXT,
            favorite BOOLEAN DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            last_used DATETIME
        )
    """)
    
    conn.commit()
    return conn
