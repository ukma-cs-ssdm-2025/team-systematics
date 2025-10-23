# src/api/repositories/sql_queries.py
import os

# Шлях до вашого SQL-файлу
sql_file_path = os.path.join(os.path.dirname(__file__), "C:\Users\Kolinko\source\repos\Software systems development methods\team-systematics\postgresql\init\Systematics.sql")

# Читання SQL із файлу
with open(sql_file_path, 'r') as f:
    _SQL = f.read()
