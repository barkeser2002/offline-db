import mysql.connector
from config import DB_CONFIG

def execute_migration():
    """Executes the database migration script."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        cursor = conn.cursor()
        with open("migrate_to_innodb.sql", "r") as f:
            sql_script = f.read()

        # Split the script into individual statements
        sql_statements = sql_script.split(';')

        # Execute each statement
        for statement in sql_statements:
            if statement.strip():
                cursor.execute(statement)

        conn.commit()
        cursor.close()
        conn.close()
        print("Database migration successful.")
    except Exception as e:
        print(f"Database migration failed: {e}")

if __name__ == "__main__":
    execute_migration()
