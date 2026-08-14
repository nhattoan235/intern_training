import os
import pyodbc

conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={os.getenv('DB_HOST')};"
    f"UID=SA;PWD={os.getenv('DB_PASSWORD')};"
    f"TrustServerCertificate=yes;"
)


conn = pyodbc.connect(conn_str)
cursor = conn.cursor()


cursor.execute("SELECT @@VERSION")

print(cursor.fetchone())