import sqlite3
from config import DB_PATH

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # watch_history progress
    cursor.execute("PRAGMA table_info(watch_history)")
    columns = [row[1] for row in cursor.fetchall()]
    if "progress" not in columns:
        print("Adding progress column to watch_history...")
        cursor.execute("ALTER TABLE watch_history ADD COLUMN progress INTEGER DEFAULT 0")

    # video_links source_id and fansub
    cursor.execute("PRAGMA table_info(video_links)")
    columns = [row[1] for row in cursor.fetchall()]
    if "source_id" not in columns:
        print("Adding source_id column to video_links...")
        cursor.execute("ALTER TABLE video_links ADD COLUMN source_id INTEGER")
    if "fansub" not in columns:
        print("Adding fansub column to video_links...")
        cursor.execute("ALTER TABLE video_links ADD COLUMN fansub TEXT")

    # anime_titles table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='anime_titles'")
    if not cursor.fetchone():
        print("Creating anime_titles table...")
        cursor.execute("CREATE TABLE anime_titles (id INTEGER PRIMARY KEY AUTOINCREMENT, anime_id INTEGER, title TEXT, type TEXT)")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
