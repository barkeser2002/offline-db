import sqlite3
conn = sqlite3.connect("anime_db.sqlite")
cursor = conn.cursor()
cursor.execute("SELECT mal_id, title FROM animes")
for row in cursor.fetchall():
    print(row)
conn.close()
