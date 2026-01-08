import mysql.connector
from config import DB_CONFIG

def verify_migration():
    """Verifies that the database tables have been migrated to InnoDB."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT TABLE_NAME, ENGINE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{DB_CONFIG["database"]}'
        """)

        all_innodb = True
        for table_name, engine in cursor:
            print(f"Table: {table_name}, Engine: {engine}")
            if engine.lower() != 'innodb':
                all_innodb = False

        if all_innodb:
            print("\nDatabase migration verified successfully. All tables are using InnoDB.")
        else:
            print("\nDatabase migration verification failed. Some tables are not using InnoDB.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database verification failed: {e}")

if __name__ == "__main__":
    verify_migration()
