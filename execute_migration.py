import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

def migrate_to_innodb():
    """
    Tüm MyISAM tablolarını InnoDB'ye dönüştür.
    """
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        cursor = conn.cursor()

        # Tüm tabloları listele
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        # Her tabloyu InnoDB'ye dönüştür
        for table in tables:
            print(f"'{table}' tablosu dönüştürülüyor...")
            cursor.execute(f"ALTER TABLE {table} ENGINE=InnoDB")
            print(f"'{table}' tablosu başarıyla InnoDB'ye dönüştürüldü.")

        print("\nTüm tablolar başarıyla InnoDB'ye dönüştürüldü.")

    except Error as e:
        print(f"[DB] Hata: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    migrate_to_innodb()
