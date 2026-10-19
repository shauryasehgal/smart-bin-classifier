import sqlite3

db_path = input("Enter the full path to your SQLite database: ")

connection = sqlite3.connect(
    f"file:{db_path}?mode=ro",
    uri=True
)

cursor = connection.cursor()

# Find all tables
cursor.execute("""
    SELECT name, sql
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""")

tables = cursor.fetchall()

print("\nDATABASE TABLES")

for table_name, create_sql in tables:
    print(f"\nTable: {table_name}")
    print(create_sql)

    # Count records
    cursor.execute(
        f'SELECT COUNT(*) FROM "{table_name}"'
    )
    print("Number of records:", cursor.fetchone()[0])

    # Inspect a few records
    cursor.execute(
        f'SELECT * FROM "{table_name}" LIMIT 3'
    )

    columns = [
        description[0]
        for description in cursor.description
    ]

    print("Columns:", columns)

    for row in cursor.fetchall():
        print(row)

connection.close()