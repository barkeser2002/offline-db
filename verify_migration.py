import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

def verify_innodb_migration():
    """
    Tüm tabloların InnoDB'ye dönüştürüldüğünü doğrula.
    """
    all_innodb = True
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}'")

        for table in cursor.fetchall():
            if table['ENGINE'] != 'InnoDB':
                print(f"[HATA] '{table['TABLE_NAME']}' tablosu hala {table['ENGINE']} kullanıyor.")
                all_innodb = False
            else:
                print(f"'{table['TABLE_NAME']}' tablosu başarıyla InnoDB'ye dönüştürülmüş.")

        if all_innodb:
            print("\nTüm tablolar başarıyla InnoDB'ye dönüştürülmüş.")
        else:
            print("\nBazı tablolar InnoDB'ye dönüştürülemedi.")

    except Error as e:
        print(f"[DB] Hata: {e}")
        all_innodb = False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return all_innodb

if __name__ == "__main__":
    if not verify_innodb_migration():
        exit(1)
